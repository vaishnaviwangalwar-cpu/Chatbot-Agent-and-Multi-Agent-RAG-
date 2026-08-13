# GCP Deployment Guide — Campus AI ChatBot Agent

This guide provides step-by-step instructions for containerizing and deploying the **Campus AI ChatBot Agent** to **Google Cloud Platform (GCP)** using **Google Cloud Run**.

---

## 1. Quick Deployment to Google Cloud Run (Recommended)

Execute these 4 steps in your terminal to build and deploy the application to GCP Cloud Run:

### Step 1: Enable Required GCP APIs
```bash
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com
```

### Step 2: Create Artifact Registry Repository
```bash
gcloud artifacts repositories create campus-ai-repo \
  --repository-format=docker \
  --location=asia-south1 \
  --description="Docker repository for Campus AI ChatBot Agent"
```

### Step 3: Build & Push Container Image (GCP Cloud Build)
```bash
export PROJECT_ID=$(gcloud config get-value project)
export IMAGE_URI="asia-south1-docker.pkg.dev/${PROJECT_ID}/campus-ai-repo/campus-ai-agent:v1"

gcloud builds submit --tag ${IMAGE_URI} .
```

### Step 4: Deploy to Cloud Run & Enable Public Access
```bash
gcloud run deploy campus-ai-agent \
  --image ${IMAGE_URI} \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars "GEMINI_API_KEY=your_gemini_api_key,GEMINI_MODEL=gemini-3.1-flash-lite,APP_ENV=production,THINKING_LEVEL=MINIMAL"

# Make service publicly accessible via web browser
gcloud run services add-iam-policy-binding campus-ai-agent \
  --region asia-south1 \
  --member allUsers \
  --role roles/run.invoker
```

---

## 2. Local Container Testing

Test the container locally on your workstation before pushing to GCP:

```bash
# Build local image
docker build -t campus-ai-agent:v1 .

# Run container passing local .env file
docker run -d -p 8000:8000 --name campus-ai-container --env-file .env campus-ai-agent:v1

# Test health endpoint
curl http://localhost:8000/health
```

---

## 3. Advanced Configurations

### Option A: Secret Manager for API Key (Production Best Practice)
Avoid hardcoding API keys in environment variables:

```bash
# 1. Store API key in GCP Secret Manager
echo -n "your_gemini_api_key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# 2. Deploy Cloud Run referencing Secret Manager
gcloud run deploy campus-ai-agent \
  --image ${IMAGE_URI} \
  --region asia-south1 \
  --port 8000 \
  --set-env-vars "GEMINI_MODEL=gemini-3.1-flash-lite,APP_ENV=production" \
  --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest"
```

### Option B: Internal Ingress & Identity-Aware Proxy (IAP)
Restrict access to internal Google Workspace users via SSO Load Balancer:

```bash
# Restrict Cloud Run ingress to internal load balancer traffic
gcloud run services update campus-ai-agent \
  --region asia-south1 \
  --ingress internal-and-cloud-load-balancing
```

---

## 4. Post-Deployment Verification

Verify your live Cloud Run service:

```bash
export SERVICE_URL=$(gcloud run services describe campus-ai-agent --region asia-south1 --format 'value(status.url)')

# Health check
curl ${SERVICE_URL}/health

# Test chat endpoint
curl -X POST ${SERVICE_URL}/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "gcp_test", "message": "What time is it right now?", "prompt_style": "structured_xml"}'
```
