from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.adapters.mimo_adapter import mimo_adapter, MIMOWebhookEvent
from app.models.conversation import Conversation, Message, MessageRole
from app.agents.intent_agent import intent_agent
from app.agents.knowledge_agent import knowledge_agent
from app.agents.dialogue_agent import dialogue_agent
from app.agents.order_agent import order_agent
from app.config import settings
from loguru import logger
import uuid

router = APIRouter(prefix="/api/v1/mimo", tags=["mimo"])


class WebhookRequest(BaseModel):
    event: str
    platform: str
    shop_id: str
    customer: Dict[str, str]
    message: Dict[str, Any]
    session: Dict[str, Any]
    timestamp: int


class WebhookResponse(BaseModel):
    code: int
    message: str
    data: Optional[Dict[str, Any]]


conversations_cache: Dict[str, Conversation] = {}


@router.post("/webhook", response_model=WebhookResponse)
async def handle_webhook(
    request: Request,
    x_mimo_signature: Optional[str] = Header(None),
    x_mimo_timestamp: Optional[str] = Header(None)
):
    body = await request.json()

    if x_mimo_signature and x_mimo_timestamp:
        try:
            timestamp = int(x_mimo_timestamp)
            if not mimo_adapter.verify_webhook_signature(x_mimo_signature, timestamp, str(body)):
                raise HTTPException(status_code=401, detail="Invalid signature")
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid timestamp format")

    event = mimo_adapter.parse_webhook_event(body)
    if not event:
        raise HTTPException(status_code=400, detail="Invalid event format")

    if event.event != "message.receive":
        return WebhookResponse(code=0, message="ignored")

    session_id = event.session.get("session_id", str(uuid.uuid4()))
    user_id = event.customer.get("open_id", "")

    if session_id not in conversations_cache:
        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            shop_id=event.shop_id,
            platform=event.platform
        )
        conversations_cache[session_id] = conversation
    else:
        conversation = conversations_cache[session_id]

    user_message = Message(
        msg_id=event.message.get("msg_id", ""),
        role=MessageRole.USER,
        content=event.message.get("content", ""),
        timestamp=datetime.fromtimestamp(event.timestamp / 1000)
    )
    conversation.add_message(user_message)

    response_content = await process_message(conversation)

    need_human = False
    if "人工" in response_content or "联系" in response_content:
        need_human = True

    mimo_response = mimo_adapter.format_response(
        msg_id=user_message.msg_id,
        handled=True,
        content=response_content,
        need_human_intervention=need_human
    )

    return WebhookResponse(**mimo_response.model_dump())


async def process_message(conversation: Conversation) -> str:
    intent_response = await intent_agent.process(conversation)

    if not intent_response.success:
        return intent_response.content

    intent_value = intent_response.metadata.get("intent", {}).get("intent", "unknown")
    conversation.context["current_intent"] = intent_value
    conversation.context["entities"] = intent_response.metadata.get("intent", {}).get("entities", {})

    order_intents = ["order_status", "logistics_query", "delivery_time", "return_request",
                     "exchange_request", "refund_status", "refund_application"]

    if any(intent_value == intent for intent in order_intents):
        order_response = await order_agent.process(conversation)
        if order_response.success and order_response.content:
            return order_response.content

    knowledge_response = await knowledge_agent.process(conversation)
    knowledge_content = ""
    if knowledge_response.metadata.get("retrieval_result", {}).get("items"):
        items = knowledge_response.metadata["retrieval_result"]["items"]
        knowledge_content = "\n".join([item.get("answer", "") for item in items[:2]])

    dialogue_response = await dialogue_agent.process(
        conversation,
        knowledge_content=knowledge_content,
        knowledge_context=knowledge_response.content
    )

    if dialogue_response.success and dialogue_response.content:
        return dialogue_response.content

    return intent_response.content


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "mimo-adapter"}
