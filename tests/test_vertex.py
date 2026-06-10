import os
import json
import httpx
import google.auth
from google.auth.transport.requests import Request

creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
creds.refresh(Request())

project_id = "credible-torus-471702-e5"
region = "us-central1"
engine_id = "2415414290723897344"

base_url = f"https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{region}/reasoningEngines/{engine_id}"

# Create session
resp = httpx.post(
    f"{base_url}:query",
    headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
    json={"class_method": "create_session", "input": {"user_id": "test_user"}}
)
session_id = resp.json()["output"]["id"]

print("Session created:", session_id)

# Stream query
with httpx.stream(
    "POST",
    f"{base_url}:streamQuery",
    headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
    json={
        "class_method": "stream_query",
        "input": {
            "user_id": "test_user",
            "session_id": session_id,
            "message": "On 2026-01-05, user `carol_ops` raised an issue impacting the **Marketing** application. The AdWords tracking pixel is failing. I need you to cross-reference this",
        },
    },
    timeout=120,
) as stream_resp:
    print(stream_resp.status_code)
    for line in stream_resp.iter_lines():
        if line and line.strip() not in ("[", "]", ","):
            print(line.strip())

