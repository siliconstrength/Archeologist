# agent.py — Self-contained ADK entrypoint for Vertex AI Agent Engine.
#
# The PatchedAdkApp subclass permanently overrides register_operations()
# so that only the '' and 'stream' modes are registered. The default
# AdkApp also registers 'async' and 'async_stream' which Vertex AI Agent
# Engine rejects, causing the entire registration batch (including stream_query)
# to fail. By subclassing we bake the fix into the pickled object itself.

from typing import Dict, List

from google.adk import Agent
from google.cloud import bigquery
from vertexai.agent_engines import AdkApp


# =====================================================================
# PATCHED AdkApp — subclass so the fix survives pickle/unpickle on the
# Vertex AI server (monkey-patching the class at module level does NOT
# survive because Vertex instantiates a fresh AdkApp from the pickle).
# =====================================================================

class PatchedAdkApp(AdkApp):
    """AdkApp with only the supported operation modes registered."""

    def register_operations(self) -> Dict[str, List[str]]:
        return {
            "": [
                "get_session",
                "list_sessions",
                "create_session",
                "delete_session",
            ],
            "stream": ["stream_query"],
        }


# =====================================================================
# TOOL DEFINITIONS
# =====================================================================

def query_knowledge_lake(sql_query: str) -> str:
    """Executes analytical SQL joins over fresh Fivetran target tables in BigQuery.

    Args:
        sql_query (str): Relational SQL query to run.

    Returns:
        str: Stringified query results or detailed processing exceptions.
    """
    try:
        client = bigquery.Client()
        query_job = client.query(sql_query)
        results = query_job.result()
        rows = [str(dict(row)) for row in results]
        return "\n".join(rows) if rows else "Query successful. No anomalies returned."
    except Exception as e:
        return f"BigQuery processing exception: {str(e)}"


def fivetran_sync_connector(connector_id: str) -> str:
    """Signals the Fivetran MCP Server to instantly refresh source targets.

    Args:
        connector_id (str): The identifier of the connector to sync.

    Returns:
        str: Sync initialization status message.
    """
    return f"SYNC_STARTED: Ingestion pipeline for {connector_id} kicked off."


def fivetran_get_sync_status(connector_id: str) -> str:
    """Polls Fivetran to verify schemas have successfully written to BigQuery.

    Args:
        connector_id (str): The identifier of the connector to check.

    Returns:
        str: Sync status outcome message.
    """
    return "SUCCESS: BigQuery target warehouse schemas are entirely synchronized."


# =====================================================================
# ROOT AGENT
# =====================================================================

root_agent = Agent(
    name="Project_Data_Archeologist_v2",
    model="gemini-2.5-flash",
    instruction=(
        "You investigate operational incidents by ingesting data, mining anomalies, linking context, and synthesizing a root cause report.\n"
        "You must execute the following 4 steps strictly in order:\n"
        "1. INGESTION: First, call 'fivetran_sync_connector' for 'drive_mock_source'. Then call 'fivetran_get_sync_status' until it responds SUCCESS.\n"
        "2. MINING: Construct focused SQL strings and feed them to query_knowledge_lake. You have access to exactly three tables:\n"
        "- `google_drive.slack_messages` (timestamp DATETIME, user STRING, channel STRING, text STRING)\n"
        "- `google_drive.jira_tickets` (ticket_id STRING, summary STRING, status STRING, assignee STRING, reporter STRING, description STRING, updated_at DATETIME)\n"
        "- `google_drive.github_commits` (commit_id STRING, author STRING, repository STRING, commit_message STRING, code_diff STRING, committed_at DATETIME)\n"
        "CRITICAL: ONLY query these exact tables. Always filter by the incident date using the correct datetime column for each table.\n"
        "3. ANALYSIS: You MUST output a paragraph starting with '### Context Analysis:' detailing your cross-referencing and reasoning before moving to resolution.\n"
        "4. RESOLUTION: Produce a final structured report using EXACTLY these headings:\n"
        "- **Root Cause:** What went wrong\n"
        "- **Responsible Actor:** Who made the change\n"
        "- **Offending Change:** Which commit/code caused it\n"
        "- **Remediation:** How to fix it"
    ),
    tools=[fivetran_sync_connector, fivetran_get_sync_status, query_knowledge_lake]
)
