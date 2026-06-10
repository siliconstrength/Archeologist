import type { TraceExecuteRequest, TraceExecuteResponse } from "../types";

export async function runTrace(request: TraceExecuteRequest): Promise<TraceExecuteResponse> {
  const apiUrl = (import.meta as any).env?.VITE_API_URL || "";
  const response = await fetch(`${apiUrl}/api/trace/execute`, {
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
