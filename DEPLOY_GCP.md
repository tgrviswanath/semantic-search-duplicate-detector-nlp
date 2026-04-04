# GCP Deployment Guide — Project 10 Semantic Search & Duplicate Detector

---

## GCP Services for Semantic Search

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Vertex AI Matching Engine**        | Managed vector similarity search at scale — ANN over billions of embeddings  | Replace your FAISS index                           |
| **Vertex AI Embeddings API**         | text-embedding-gecko for generating document/query embeddings                | Replace your sentence-transformers model           |
| **Vertex AI Ranking API**            | Re-rank search results using language model understanding                    | Replace your CrossEncoder re-ranking               |

> **Vertex AI Matching Engine** is the direct replacement for your FAISS index. Pair it with **Vertex AI Embeddings** to replace sentence-transformers entirely.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Cloud Run**              | Run backend + nlp-service containers — serverless, scales to zero   | Best match for your current microservice architecture |
| **Artifact Registry**      | Store your Docker images                                            | Used with Cloud Run or GKE                            |

### 3. Frontend Hosting

| Service                    | What it does                                                              |
|----------------------------|---------------------------------------------------------------------------| 
| **Firebase Hosting**       | Host your React frontend — free tier, auto CI/CD from GitHub              |

### 4. Supporting Services

| Service                        | Purpose                                                                   |
|--------------------------------|---------------------------------------------------------------------------|
| **Secret Manager**             | Store API keys and connection strings instead of .env files               |
| **Cloud Monitoring + Logging** | Track search latency, similarity scores, request volume                   |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Firebase Hosting — React Frontend                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Cloud Run — Backend (FastAPI :8000)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal HTTPS
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Cloud Run         │    │ Vertex AI Matching Engine          │
│ NLP Service :8001 │    │ + Vertex AI Embeddings API         │
│ sentence-trans+   │    │ No model maintenance needed        │
│ FAISS             │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
gcloud auth login
gcloud projects create semsearch-project --name="Semantic Search"
gcloud config set project semsearch-project
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com aiplatform.googleapis.com \
  storage.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Create Artifact Registry and Push Images

```bash
GCP_REGION=europe-west2
gcloud artifacts repositories create semsearch-repo \
  --repository-format=docker --location=$GCP_REGION
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
AR=$GCP_REGION-docker.pkg.dev/semsearch-project/semsearch-repo
docker build -f docker/Dockerfile.nlp-service -t $AR/nlp-service:latest ./nlp-service
docker push $AR/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $AR/backend:latest ./backend
docker push $AR/backend:latest
```

---

## Step 2 — Deploy to Cloud Run

```bash
gcloud run deploy nlp-service \
  --image $AR/nlp-service:latest --region $GCP_REGION \
  --port 8001 --no-allow-unauthenticated \
  --min-instances 1 --max-instances 3 --memory 2Gi --cpu 1

NLP_URL=$(gcloud run services describe nlp-service --region $GCP_REGION --format "value(status.url)")

gcloud run deploy backend \
  --image $AR/backend:latest --region $GCP_REGION \
  --port 8000 --allow-unauthenticated \
  --min-instances 1 --max-instances 5 --memory 1Gi --cpu 1 \
  --set-env-vars NLP_SERVICE_URL=$NLP_URL
```

---

## Option B — Use Vertex AI Matching Engine

```python
from google.cloud import aiplatform

aiplatform.init(project="semsearch-project", location="europe-west2")

index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
    index_endpoint_name="projects/semsearch-project/locations/europe-west2/indexEndpoints/<endpoint-id>"
)

def search(query_embedding: list, top_k: int = 5) -> dict:
    response = index_endpoint.find_neighbors(
        deployed_index_id="semsearch_index",
        queries=[query_embedding],
        num_neighbors=top_k
    )
    results = [{"id": n.id, "distance": n.distance} for n in response[0]]
    return {"results": results}
```

Add to requirements.txt: `google-cloud-aiplatform>=1.50.0`

---

## CI/CD — GitHub Actions

```yaml
name: Deploy to GCP
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker europe-west2-docker.pkg.dev
      - run: |
          docker build -f docker/Dockerfile.backend \
            -t europe-west2-docker.pkg.dev/${{ secrets.GCP_PROJECT }}/semsearch-repo/backend:${{ github.sha }} ./backend
          docker push europe-west2-docker.pkg.dev/${{ secrets.GCP_PROJECT }}/semsearch-repo/backend:${{ github.sha }}
          gcloud run deploy backend \
            --image europe-west2-docker.pkg.dev/${{ secrets.GCP_PROJECT }}/semsearch-repo/backend:${{ github.sha }} \
            --region europe-west2 --platform managed
```

---

## Estimated Monthly Cost

| Service                    | Tier                  | Est. Cost          |
|----------------------------|-----------------------|--------------------|
| Cloud Run (backend)        | 1 vCPU / 1 GB         | ~$10–15/month      |
| Cloud Run (nlp-service)    | 1 vCPU / 2 GB         | ~$12–18/month      |
| Artifact Registry          | Storage               | ~$1–2/month        |
| Firebase Hosting           | Free tier             | $0                 |
| Vertex AI Matching Engine  | Pay per node hour     | ~$65–100/month     |
| **Total (Option A)**       |                       | **~$23–35/month**  |
| **Total (Option B)**       |                       | **~$78–120/month** |

For exact estimates → https://cloud.google.com/products/calculator

---

## Teardown

```bash
gcloud run services delete backend --region $GCP_REGION --quiet
gcloud run services delete nlp-service --region $GCP_REGION --quiet
gcloud artifacts repositories delete semsearch-repo --location=$GCP_REGION --quiet
gcloud projects delete semsearch-project
```
