import type { FinalConclusion } from "../types";

interface ConclusionPanelProps {
  conclusion: FinalConclusion | null;
  executionId: string | null;
}

export function ConclusionPanel({ conclusion, executionId }: ConclusionPanelProps): JSX.Element {
  return (
    <section className="panel panel-conclusion">
      <h2>Final Conclusion</h2>
      <p className="panel-subtitle">Forensic narrative synthesized from all agent evidence.</p>
      {conclusion ? (
        <div className="conclusion-grid">
          <div>
            <h3>Root Cause</h3>
            <p>{conclusion.root_cause}</p>
          </div>
          <div>
            <h3>Responsible Actor</h3>
            <p>{conclusion.responsible_actor}</p>
          </div>
          <div>
            <h3>Offending Change</h3>
            <p>{conclusion.offending_code}</p>
          </div>
          <div>
            <h3>Remediation</h3>
            <p>{conclusion.remediation}</p>
          </div>
          {executionId ? (
            <div className="execution-id-block">
              <h3>Execution ID</h3>
              <p>{executionId}</p>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="placeholder">Run an incident analysis to generate a conclusion.</div>
      )}
    </section>
  );
}
