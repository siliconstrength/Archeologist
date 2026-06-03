import type { TraceExecuteRequest, TraceExecuteResponse } from "../types";

export async function runTrace(request: TraceExecuteRequest): Promise<TraceExecuteResponse> {
  const response = await fetch("/api/trace/execute", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Trace execution failed: ${response.status} ${text}`);
  }

  return (await response.json()) as TraceExecuteResponse;
}
