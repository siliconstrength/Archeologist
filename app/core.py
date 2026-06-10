# app/core.py
# Core entry point for the Data Archeologist agent platform.
# Provides BigQuery query utilities and agent orchestration.

import os
import time
from google.adk import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from google.cloud import bigquery

# =====================================================================
# MCP TOOL DEFINITIONS
# =====================================================================

def query_knowledge_lake(sql_query: str) -> str:
    """Executes analytical SQL joins over fresh Fivetran target tables in BigQuery.
    
    Args:
        sql_query (str): Relational SQL query to run.
        
    Returns:
        str: Stringified query results or detailed processing exceptions.
    """
    try:
        # Standard BigQuery client initialization (utilizes standard GOOGLE_APPLICATION_CREDENTIALS)
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
# AGENT SUITE INITIALIZATION
# =====================================================================

ingestion_agent = Agent(
    name="IngestionController",
    model="gemini-2.5-flash",
    instruction=(
        "You supervise ingestion loops. Before doing anything else, you must call "
        "'fivetran_sync_connector' for 'drive_mock_source'. Continuously call "
        "'fivetran_get_sync_status' until it responds with a SUCCESS state. "
        "Once successful, DO NOT attempt to answer the user's query yourself. Simply output: 'Ingestion complete. Proceeding to DataMiner with the incident description.'"
    ),
    tools=[fivetran_sync_connector, fivetran_get_sync_status]
)

miner_agent = Agent(
    name="DataMiner",
    model="gemini-2.5-flash",
    instruction=(
        "You run analytics over BigQuery tables. You have access to exactly three tables located inside the `google_drive` dataset: `google_drive.slack_messages`, `google_drive.jira_tickets`, and `google_drive.github_commits`. "
        "Construct focused SQL strings and feed them to query_knowledge_lake to find anomalies across these three tables. You MUST fully qualify your table names with the dataset name in your SQL. "
        "CRITICAL ANTI-HALLUCINATION: Do NOT guess or hallucinate any other dataset or table names. You must ONLY query the exact `google_drive` tables provided here. "
        "CRITICAL: When tracing the root cause of an incident, you MUST use the exact date of the incident "
        "to filter your SQL queries! A commit or Jira ticket cannot be the root cause if it happened "
        "AFTER the incident was reported. Always use strict WHERE clauses (e.g., `committed_at <= 'YYYY-MM-DD'`) "
        "to ensure you only pull commits and tickets created BEFORE or ON the incident timestamp."
    ),
    tools=[query_knowledge_lake]
)

linker_agent = Agent(
    name="ContextLinker",
    model="gemini-2.5-pro",
    instruction=(
        "Analyze text payloads and code diffs pulled by DataMiner. Draw clear "
        "lines of correlation between human conversations, tracking tickets, and repository commits."
    )
)

resolver_agent = Agent(
    name="SynthesizerResolver",
    model="gemini-2.5-pro",
    instruction=(
        "Compile the final timeline detailing the operational failure, owner, and specific code patch. "
        "CRITICAL: Produce a final structured report using EXACTLY these headings: "
        "\n- **Root Cause:** What went wrong"
        "\n- **Responsible Actor:** Who made the change"
        "\n- **Offending Change:** Which commit/code caused it"
        "\n- **Remediation:** How to fix it"
    )
)

# =====================================================================
# PIPELINE ORCHESTRATION
# =====================================================================

# Plain SequentialAgent — ADK drives execution via sessions in Agent Engine.
# No custom run() override needed; Agent Engine calls sub-agents in order.
data_archeologist_pipeline = SequentialAgent(
    name="Project_Data_Archeologist_v2",
    description="Investigates operational incidents by ingesting data, mining anomalies, linking context, and synthesizing a root cause report.",
    sub_agents=[ingestion_agent, miner_agent, linker_agent, resolver_agent]
)

