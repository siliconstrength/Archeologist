import type { TraceEvent } from "../types";

interface TracePanelProps {
  events: TraceEvent[];
}

export function TracePanel({ events }: TracePanelProps): JSX.Element {
  return (
    <section className="panel panel-trace">
      <h2>Trace Stream</h2>
      <p className="panel-subtitle">Tool calls and per-agent transitions used to build the conclusion.</p>
      <div className="trace-list" role="log" aria-live="polite">
        {events.map((event, index) => (
          <article key={`${event.agent_name}-${event.event_type}-${index}`} className="trace-item">
            <div className="trace-head">
              <span className="trace-time">{new Date(event.timestamp).toLocaleTimeString()}</span>
              <span className="trace-agent">{event.agent_name}</span>
              <span className="trace-type">{event.event_type}</span>
            </div>
            <pre>{JSON.stringify(event.payload, null, 2)}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}
