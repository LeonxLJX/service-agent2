from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.models.conversation import Conversation, Message, MessageRole, IntentType, IntentRecognitionResult
from app.agents.intent_agent import intent_agent
from loguru import logger

router = APIRouter(prefix="/api/v1/intent", tags=["intent"])


class IntentRecognizeRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    context: Optional[Dict[str, Any]] = {}


class IntentRecognizeResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]]


@router.post("/recognize", response_model=IntentRecognizeResponse)
async def recognize_intent(request: IntentRecognizeRequest):
    try:
        conversation = Conversation(
            session_id="temp",
            user_id="temp",
            history=[
                Message(role=MessageRole.USER, content=msg["content"])
                for msg in (request.history or [])
            ]
        )
        conversation.add_message(Message(role=MessageRole.USER, content=request.message))

        result = intent_agent.recognize_intent(request.message, conversation)

        return IntentRecognizeResponse(
            code=0,
            message="success",
            data={
                "intent": result.intent.value,
                "sub_intent": result.sub_intent,
                "confidence": result.confidence,
                "entities": result.entities,
                "suggestions": result.suggestions
            }
        )
    except Exception as e:
        logger.error(f"Intent recognition error: {e}")
        return IntentRecognizeResponse(
            code=500,
            message=str(e),
            data=None
        )
