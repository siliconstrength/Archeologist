import os
import sys
import vertexai
from vertexai.preview.reasoning_engines import ReasoningEngine

# Import both root_agent and PatchedAdkApp from the local agent.py
from agent import root_agent, PatchedAdkApp

project_id = os.getenv("PROJECT_ID", "credible-torus-471702-e5")
location = os.getenv("REGION", "us-central1")
staging_bucket = f"gs://{project_id}-adk-staging"
vertexai.init(project=project_id, location=location, staging_bucket=staging_bucket)

print(f"Deploying AdkApp to Vertex AI Agent Engine in {project_id}/{location}...")

# Create the Engine
engine = ReasoningEngine.create(
    PatchedAdkApp(agent=root_agent),
    requirements=[
        "google-cloud-aiplatform",
        "google-adk==1.18.0",
        "google-cloud-bigquery"
    ],
    extra_packages=["agent.py"],
    display_name="Data_Archeologist_Agent"
)

print(f"\n✅ Deployment Successful!")
print(f"Engine Resource Name: {engine.resource_name}")
