# Azure Deployment Guide — Project 10 Semantic Search & Duplicate Detector

---

## Azure Services for Semantic Search

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Azure AI Search**                  | Managed semantic search with vector search and hybrid ranking                | Replace your sentence-transformers + FAISS pipeline |
| **Azure OpenAI Embeddings**          | text-embedding-ada-002 for generating document/query embeddings              | Replace your sentence-transformers model           |
| **Azure AI Search — Semantic Ranker**| Re-rank results using language model understanding                           | Replace your CrossEncoder re-ranking               |

> **Azure AI Search with vector search** is the direct replacement for your bi-encoder + FAISS + CrossEncoder pipeline. It handles embedding storage, ANN search, and semantic re-ranking natively.

### 2. Host Your Own Model (Keep Current Stack)

| Service                        | What it does                                                        | When to use                                           |
|--------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Container Apps**       | Run your 3 Docker containers (frontend, backend, nlp-service)       | Best match for your current microservice architecture |
| **Azure Container Registry**   | Store your Docker images                                            | Used with Container Apps or AKS                       |

### 3. Train and Manage Your Model

| Service                        | What it does                                                              | When to use                                           |
|--------------------------------|---------------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Machine Learning**     | Fine-tune bi-encoder on domain-specific data, deploy managed endpoints    | When you need domain-specific semantic search         |

### 4. Frontend Hosting

| Service                   | What it does                                                               |
|---------------------------|----------------------------------------------------------------------------|
| **Azure Static Web Apps** | Host your React frontend — free tier available, auto CI/CD from GitHub     |

### 5. Supporting Services

| Service                       | Purpose                                                                  |
|-------------------------------|--------------------------------------------------------------------------|
| **Azure AI Search**           | Persistent vector index — replace in-memory FAISS                       |
| **Azure Key Vault**           | Store API keys and connection strings instead of .env files              |
| **Azure Monitor + App Insights** | Track search latency, similarity scores, request volume              |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Static Web Apps — React Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Azure Container Apps — Backend (FastAPI :8000)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Container Apps    │    │ Azure AI Search (vector)           │
│ NLP Service :8001 │    │ + Azure OpenAI Embeddings          │
│ sentence-trans+   │    │ No model maintenance needed        │
│ FAISS             │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
az login
az group create --name rg-semantic-search --location uksouth
az extension add --name containerapp --upgrade
```

---

## Step 1 — Create Container Registry and Push Images

```bash
az acr create --resource-group rg-semantic-search --name semsearchacr --sku Basic --admin-enabled true
az acr login --name semsearchacr
ACR=semsearchacr.azurecr.io
docker build -f docker/Dockerfile.nlp-service -t $ACR/nlp-service:latest ./nlp-service
docker push $ACR/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $ACR/backend:latest ./backend
docker push $ACR/backend:latest
```

---

## Step 2 — Deploy Container Apps

```bash
az containerapp env create --name semsearch-env --resource-group rg-semantic-search --location uksouth

az containerapp create \
  --name nlp-service --resource-group rg-semantic-search \
  --environment semsearch-env --image $ACR/nlp-service:latest \
  --registry-server $ACR --target-port 8001 --ingress internal \
  --min-replicas 1 --max-replicas 3 --cpu 1 --memory 2.0Gi

az containerapp create \
  --name backend --resource-group rg-semantic-search \
  --environment semsearch-env --image $ACR/backend:latest \
  --registry-server $ACR --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1.0Gi \
  --env-vars NLP_SERVICE_URL=http://nlp-service:8001
```

---

## Option B — Use Azure AI Search with Vector Search

```bash
az search service create \
  --name semsearch-service \
  --resource-group rg-semantic-search \
  --sku basic \
  --location uksouth
```

```python
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name="documents",
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)

def search(query_vector: list, top_k: int = 5) -> dict:
    vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="embedding")
    results = search_client.search(search_text=None, vector_queries=[vector_query])
    return {"results": [{"id": r["id"], "content": r["content"], "score": r["@search.score"]} for r in results]}
```

Add to requirements.txt: `azure-search-documents>=11.4.0`

---

## CI/CD — GitHub Actions

```yaml
name: Deploy to Azure
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - run: az acr login --name semsearchacr
      - run: |
          docker build -f docker/Dockerfile.backend -t semsearchacr.azurecr.io/backend:${{ github.sha }} ./backend
          docker push semsearchacr.azurecr.io/backend:${{ github.sha }}
          az containerapp update --name backend --resource-group rg-semantic-search \
            --image semsearchacr.azurecr.io/backend:${{ github.sha }}
```

---

## Estimated Monthly Cost

| Service                  | Tier      | Est. Cost         |
|--------------------------|-----------|-------------------|
| Container Apps (backend) | 0.5 vCPU  | ~$10–15/month     |
| Container Apps (nlp-svc) | 1 vCPU    | ~$15–20/month     |
| Container Registry       | Basic     | ~$5/month         |
| Static Web Apps          | Free      | $0                |
| Azure AI Search          | Basic     | ~$75/month        |
| **Total (Option A)**     |           | **~$30–40/month** |
| **Total (Option B)**     |           | **~$95–115/month**|

For exact estimates → https://calculator.azure.com

---

## Teardown

```bash
az group delete --name rg-semantic-search --yes --no-wait
```
