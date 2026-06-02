# app/mcp/__init__.py
# Loads environment and MCP configuration utilities.
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root .env (if present)
project_root = Path(__file__).parents[2]
dotenv_path = project_root / ".env"
if dotenv_path.is_file():
    load_dotenv(dotenv_path)

def load_mcp_config() -> dict:
    """Load the MCP server configuration JSON and interpolate environment variables.

    Returns a dict with the full config ready for runtime consumption.
    """
    config_path = Path(__file__) / "config.json"
    raw = config_path.read_text()
    # Simple placeholder replacement for env vars
    for var in ["FIVETRAN_API_KEY", "FIVETRAN_API_SECRET"]:
        placeholder = f"${{{var}}}"
        raw = raw.replace(placeholder, os.getenv(var, ""))
    return json.loads(raw)
