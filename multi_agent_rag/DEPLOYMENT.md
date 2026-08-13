# GCP Deployment Guide — Multi-Agent RAG Assistant

This guide covers containerizing and deploying the Multi-Agent RAG Assistant to **Google Cloud Platform** using **Cloud Run**.

> **Note on ChromaDB persistence**: Cloud Run is stateless — each container restart loses the ChromaDB data stored in `./chroma_db`. For a workshop/demo deployment this is acceptable (the vector store rebuilds from `sample_docs/` on startup). For a production deployment, mount a Cloud Filestore NFS volume or switch to a managed vector DB.

---

## 1. Prerequisites

- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- A GCP project with billing enabled
- Docker installed (for local testing only)

---

## 2. Quick Deployment to Cloud Run

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
gcloud artifacts repositories create multi-agent-rag-repo \
  --repository-format=docker \
  --location=asia-south1 \
  --description="Docker repository for Multi-Agent RAG Assistant"
```

### Step 3: Build & Push Container Image via Cloud Build
```bash
export PROJECT_ID=$(gcloud config get-value project)
export IMAGE_URI="asia-south1-docker.pkg.dev/${PROJECT_ID}/multi-agent-rag-repo/multi-agent-rag:v1"

gcloud builds submit --tag ${IMAGE_URI} .
```

### Step 4: Deploy to Cloud Run
```bash
gcloud run deploy multi-agent-rag \
  --image ${IMAGE_URI} \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8001 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars "GEMINI_MODEL=gemini-3.1-flash-lite,EMBEDDING_MODEL=gemini-embedding-001,CHROMA_PATH=./chroma_db,TOP_K=3" \
  --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest"
```

> The API key is passed via **Secret Manager** (see Section 4) rather than `--set-env-vars` to avoid it appearing in deployment logs.

---

## 3. Local Container Testing

Test the Docker image on your local machine before pushing to GCP:

```bash
# Build local image
docker build -t multi-agent-rag:v1 .

# Run container with local .env file
docker run -d -p 8001:8001 --name multi-agent-rag-container --env-file .env multi-agent-rag:v1

# Test health endpoint
curl http://localhost:8001/health

# Clean up
docker stop multi-agent-rag-container && docker rm multi-agent-rag-container
```

---

## 4. Storing the API Key in Secret Manager (Recommended)

Never hardcode API keys in `--set-env-vars`. Store them in GCP Secret Manager:

```bash
# Create the secret
echo -n "your_gemini_api_key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Grant Cloud Run's service account access to the secret
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Then reference it in deployment with `--set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest"` (already included in Step 4 above).

---

## 5. Post-Deployment Verification

```bash
export SERVICE_URL=$(gcloud run services describe multi-agent-rag --region asia-south1 --format 'value(status.url)')

# Health check
curl ${SERVICE_URL}/health

# Test RAG query
curl -X POST ${SERVICE_URL}/api/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the hostel curfew timing?", "top_k": 3}'

# List indexed documents
curl ${SERVICE_URL}/api/rag/sources
```

---

## 6. Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(required)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Gemini model for generation, routing, and parsing |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Gemini model for vector embeddings |
| `CHROMA_PATH` | `./chroma_db` | Local path for ChromaDB persistence |
| `TOP_K` | `3` | Number of chunks retrieved per query |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8001` | Server bind port |

---

## 7. Restricting Access (Optional)

To lock down the service to internal users only (e.g., via Google Workspace SSO + Identity-Aware Proxy):

```bash
# Restrict ingress to internal load balancer traffic
gcloud run services update multi-agent-rag \
  --region asia-south1 \
  --ingress internal-and-cloud-load-balancing \
  --no-allow-unauthenticated
```
