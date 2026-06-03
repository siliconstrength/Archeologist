# app/agent.py
# ADK entrypoint: exposes root_agent for `adk run app`.
# Loads .env from the project root if present.

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above this file's directory)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

from app.core import data_archeologist_pipeline

# ADK discovers this symbol when running `adk run app`
root_agent = data_archeologist_pipeline
