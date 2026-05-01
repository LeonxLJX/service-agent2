from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List
from app.models.conversation import KnowledgeItem, KnowledgeRetrievalResult
from app.agents.knowledge_agent import knowledge_agent
from loguru import logger

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


class KnowledgeRetrieveRequest(BaseModel):
    query: str
    intent: Optional[str] = "unknown"
    entities: Optional[dict] = {}
    top_k: Optional[int] = 5


class KnowledgeRetrieveResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict]


@router.post("/retrieve", response_model=KnowledgeRetrieveResponse)
async def retrieve_knowledge(request: KnowledgeRetrieveRequest):
    try:
        result = knowledge_agent.retrieve_knowledge(
            query=request.query,
            intent=request.intent,
            entities=request.entities or {}
        )

        items_data = []
        for item in result.items:
            items_data.append({
                "kb_id": item.kb_id,
                "item_id": item.item_id,
                "category": item.category,
                "question": item.question,
                "answer": item.answer
            })

        return KnowledgeRetrieveResponse(
            code=0,
            message="success",
            data={
                "items": items_data,
                "scores": result.scores
            }
        )
    except Exception as e:
        logger.error(f"Knowledge retrieval error: {e}")
        return KnowledgeRetrieveResponse(
            code=500,
            message=str(e),
            data=None
        )


class KnowledgeAddRequest(BaseModel):
    kb_id: str
    category: str
    question: str
    answer: str
    metadata: Optional[dict] = {}


class KnowledgeAddResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict]


@router.post("/add", response_model=KnowledgeAddResponse)
async def add_knowledge(request: KnowledgeAddRequest):
    try:
        from app.services.vector_service import vector_service

        item = KnowledgeItem(
            kb_id=request.kb_id,
            item_id=f"kb_{len(knowledge_agent.knowledge_base)}",
            category=request.category,
            question=request.question,
            answer=request.answer,
            metadata=request.metadata
        )

        knowledge_agent.knowledge_base.append(item)

        vector = vector_service.text_to_vector(request.question + " " + request.answer)
        vector_service.add_vector(vector, item.model_dump())

        return KnowledgeAddResponse(
            code=0,
            message="success",
            data={"item_id": item.item_id}
        )
    except Exception as e:
        logger.error(f"Add knowledge error: {e}")
        return KnowledgeAddResponse(
            code=500,
            message=str(e),
            data=None
        )
