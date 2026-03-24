# Project 10 - Semantic Search & Duplicate Detector

Microservice NLP project using sentence-transformers (bi-encoder) + FAISS for semantic search, with CrossEncoder re-ranking and pairwise duplicate detection.

## Architecture

```
Frontend :3000  →  Backend :8000  →  NLP Service :8001
  React/MUI        FastAPI/httpx      sentence-transformers + FAISS
```

## Local Run

```bash
# Terminal 1 - NLP Service (models auto-download ~90MB on first request)
cd nlp-service && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Backend
cd backend && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3 - Frontend
cd frontend && npm install && npm start
```

## Docker

```bash
docker-compose up --build
```

## Stack

| Layer | Tools |
|-------|-------|
| NLP Service | sentence-transformers (all-MiniLM-L6-v2), FAISS (IndexFlatIP), CrossEncoder (ms-marco-MiniLM-L-6-v2) |
| Backend | FastAPI, httpx |
| Frontend | React, MUI, Recharts |

## How It Works

### Semantic Search
1. Documents embedded with bi-encoder → stored in FAISS
2. Query embedded → top-K retrieved via cosine similarity
3. CrossEncoder re-ranks results for higher precision

### Duplicate Detection
1. All texts embedded with bi-encoder
2. Pairwise cosine similarity computed
3. Pairs above threshold flagged as duplicates

## Features

- Load 10 sample financial documents with one click
- Semantic search with bi-encoder + optional CrossEncoder re-ranking
- Score visualization per result
- Duplicate detector with adjustable similarity threshold slider
- Index stats (document count, model name)
- Clear index button
