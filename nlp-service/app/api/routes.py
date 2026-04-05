import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.store import add_documents, search, find_duplicates, get_stats, clear_index

router = APIRouter(prefix="/api/v1/nlp", tags=["semantic-search"])


class Document(BaseModel):
    text: str
    metadata: dict = {}


class AddDocsInput(BaseModel):
    documents: list[Document]


class SearchInput(BaseModel):
    query: str
    top_k: int = 10
    rerank: bool = True


class DuplicateInput(BaseModel):
    texts: list[str]
    threshold: float = 0.85


@router.post("/documents")
async def add_docs(body: AddDocsInput):
    if not body.documents:
        raise HTTPException(status_code=400, detail="documents list cannot be empty")
    try:
        loop = asyncio.get_running_loop()
        total = await loop.run_in_executor(None, add_documents, [d.model_dump() for d in body.documents])
        return {"added": len(body.documents), "total": total}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_endpoint(body: SearchInput):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")
    try:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, search, body.query, body.top_k, body.rerank)
        return {"query": body.query, "results": results, "count": len(results)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/duplicates")
async def duplicates_endpoint(body: DuplicateInput):
    if len(body.texts) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 texts")
    try:
        loop = asyncio.get_running_loop()
        pairs = await loop.run_in_executor(None, find_duplicates, body.texts, body.threshold)
        return {"pairs": pairs, "count": len(pairs), "threshold": body.threshold}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def stats():
    return get_stats()


@router.delete("/documents")
def clear():
    clear_index()
    return {"message": "Index cleared"}
