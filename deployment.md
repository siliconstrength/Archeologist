# Deployment Guide 

This guide deploys the full Project Data Archeologist stack on GCP. The architecture uses a three-tier model to securely expose the Google Agent Development Kit (ADK) reasoning engine:

1. **Vertex AI Agent Engine or Google Agent Cloud Builder:** The core reasoning agent.
2. **Cloud Run Backend:** A lightweight, secure proxy API.
3. **Cloud Run Frontend:** A React UI served by Nginx.

---

## 1. Prerequisites

Install and configure:
- Google Cloud SDK (`gcloud`)
- Access to a GCP project with billing enabled

Authenticate:
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1
```

Enable Required Services:
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com iam.googleapis.com bigquery.googleapis.com aiplatform.googleapis.com
```

---

## 2. Deploy Agent to Vertex AI

The agent is deployed to the fully managed Vertex AI Agent Engine platform using the Google ADK.

1. Navigate to the deployment folder:
```bash
cd agent_deploy
```

2. Run the deployment script to upload the agent to Vertex AI:
```bash
# Ensure you are using Python 3.11
pip install -r requirements.txt
python deploy_vertex.py
```

3. Note your **Engine ID** from the output. Set it as an environment variable for the next steps:
```bash
export AGENT_ENGINE_ID="your_engine_id_here"
export PROJECT_ID="your_project_id_here"
```

---

## 3. Deploy Backend API Proxy (Cloud Run)

The backend is a minimal FastAPI/Starlette server that securely forwards HTTP requests to the deployed Vertex AI Agent Engine.

1. Submit the backend build from the repository root:
```bash
gcloud builds submit --config cloudbuild.backend.yaml --project $PROJECT_ID .
```

2. Deploy the backend image:
```bash
gcloud run deploy data-archeologist-api \
  --image gcr.io/$PROJECT_ID/data-archeologist-api \
  --platform managed --region us-central1 --project $PROJECT_ID \
  --memory 1024Mi \
  --allow-unauthenticated
```

3. Update the backend environment variables with your Engine ID:
```bash
gcloud run services update data-archeologist-api \
  --update-env-vars="AGENT_ENGINE_ID=$AGENT_ENGINE_ID" \
  --region=us-central1 --project=$PROJECT_ID
```

4. Note the Backend URL (e.g., `https://data-archeologist-api-...run.app`).

---

## 4. Deploy Frontend UI (Cloud Run)

The frontend is a React SPA built with Vite. It is hosted on Cloud Run using an Nginx container.

1. Submit the frontend build from the repository root:
```bash
gcloud builds submit --config cloudbuild.frontend.yaml --project $PROJECT_ID .
```

2. Deploy the frontend image:
```bash
gcloud run deploy data-archeologist-ui \
  --image gcr.io/$PROJECT_ID/data-archeologist-ui \
  --platform managed --region us-central1 --project $PROJECT_ID \
  --memory 512Mi \
  --allow-unauthenticated
```

---

## 5. Share With Testers

You now have a fully deployed end-to-end stack!

- **Frontend URL:** Send this to your testers. They can interact with the agent without needing any credentials.
- **Backend URL:** Acts entirely as a proxy. Protects your Agent Runtime from unauthenticated access.
