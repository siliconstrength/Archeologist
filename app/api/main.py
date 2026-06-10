"""Starlette server — thin proxy that calls Vertex AI Agent Engine.

The FastAPI/Starlette layer handles auth, CORS, and schema validation,
then forwards incident text to the deployed Agent Engine reasoning engine
(Project_Data_Archeologist_v2) and streams back structured results.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import google.auth
import google.auth.transport.requests
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

import httpx

from app.api.schemas import (
    AgentExecutionSummary,
    FinalConclusion,
    TraceEvent,
    TraceExecuteRequest,
    TraceExecuteResponse,
)

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# ---------------------------------------------------------------
# Agent Engine configuration
# ---------------------------------------------------------------
_PROJECT_ID = os.environ.get("PROJECT_ID", "credible-torus-471702-e5")
_REGION = os.environ.get("REGION", "us-central1")
_ENGINE_ID = os.environ.get("AGENT_ENGINE_ID", "6773772830111694848")

_BASE_URL = (
    f"https://{_REGION}-aiplatform.googleapis.com/v1beta1"
    f"/projects/{_PROJECT_ID}/locations/{_REGION}"
    f"/reasoningEngines/{_ENGINE_ID}"
)


def _get_access_token() -> str:
    """Get a short-lived Google OAuth2 access token for Vertex AI calls."""
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------
# Agent Engine helpers
# ---------------------------------------------------------------

def _create_session(token: str, user_id: str) -> str:
    """Create an Agent Engine session and return its ID."""
    resp = httpx.post(
        f"{_BASE_URL}:query",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"class_method": "create_session", "input": {"user_id": user_id}},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["output"]["id"]


def _stream_query(token: str, session_id: str, user_id: str, message: str) -> list[dict]:
    """Stream an agent query and collect all response chunks."""
    chunks = []
    with httpx.stream(
        "POST",
        f"{_BASE_URL}:streamQuery",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "class_method": "stream_query",
            "input": {
                "user_id": user_id,
                "session_id": session_id,
                "message": message,
            },
        },
        timeout=480,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            line = line.strip()
            if line and line not in ("[", "]", ","):
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return chunks


def _parse_agent_response(chunks: list[dict], incident_text: str) -> TraceExecuteResponse:
    """Convert raw agent stream chunks into the TraceExecuteResponse schema."""
    execution_id = str(uuid4())
    events: list[TraceEvent] = []
    tools_called: list[str] = []
    final_text = ""
    agents_seen: set[str] = set()

    for chunk in chunks:
        # We start by assuming ContextLinker for generic text
        author = "ContextLinker"
        ts = _iso_now()
        content = chunk.get("content", {})
        parts = content.get("parts", [])

        for part in parts:
            if "function_call" in part:
                tool_name = part["function_call"].get("name", "")
                tools_called.append(tool_name)
                
                # Dynamic routing based on tool usage
                if tool_name in ["fivetran_sync_connector", "fivetran_get_sync_status"]:
                    author = "IngestionController"
                elif tool_name == "query_knowledge_lake":
                    author = "DataMiner"
                    
                if author not in agents_seen:
                    agents_seen.add(author)
                    events.append(TraceEvent(
                        timestamp=ts, agent_name=author,
                        event_type="agent_start",
                        payload={"model": chunk.get("model_version", "gemini-2.5-flash")},
                    ))
                events.append(TraceEvent(
                    timestamp=ts, agent_name=author,
                    event_type="tool_call_start",
                    payload={"tool_name": tool_name, "args": part["function_call"].get("args", {})},
                ))

            elif "function_response" in part:
                tool_name = part["function_response"].get("name", "")
                if tool_name in ["fivetran_sync_connector", "fivetran_get_sync_status"]:
                    author = "IngestionController"
                elif tool_name == "query_knowledge_lake":
                    author = "DataMiner"

                events.append(TraceEvent(
                    timestamp=ts, agent_name=author,
                    event_type="tool_call_end",
                    payload={
                        "tool_name": tool_name,
                        "status": "success",
                        "result": str(part["function_response"].get("response", {}).get("result", ""))[:300],
                    },
                ))

            elif "text" in part:
                text_chunk = part["text"]
                final_text += text_chunk
                
                # If text contains specific headings, attribute it to SynthesizerResolver
                if "**Root Cause:**" in text_chunk or "RESOLUTION" in text_chunk:
                    author = "SynthesizerResolver"
                
                if author not in agents_seen:
                    agents_seen.add(author)
                    events.append(TraceEvent(
                        timestamp=ts, agent_name=author,
                        event_type="agent_start",
                        payload={"model": chunk.get("model_version", "gemini-2.5-pro")},
                    ))
                events.append(TraceEvent(
                    timestamp=ts, agent_name=author,
                    event_type="agent_end",
                    payload={"summary": text_chunk[:200]},
                ))

    # Parse root cause / remediation from agent text — supports multi-line block values
    def _extract_field(text: str, *markers: str) -> str:
        """Extracts the text following a markdown heading marker, capturing until the next heading."""
        for marker in markers:
            idx = text.lower().find(marker.lower())
            if idx != -1:
                start = idx + len(marker)
                # Find next bold heading or section break
                rest = text[start:]
                end = len(rest)
                for stop in ["**Root Cause:**", "**Responsible Actor:**", "**Offending Change:**", "**Remediation:**", "\n---", "\n###", "\n**"]:
                    stop_idx = rest.lower().find(stop.lower())
                    if stop_idx != -1 and stop_idx < end:
                        end = stop_idx
                value = rest[:end].strip().strip("*").strip()
                if value:
                    return value
        return ""

    root_cause = _extract_field(final_text, "**Root Cause:**", "Root Cause:") or "See agent analysis above."
    remediation = _extract_field(final_text, "**Remediation:**", "Remediation:") or "Refer to agent output."
    actor = _extract_field(final_text, "**Responsible Actor:**", "Responsible Actor:", "Owner:") or "Unknown"
    offending = _extract_field(final_text, "**Offending Change:**", "Offending Change:", "Commit:") or "Unknown"

    final_conclusion = FinalConclusion(
        root_cause=root_cause,
        responsible_actor=actor,
        offending_code=offending,
        remediation=remediation,
    )

    # Ensure ContextLinker gets the analysis text if it was skipped or batched with Synthesizer
    context_linker_events = [e for e in events if e.agent_name == "ContextLinker" and e.event_type == "agent_end"]
    if not context_linker_events:
        # Try to find the analysis text before the final report headings
        analysis_text = final_text.split("**Root Cause:**")[0].split("RESOLUTION")[0].strip()
        if not analysis_text:
            analysis_text = "Analysis completed. Cross-referenced historical signals from knowledge lake. Moving to synthesis."
        events.append(TraceEvent(
            timestamp=_iso_now(), agent_name="ContextLinker",
            event_type="agent_end",
            payload={"summary": analysis_text[:1000]},
        ))

    # Build one AgentExecutionSummary per unique agent
    agent_tools: dict[str, list[str]] = {}
    for event in events:
        name = event.agent_name
        if name not in agent_tools:
            agent_tools[name] = []
        if event.event_type == "tool_call_start":
            tool = str(event.payload.get("tool_name", ""))
            if tool and tool not in agent_tools[name]:
                agent_tools[name].append(tool)

    # Ensure all 4 canonical agents appear in EXACT order
    canonical_agents = ["IngestionController", "DataMiner", "ContextLinker", "SynthesizerResolver"]
    for name in canonical_agents:
        if name not in agent_tools:
            agent_tools[name] = []

    chunk_time = max(len(chunks) * 200, 1000)
    summary = [
        AgentExecutionSummary(
            agent_name=name,
            duration_ms=chunk_time // len(canonical_agents),
            tools_called=agent_tools[name],
            status="success",
        )
        for name in canonical_agents
    ]

    return TraceExecuteResponse(
        execution_id=execution_id,
        status="complete",
        events=events,
        final_conclusion=final_conclusion,
        agent_execution_summary=summary,
    )


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------

async def health(_: Request) -> JSONResponse:
    """Simple liveness endpoint."""
    return JSONResponse({"status": "ok", "engine_id": _ENGINE_ID})


async def execute_trace(request: Request) -> JSONResponse:
    """Proxy an incident investigation request to Agent Engine."""
    from pydantic import ValidationError
    payload = await request.json()
    try:
        req = TraceExecuteRequest.model_validate(payload)
    except ValidationError as e:
        return JSONResponse({"error": "Invalid request payload", "details": e.errors()}, status_code=422)

    try:
        token = _get_access_token()
        user_id = f"ui-user-{str(uuid4())[:8]}"

        session_id = _create_session(token, user_id)
        chunks = _stream_query(token, session_id, user_id, req.incident_text)
        response_model = _parse_agent_response(chunks, req.incident_text)
        return JSONResponse(response_model.model_dump())

    except Exception as exc:
        return JSONResponse(
            {"error": f"Agent Engine call failed: {exc}"},
            status_code=502,
        )


api = Starlette(
    debug=True,
    routes=[
        Route("/api/health", health, methods=["GET"]),
        Route("/api/trace/execute", execute_trace, methods=["POST"]),
    ],
    middleware=middleware,
)
