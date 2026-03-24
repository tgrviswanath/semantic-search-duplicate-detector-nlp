from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.service import add_documents, search, find_duplicates, get_stats, clear_index
import httpx

router = APIRouter(prefix="/api/v1", tags=["search"])


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


def _handle(e: Exception):
    if isinstance(e, httpx.ConnectError):
        raise HTTPException(status_code=503, detail="NLP service unavailable")
    if isinstance(e, httpx.HTTPStatusError):
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents")
async def add_docs(body: AddDocsInput):
    try:
        return await add_documents([d.model_dump() for d in body.documents])
    except Exception as e:
        _handle(e)


@router.post("/search")
async def search_endpoint(body: SearchInput):
    try:
        return await search(body.query, body.top_k, body.rerank)
    except Exception as e:
        _handle(e)


@router.post("/duplicates")
async def duplicates_endpoint(body: DuplicateInput):
    try:
        return await find_duplicates(body.texts, body.threshold)
    except Exception as e:
        _handle(e)


@router.get("/stats")
async def stats():
    try:
        return await get_stats()
    except Exception as e:
        _handle(e)


@router.delete("/documents")
async def clear():
    try:
        return await clear_index()
    except Exception as e:
        _handle(e)
