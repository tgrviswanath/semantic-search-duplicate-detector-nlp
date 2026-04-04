# AWS Deployment Guide — Project 10 Semantic Search & Duplicate Detector

---

## AWS Services for Semantic Search

### 1. Ready-to-Use AI (No Model Needed)

| Service                    | What it does                                                                 | When to use                                        |
|----------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Amazon Kendra**          | Managed semantic search over documents — no embeddings or FAISS needed       | Replace your sentence-transformers + FAISS pipeline |
| **Amazon OpenSearch**      | Vector search with k-NN plugin — store and query embeddings at scale         | When you need scalable vector search               |
| **Amazon Bedrock**         | Titan Embeddings for generating document/query embeddings                    | Replace your sentence-transformers model           |

> **Amazon Kendra** is the direct replacement for your bi-encoder + FAISS pipeline. It handles semantic search, re-ranking, and duplicate detection out of the box.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS App Runner**         | Run backend container — simplest, no VPC or cluster needed          | Quickest path to production                           |
| **Amazon ECS Fargate**     | Run backend + nlp-service containers in a private VPC               | Best match for your current microservice architecture |
| **Amazon ECR**             | Store your Docker images                                            | Used with App Runner, ECS, or EKS                     |

### 3. Train and Manage Your Model

| Service                         | What it does                                                        | When to use                                           |
|---------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS SageMaker**               | Fine-tune bi-encoder or cross-encoder on domain-specific data       | When you need domain-specific semantic search         |
| **SageMaker Managed Endpoints** | Serve your sentence-transformers model as a REST endpoint           | Replace nlp-service with a managed inference endpoint |

### 4. Frontend Hosting

| Service               | What it does                                                                  |
|-----------------------|-------------------------------------------------------------------------------|
| **Amazon S3**         | Host your React build as a static website                                     |
| **Amazon CloudFront** | CDN in front of S3 — HTTPS, low latency globally                              |

### 5. Supporting Services

| Service                  | Purpose                                                                   |
|--------------------------|---------------------------------------------------------------------------|
| **Amazon OpenSearch**    | Persistent vector index — replace in-memory FAISS                        |
| **AWS Secrets Manager**  | Store API keys and connection strings instead of .env files               |
| **Amazon CloudWatch**    | Track search latency, similarity scores, request volume                   |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 + CloudFront — React Frontend                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  AWS App Runner / ECS Fargate — Backend (FastAPI :8000)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ ECS Fargate       │    │ Amazon Kendra                      │
│ NLP Service :8001 │    │ + Amazon OpenSearch (vector)       │
│ sentence-trans+   │    │ No model maintenance needed        │
│ FAISS             │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
aws configure
AWS_REGION=eu-west-2
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
```

---

## Step 1 — Create ECR and Push Images

```bash
aws ecr create-repository --repository-name semsearch/nlp-service --region $AWS_REGION
aws ecr create-repository --repository-name semsearch/backend --region $AWS_REGION
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
docker build -f docker/Dockerfile.nlp-service -t $ECR/semsearch/nlp-service:latest ./nlp-service
docker push $ECR/semsearch/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $ECR/semsearch/backend:latest ./backend
docker push $ECR/semsearch/backend:latest
```

---

## Step 2 — Deploy with App Runner

```bash
aws apprunner create-service \
  --service-name semsearch-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR'/semsearch/backend:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "NLP_SERVICE_URL": "http://nlp-service:8001"
        }
      }
    }
  }' \
  --instance-configuration '{"Cpu": "1 vCPU", "Memory": "2 GB"}' \
  --region $AWS_REGION
```

---

## Option B — Use Amazon Kendra

```python
import boto3

kendra = boto3.client("kendra", region_name="eu-west-2")

def search(query: str, index_id: str) -> dict:
    result = kendra.query(IndexId=index_id, QueryText=query)
    items = []
    for item in result.get("ResultItems", []):
        items.append({
            "title": item.get("DocumentTitle", {}).get("Text", ""),
            "excerpt": item.get("DocumentExcerpt", {}).get("Text", ""),
            "score": item.get("ScoreAttributes", {}).get("ScoreConfidence", "")
        })
    return {"results": items, "total": len(items)}
```

Add to requirements.txt: `boto3>=1.34.0`

---

## CI/CD — GitHub Actions

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-west-2
      - uses: aws-actions/amazon-ecr-login@v2
      - run: |
          docker build -f docker/Dockerfile.backend \
            -t ${{ secrets.ECR_REGISTRY }}/semsearch/backend:${{ github.sha }} ./backend
          docker push ${{ secrets.ECR_REGISTRY }}/semsearch/backend:${{ github.sha }}
```

---

## Estimated Monthly Cost

| Service                    | Tier              | Est. Cost          |
|----------------------------|-------------------|--------------------|
| App Runner (backend)       | 1 vCPU / 2 GB     | ~$20–25/month      |
| App Runner (nlp-service)   | 1 vCPU / 2 GB     | ~$20–25/month      |
| ECR + S3 + CloudFront      | Standard          | ~$3–7/month        |
| Amazon Kendra              | Developer edition | ~$810/month        |
| Amazon OpenSearch          | t3.small.search   | ~$25–35/month      |
| **Total (Option A)**       |                   | **~$43–57/month**  |
| **Total (Option B)**       |                   | **~$55–70/month**  |

For exact estimates → https://calculator.aws

---

## Teardown

```bash
aws ecr delete-repository --repository-name semsearch/backend --force
aws ecr delete-repository --repository-name semsearch/nlp-service --force
```
