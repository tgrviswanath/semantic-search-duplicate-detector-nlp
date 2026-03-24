import httpx
from app.core.config import settings

NLP_URL = settings.NLP_SERVICE_URL


async def add_documents(documents: list[dict]) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{NLP_URL}/api/v1/nlp/documents",
                              json={"documents": documents}, timeout=60.0)
        r.raise_for_status()
        return r.json()


async def search(query: str, top_k: int, rerank: bool) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{NLP_URL}/api/v1/nlp/search",
                              json={"query": query, "top_k": top_k, "rerank": rerank},
                              timeout=60.0)
        r.raise_for_status()
        return r.json()


async def find_duplicates(texts: list[str], threshold: float) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{NLP_URL}/api/v1/nlp/duplicates",
                              json={"texts": texts, "threshold": threshold},
                              timeout=60.0)
        r.raise_for_status()
        return r.json()


async def get_stats() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{NLP_URL}/api/v1/nlp/stats", timeout=10.0)
        r.raise_for_status()
        return r.json()


async def clear_index() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{NLP_URL}/api/v1/nlp/documents", timeout=10.0)
        r.raise_for_status()
        return r.json()
