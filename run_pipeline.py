# run_pipeline.py
# -------------------------------------------------
# Tiny helper to launch the full ADK agent pipeline.
# -------------------------------------------------
import os
from app.core import data_archeologist_pipeline

# ------------------------------------------------------------------
# Sample incident – replace with any real incident you want to analyse.
# ------------------------------------------------------------------
sample_incident = """
The finance‑recon tracking system broke this morning.
User `aniruddha_p` rotated the Stripe gateway token but forgot to
update the environment config. A hot‑fix commit `c998124f` introduced
a hard‑coded expired token string, breaking reconciliation jobs.
"""

def main() -> None:
    # Use the pre‑initialized pipeline instance.
    pipeline = data_archeologist_pipeline
    # Run the whole workflow.
    result = pipeline.run(sample_incident)

    # ------------------------------------------------------------------
    # Show what happened
    # ------------------------------------------------------------------
    print("\n=== Pipeline Output ===\n")
    print(result.output)
    print("\n=== Tools Invoked ===")
    print(", ".join(result.called_tools))

if __name__ == "__main__":
    main()
