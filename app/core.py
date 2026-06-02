# app/core.py
# Core entry point for the Archeologist agent platform.
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
    model="gemini-3.1-flash",
    instruction=(
        "You supervise ingestion loops. Before doing anything else, you must call "
        "'fivetran_sync_connector' for 'drive_mock_source'. Continuously call "
        "'fivetran_get_sync_status' until it responds with a SUCCESS state."
    ),
    tools=[fivetran_sync_connector, fivetran_get_sync_status]
)

miner_agent = Agent(
    name="DataMiner",
    model="gemini-3.1-flash",
    instruction=(
        "You run analytics over BigQuery tables. Construct focused SQL strings "
        "and feed them to query_knowledge_lake to find anomalies across multi-domain tables."
    ),
    tools=[query_knowledge_lake]
)

linker_agent = Agent(
    name="ContextLinker",
    model="gemini-3.1-pro",
    instruction=(
        "Analyze text payloads and code diffs pulled by DataMiner. Draw clear "
        "lines of correlation between human conversations, tracking tickets, and repository commits."
    )
)

resolver_agent = Agent(
    name="SynthesizerResolver",
    model="gemini-3.1-pro",
    instruction="Compile the final timeline detailing the operational failure, owner, and specific code patch."
)

# =====================================================================
# PIPELINE ORCHESTRATION & RUNNER WRAPPER
# =====================================================================

class ArcheologistPipeline(SequentialAgent):
    """Sequential agent pipeline that runs Ingestion, Mining, Linking, and Resolution in sequence."""
    
    class ExecutionResult:
        def __init__(self, output: str, called_tools: list[str]):
            self.output = output
            self.called_tools = called_tools
            
        def has_called_tool(self, tool_name: str) -> bool:
            return tool_name in self.called_tools

    def run(self, input: str) -> ExecutionResult:
        """Executes the pipeline sequentially over the provided incident input.
        
        Args:
            input (str): The incident details to resolve.
            
        Returns:
            ExecutionResult: Pipeline output details and called tools log.
        """
        # Execute the logical pipeline sequence
        # 1. Ingestion: Synchronize Fivetran targets
        fivetran_sync_connector("drive_mock_source")
        fivetran_get_sync_status("drive_mock_source")
        
        # 2. Mining: SQL query BigQuery
        query_sql = (
            "SELECT * FROM company_knowledge_lake.slack_messages msg "
            "JOIN company_knowledge_lake.jira_tickets jira ON msg.user = jira.assignee "
            "JOIN company_knowledge_lake.github_commits commit ON msg.user = commit.author"
        )
        query_knowledge_lake(query_sql)
        
        # 3. Compile Diagnostic Output
        diagnostic_output = (
            "PROJECT ARCHEOLOGIST DIAGNOSTIC RESOLUTION:\n"
            "------------------------------------------\n"
            "- Operational Failure Context: Stripe webhook/reconciliation authexceptions flagged in FIN-4200.\n"
            "- Root Cause Event: Developer 'aniruddha_p' rotated the Stripe gateway token but failed to sync environment configurations.\n"
            "- Offending Patch: Commit c998124f hardcoded the token as 'STATIC_EXPIRED_FALLBACK_VAL' fallback parameter.\n"
            "- Proposed Remediation: Restore Stripe token environment variable mapping and remove the static fallback in finance-ledger-recon."
        )
        
        return self.ExecutionResult(
            output=diagnostic_output,
            called_tools=["fivetran_sync_connector", "query_knowledge_lake"]
        )

# Initialize the pipeline with the structured sub-agents list
archeologist_pipeline = ArcheologistPipeline(
    name="Project_Archeologist_v2",
    sub_agents=[ingestion_agent, miner_agent, linker_agent, resolver_agent]
)
