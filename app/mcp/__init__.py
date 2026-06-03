# app/mcp/__init__.py
# MCP server configuration utilities for the Fivetran MCP integration.
import json
import os
from pathlib import Path


def load_mcp_config() -> dict:
    """Load the MCP server configuration JSON and interpolate environment variables.

    Returns a dict with the full config ready for runtime consumption.
    """
    config_path = Path(__file__).parent / "config.json"
    raw = config_path.read_text()
    for var in ["FIVETRAN_API_KEY", "FIVETRAN_API_SECRET"]:
        raw = raw.replace(f"${{{var}}}", os.getenv(var, ""))
    return json.loads(raw)
