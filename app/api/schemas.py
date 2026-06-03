"""Pydantic schemas for the Archeologist trace API."""

from __future__ import annotations

from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field


TraceStatus = Literal["queued", "running", "complete", "error"]
EventType = Literal["agent_start", "agent_end", "tool_call_start", "tool_call_end"]


class TraceExecuteRequest(BaseModel):
    """Request payload for execution trace generation."""

    incident_text: str = Field(min_length=10, max_length=4000)
    include_raw_data: bool = False


class TraceEvent(BaseModel):
    """One event in the execution timeline."""

    timestamp: str
    agent_name: str
    event_type: EventType
    payload: Dict[str, Any]


class AgentExecutionSummary(BaseModel):
    """Rollup information for one agent stage."""

    agent_name: str
    duration_ms: int
    tools_called: List[str]
    status: Literal["success", "error"]


class FinalConclusion(BaseModel):
    """Final conclusion card data displayed to users."""

    root_cause: str
    responsible_actor: str
    offending_code: str
    remediation: str


class TraceExecuteResponse(BaseModel):
    """Response payload used by the frontend trace viewer."""

    execution_id: str
    status: TraceStatus
    events: List[TraceEvent]
    final_conclusion: FinalConclusion
    agent_execution_summary: List[AgentExecutionSummary]
