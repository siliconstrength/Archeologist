import { useMemo, useState } from "react";

import { runTrace } from "./api/client";
import { ConclusionPanel } from "./components/ConclusionPanel";
import { FlowPanel } from "./components/FlowPanel";
import { InputPanel } from "./components/InputPanel";
import type { FinalConclusion, TraceEvent, TraceStatus } from "./types";

function emptyConclusion(): FinalConclusion | null {
  return null;
}

export default function App(): JSX.Element {
  const [status, setStatus] = useState<TraceStatus>("queued");
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [conclusion, setConclusion] = useState<FinalConclusion | null>(emptyConclusion());
  const [summary, setSummary] = useState<Array<{ agent_name: string; duration_ms: number; tools_called: string[]; status: "success" | "error" }>>([]);
  const [errorText, setErrorText] = useState<string | null>(null);

  const isRunning = status === "running";

  const headline = useMemo(() => {
    if (status === "running") return "Live Analysis Running";
    if (status === "complete") return "Analysis Complete";
    if (status === "error") return "Analysis Failed";
    return "Ready for Incident Intake";
  }, [status]);

  async function handleRun(incidentText: string, includeRawData: boolean): Promise<void> {
    setStatus("running");
    setErrorText(null);
    setExecutionId(null);
    setEvents([]);
    setConclusion(emptyConclusion());
    setSummary([]);

    try {
      const response = await runTrace({
        incident_text: incidentText,
        include_raw_data: includeRawData,
      });

      setExecutionId(response.execution_id);
      setEvents(response.events);
      setConclusion(response.final_conclusion);
      setSummary(response.agent_execution_summary);
      setStatus(response.status);
    } catch (error) {
      setStatus("error");
      setErrorText(error instanceof Error ? error.message : "Unexpected error while running trace.");
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <h1>Project Data Archeologist | Institutional Failure Forensics Console</h1>
        <p className="hero-subtitle">{headline}</p>
      </header>

      {errorText ? <div className="error-banner">{errorText}</div> : null}

      <section className="layout-grid">
        <div className="left-stack">
          <InputPanel isRunning={isRunning} onSubmit={handleRun} />
          <ConclusionPanel conclusion={conclusion} executionId={executionId} />
        </div>
        <FlowPanel summary={summary} events={events} />
      </section>
    </main>
  );
}
