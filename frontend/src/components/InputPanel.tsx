import { FormEvent, useState } from "react";

interface InputPanelProps {
  isRunning: boolean;
  onSubmit: (incidentText: string, includeRawData: boolean) => void;
}

const defaultIncident =
  "Finance-recon failed after Stripe token rotation. Commit c998124f introduced a fallback token and reconciliation jobs started throwing auth exceptions.";

export function InputPanel({ isRunning, onSubmit }: InputPanelProps): JSX.Element {
  const [incidentText, setIncidentText] = useState(defaultIncident);

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    onSubmit(incidentText, false);
  };

  return (
    <section className="panel panel-input">
      <h2>Incident Intake</h2>
      <p className="panel-subtitle">Describe the failure context to start a forensic multi-agent run.</p>
      <form onSubmit={handleSubmit} className="incident-form">
        <label htmlFor="incident-text">Incident Description</label>
        <textarea
          id="incident-text"
          value={incidentText}
          onChange={(event) => setIncidentText(event.target.value)}
          minLength={10}
          rows={8}
          required
          disabled={isRunning}
        />
        <button type="submit" disabled={isRunning || incidentText.trim().length < 10}>
          {isRunning ? "Analyzing..." : "Analyze Incident"}
        </button>
      </form>
    </section>
  );
}
