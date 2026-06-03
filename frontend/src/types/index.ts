export type TraceStatus = "queued" | "running" | "complete" | "error";
export type EventType = "agent_start" | "agent_end" | "tool_call_start" | "tool_call_end";

export interface TraceExecuteRequest {
  incident_text: string;
  include_raw_data: boolean;
}

export interface TraceEvent {
  timestamp: string;
  agent_name: string;
  event_type: EventType;
  payload: Record<string, unknown>;
}

export interface FinalConclusion {
  root_cause: string;
  responsible_actor: string;
  offending_code: string;
  remediation: string;
}

export interface AgentExecutionSummary {
  agent_name: string;
  duration_ms: number;
  tools_called: string[];
  status: "success" | "error";
}

export interface TraceExecuteResponse {
  execution_id: string;
  status: TraceStatus;
  events: TraceEvent[];
  final_conclusion: FinalConclusion;
  agent_execution_summary: AgentExecutionSummary[];
}
