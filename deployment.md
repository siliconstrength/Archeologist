# Deployment Guide 

This guide deploys the full Project Data Archeologist stack on GCP with the fastest practical setup:

- Backend API on Cloud Run
- Frontend UI on Cloud Run
- Secrets in Secret Manager
- BigQuery access through Cloud Run service account

Result: testers get one frontend URL and can validate full functionality quickly.

---

## 1. Prerequisites

Install and configure:

- Google Cloud SDK (`gcloud`)
- Docker Desktop (or Cloud Build only)
- Access to a GCP project with billing enabled

Authenticate:

```powershell
gcloud auth login
gcloud auth application-default login
```

Create a `.env` file at repository root and keep all reusable variables there.

> Do not commit secrets. Ensure `.env` is in `.gitignore`.

Example `.env`:

```dotenv
PROJECT_ID=YOUR_PROJECT_ID
REGION=us-central1

BACKEND_SERVICE=data-archeologist-api
FRONTEND_SERVICE=data-archeologist-ui
SERVICE_ACCOUNT=archeologist-run-sa

SECRET_GEMINI_API_KEY=GEMINI_API_KEY
GEMINI_API_KEY_VALUE=YOUR_GEMINI_API_KEY
```

Load `.env` variables into your current PowerShell session:

```powershell
Get-Content .env |
  Where-Object { $_ -and $_ -notmatch '^\s*#' } |
  ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
  }

gcloud config set project $env:PROJECT_ID
gcloud config set run/region $env:REGION
gcloud auth application-default set-quota-project $env:PROJECT_ID
```

---

## 2. Enable Required GCP Services

```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com iam.googleapis.com bigquery.googleapis.com --project $env:PROJECT_ID
```

---

## 3. Create Runtime Service Account and IAM

Create service account:

```powershell
gcloud iam service-accounts create $env:SERVICE_ACCOUNT --display-name "Archeologist Cloud Run SA" --project $env:PROJECT_ID
```

Grant minimum roles (tighten later by dataset if needed):

```powershell
gcloud projects add-iam-policy-binding $env:PROJECT_ID --member="serviceAccount:$($env:SERVICE_ACCOUNT)@$($env:PROJECT_ID).iam.gserviceaccount.com" --role="roles/bigquery.dataViewer" --project $env:PROJECT_ID
gcloud projects add-iam-policy-binding $env:PROJECT_ID --member="serviceAccount:$($env:SERVICE_ACCOUNT)@$($env:PROJECT_ID).iam.gserviceaccount.com" --role="roles/bigquery.jobUser" --project $env:PROJECT_ID
gcloud projects add-iam-policy-binding $env:PROJECT_ID --member="serviceAccount:$($env:SERVICE_ACCOUNT)@$($env:PROJECT_ID).iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor" --project $env:PROJECT_ID
```

---

## 4. Store Secrets in Secret Manager

Create Gemini API key secret:

```powershell
$env:GEMINI_API_KEY_VALUE | gcloud secrets create $env:SECRET_GEMINI_API_KEY --data-file=- --project $env:PROJECT_ID
```

If secret already exists, add a new version:

```powershell
$env:GEMINI_API_KEY_VALUE | gcloud secrets versions add $env:SECRET_GEMINI_API_KEY --data-file=- --project $env:PROJECT_ID
```

---

## 5. Backend Deployment (Cloud Run)

### 5.1 Create backend Dockerfile

Create file `Dockerfile.backend` at repo root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["sh", "-c", "uvicorn app.api.main:api --host 0.0.0.0 --port ${PORT}"]
```

### 5.2 Build and deploy backend

```powershell
gcloud builds submit --tag gcr.io/$env:PROJECT_ID/$env:BACKEND_SERVICE -f Dockerfile.backend . --project $env:PROJECT_ID

gcloud run deploy $env:BACKEND_SERVICE `
  --image gcr.io/$env:PROJECT_ID/$env:BACKEND_SERVICE `
  --platform managed `
  --region $env:REGION `
  --allow-unauthenticated `
  --service-account "$($env:SERVICE_ACCOUNT)@$($env:PROJECT_ID).iam.gserviceaccount.com" `
  --set-secrets GEMINI_API_KEY=$($env:SECRET_GEMINI_API_KEY):latest `
  --project $env:PROJECT_ID
```

Get backend URL:

```powershell
$env:BACKEND_URL=(gcloud run services describe $env:BACKEND_SERVICE --region $env:REGION --format="value(status.url)" --project $env:PROJECT_ID)
Write-Host $env:BACKEND_URL

# Optional: persist discovered URL back into .env for reuse
Add-Content .env "`nBACKEND_URL=$($env:BACKEND_URL)"
```

Health check:

```powershell
Invoke-RestMethod -Uri "$env:BACKEND_URL/api/health" -Method Get
```

---

## 6. Frontend Deployment (Cloud Run)

### 6.1 Create frontend Dockerfile

Create file `Dockerfile.frontend` at repo root:

```dockerfile
# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
CMD ["sh", "-c", "sed -i 's/listen       80;/listen       8080;/' /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
```

### 6.2 Build and deploy frontend

```powershell
gcloud builds submit `
  --tag gcr.io/$env:PROJECT_ID/$env:FRONTEND_SERVICE `
  --config /dev/null `
  --substitutions=_DUMMY=1 `
  --pack image=gcr.io/$env:PROJECT_ID/$env:FRONTEND_SERVICE `
  --project $env:PROJECT_ID
```

If the above pack build is not available in your environment, use Docker build from repo root:

```powershell
docker build -f Dockerfile.frontend --build-arg VITE_API_BASE_URL=$env:BACKEND_URL -t gcr.io/$env:PROJECT_ID/$env:FRONTEND_SERVICE .
docker push gcr.io/$env:PROJECT_ID/$env:FRONTEND_SERVICE
```

Deploy frontend:

```powershell
gcloud run deploy $env:FRONTEND_SERVICE `
  --image gcr.io/$env:PROJECT_ID/$env:FRONTEND_SERVICE `
  --platform managed `
  --region $env:REGION `
  --allow-unauthenticated `
  --project $env:PROJECT_ID
```

Get frontend URL:

```powershell
$env:FRONTEND_URL=(gcloud run services describe $env:FRONTEND_SERVICE --region $env:REGION --format="value(status.url)" --project $env:PROJECT_ID)
Write-Host $env:FRONTEND_URL

# Optional: persist discovered URL back into .env for reuse
Add-Content .env "`nFRONTEND_URL=$($env:FRONTEND_URL)"
```

---

## 7. Validate End-to-End Functionality

1. Open frontend URL in browser.
2. Submit an incident in UI.
3. Confirm agent flow and final conclusion appear.
4. Validate backend endpoint directly:

```powershell
Invoke-RestMethod -Uri "$env:BACKEND_URL/api/trace/execute" -Method Post -ContentType "application/json" -Body '{"incident_text":"Finance reconciliation failed after token rotation and fallback patch.","include_raw_data":false}'
```

---

## 8. Share With Testers

Share:

- Frontend URL: main entry point for testers
- Optional backend health URL: `/api/health`

For demo stability, set Cloud Run min instances to 1:

```powershell
gcloud run services update $env:BACKEND_SERVICE --region $env:REGION --min-instances 1 --project $env:PROJECT_ID
gcloud run services update $env:FRONTEND_SERVICE --region $env:REGION --min-instances 1 --project $env:PROJECT_ID
```

---

## 9. Common Issues and Quick Fixes

- **CORS errors in browser**
  - Ensure backend CORS allows frontend Cloud Run domain.

- **401/403 BigQuery or Secret access**
  - Re-check IAM roles on Cloud Run service account.

- **Frontend cannot reach backend**
  - Verify `VITE_API_BASE_URL` was set correctly at frontend build time.

- **Cold starts during demos**
  - Set min instances to 1 as shown above.

---

## 10. Optional Hardening (Post-Demo)

- Restrict backend ingress/auth and place frontend behind custom domain.
- Use dataset-level BigQuery IAM instead of project-level roles.
- Add Cloud Logging dashboards and alerting.
- Move to CI/CD (Cloud Build trigger from GitHub).
