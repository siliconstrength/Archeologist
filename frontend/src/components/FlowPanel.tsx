import { useEffect, useMemo, useState } from "react";

import type { AgentExecutionSummary, TraceEvent } from "../types";

interface FlowPanelProps {
  summary: AgentExecutionSummary[];
  events: TraceEvent[];
}

function statusLabel(status: "success" | "error"): string {
  return status === "success" ? "SUCCESS" : "ERROR";
}

function safeValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  return JSON.stringify(value);
}

export function FlowPanel({ summary, events }: FlowPanelProps): JSX.Element {
  const [activeAgent, setActiveAgent] = useState<string>("");

  useEffect(() => {
    if (!summary.length) {
      setActiveAgent("");
      return;
    }
    if (!activeAgent || !summary.some((item) => item.agent_name === activeAgent)) {
      setActiveAgent(summary[0].agent_name);
    }
  }, [summary, activeAgent]);

  const activeStage = useMemo(
    () => summary.find((item) => item.agent_name === activeAgent) ?? null,
    [summary, activeAgent],
  );

  const activeEvents = useMemo(
    () => events.filter((event) => event.agent_name === activeAgent),
    [events, activeAgent],
  );

  const agentSummaryText = useMemo(() => {
    const endEvent = [...activeEvents].reverse().find((event) => event.event_type === "agent_end");
    if (!endEvent) return "No agent-end summary available yet.";
    return safeValue(endEvent.payload.summary) || "No summary text available for this stage.";
  }, [activeEvents]);

  const toolOutputs = useMemo(
    () =>
      activeEvents
        .filter((event) => event.event_type === "tool_call_end")
        .map((event, index) => ({
          id: `${event.agent_name}-${event.event_type}-${index}`,
          toolName: safeValue(event.payload.tool_name) || "tool",
          output:
            safeValue(event.payload.result_summary) ||
            safeValue(event.payload.result) ||
            safeValue(event.payload.status) ||
            "No tool output payload.",
          payload: event.payload,
        })),
    [activeEvents],
  );

  return (
    <section className="panel panel-flow">
      <h2>Agent Flow and Responses</h2>
      <p className="panel-subtitle">Select an agent tab to inspect its stage output.</p>

      <div className="flow-tabs" role="tablist" aria-label="Agent tabs">
        {summary.map((stage, index) => {
          const isLast = index === summary.length - 1;
          return (
          <button
            key={stage.agent_name}
            type="button"
            role="tab"
            aria-selected={stage.agent_name === activeAgent}
            className={`flow-tab ${stage.agent_name === activeAgent ? "active" : ""}`}
            onClick={() => setActiveAgent(stage.agent_name)}
          >
            <span className="flow-tab-seq">{index + 1}</span>
            <span className="flow-tab-name">{stage.agent_name}</span>
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.45rem" }}>
              {!isLast ? <span className="flow-tab-arrow" aria-hidden="true">→</span> : null}
              <span className={`pill ${stage.status}`}>{statusLabel(stage.status)}</span>
            </div>
          </button>
          );
        })}
      </div>

      {activeStage ? (
        <article className="flow-detail" role="tabpanel" aria-label={`${activeStage.agent_name} details`}>
          <header>
            <h3>{activeStage.agent_name}</h3>
            <p>
              Duration: <strong>{activeStage.duration_ms} ms</strong>
            </p>
          </header>

          <div className="flow-output-block">
            <h4>Agent Output</h4>
            <p>{agentSummaryText}</p>
          </div>

          <div className="flow-output-block">
            <h4>Tools Used</h4>
            <p>{activeStage.tools_called.length ? activeStage.tools_called.join(", ") : "None"}</p>
          </div>

          <div className="flow-output-block">
            <h4>Tool Responses</h4>
            {toolOutputs.length ? (
              <ul className="tool-response-list">
                {toolOutputs.map((item) => (
                  <li key={item.id}>
                    <strong>{item.toolName}:</strong> {item.output}
                    <pre className="flow-json">{JSON.stringify(item.payload, null, 2)}</pre>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No tool response payloads captured for this stage.</p>
            )}
          </div>

          <div className="flow-output-block">
            <h4>Agent Runtime Events</h4>
            {activeEvents.length ? (
              <ul className="event-detail-list">
                {activeEvents.map((event, index) => (
                  <li key={`${event.agent_name}-${event.event_type}-${index}`}>
                    <div>
                      <strong>{event.event_type}</strong> at {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                    <pre className="flow-json">{JSON.stringify(event.payload, null, 2)}</pre>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No event data captured for this agent yet.</p>
            )}
          </div>
        </article>
      ) : (
        <div className="placeholder">Run an incident analysis to view agent tabs and outputs.</div>
      )}
    </section>
  );
}
