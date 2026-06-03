"""Starlette server exposing trace contract endpoints for the UI."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

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


def _iso_timestamp(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _build_demo_response(incident_text: str, include_raw_data: bool) -> TraceExecuteResponse:
    execution_id = str(uuid4())
    start = datetime.now(timezone.utc)

    events = [
        TraceEvent(
            timestamp=_iso_timestamp(start),
            agent_name="IngestionController",
            event_type="agent_start",
            payload={"model": "gemini-2.5-flash"},
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=180)),
            agent_name="IngestionController",
            event_type="tool_call_start",
            payload={"tool_name": "fivetran_sync_connector", "args": {"connector_id": "drive_mock_source"}},
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=470)),
            agent_name="IngestionController",
            event_type="tool_call_end",
            payload={"tool_name": "fivetran_sync_connector", "status": "success", "result": "SYNC_STARTED"},
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=620)),
            agent_name="IngestionController",
            event_type="agent_end",
            payload={"summary": "Connector sync initiated and status validated."},
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=760)),
            agent_name="DataMiner",
            event_type="agent_start",
            payload={"model": "gemini-2.5-flash"},
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=980)),
            agent_name="DataMiner",
            event_type="tool_call_start",
            payload={
                "tool_name": "query_knowledge_lake",
                "args": {
                    "sql_query": "SELECT * FROM company_knowledge_lake.slack_messages ...",
                },
            },
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=1510)),
            agent_name="DataMiner",
            event_type="tool_call_end",
            payload={
                "tool_name": "query_knowledge_lake",
                "status": "success",
                "result_summary": "3 anomaly rows matched across Slack, Jira, and GitHub.",
                "result_rows": [
                    {
                        "ticket_id": "FIN-4200",
                        "commit_id": "c998124f",
                        "user": "aniruddha_p",
                    }
                ]
                if include_raw_data
                else [],
            },
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=1740)),
            agent_name="DataMiner",
            event_type="agent_end",
            payload={"summary": "Correlated incident entities and extracted key anomalies."},
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=1880)),
            agent_name="ContextLinker",
            event_type="agent_start",
            payload={"model": "gemini-2.5-pro"},
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=2360)),
            agent_name="ContextLinker",
            event_type="agent_end",
            payload={
                "summary": "Connected token rotation activity to auth failures and hotfix regression."
            },
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=2490)),
            agent_name="SynthesizerResolver",
            event_type="agent_start",
            payload={"model": "gemini-2.5-pro"},
        ),
        TraceEvent(
            timestamp=_iso_timestamp(start + timedelta(milliseconds=2980)),
            agent_name="SynthesizerResolver",
            event_type="agent_end",
            payload={
                "summary": "Produced final causal narrative and remediation recommendation."
            },
        ),
    ]

    final_conclusion = FinalConclusion(
        root_cause=(
            "Stripe token was rotated without syncing finance-recon environment mappings; "
            "a fallback hardcoded token then caused continued auth failures."
        ),
        responsible_actor="aniruddha_p",
        offending_code="commit c998124f introduced STATIC_EXPIRED_FALLBACK_VAL",
        remediation=(
            "Restore env-driven STRIPE_TOKEN mapping, remove fallback literal, and add "
            "post-rotation validation checks in pipeline release gates."
        ),
    )

    summary = [
        AgentExecutionSummary(
            agent_name="IngestionController",
            duration_ms=620,
            tools_called=["fivetran_sync_connector", "fivetran_get_sync_status"],
            status="success",
        ),
        AgentExecutionSummary(
            agent_name="DataMiner",
            duration_ms=980,
            tools_called=["query_knowledge_lake"],
            status="success",
        ),
        AgentExecutionSummary(
            agent_name="ContextLinker",
            duration_ms=480,
            tools_called=[],
            status="success",
        ),
        AgentExecutionSummary(
            agent_name="SynthesizerResolver",
            duration_ms=490,
            tools_called=[],
            status="success",
        ),
    ]

    return TraceExecuteResponse(
        execution_id=execution_id,
        status="complete",
        events=events,
        final_conclusion=final_conclusion,
        agent_execution_summary=summary,
    )


async def health(_: Request) -> JSONResponse:
    """Simple liveness endpoint for local dev checks."""

    return JSONResponse({"status": "ok"})


async def execute_trace(request: Request) -> JSONResponse:
    """Return a deterministic trace contract response for frontend integration."""

    payload = await request.json()
    request_model = TraceExecuteRequest.model_validate(payload)
    response_model = _build_demo_response(
        incident_text=request_model.incident_text,
        include_raw_data=request_model.include_raw_data,
    )
    return JSONResponse(response_model.model_dump())


api = Starlette(
    debug=True,
    routes=[
        Route("/api/health", health, methods=["GET"]),
        Route("/api/trace/execute", execute_trace, methods=["POST"]),
    ],
    middleware=middleware,
)
