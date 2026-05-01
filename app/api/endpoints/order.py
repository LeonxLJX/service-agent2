from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from app.agents.order_agent import order_agent
from loguru import logger

router = APIRouter(prefix="/api/v1/agent/order", tags=["order"])


class OrderQueryRequest(BaseModel):
    order_id: Optional[str] = None
    user_id: Optional[str] = None


class OrderQueryResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict]


@router.post("/query", response_model=OrderQueryResponse)
async def query_order(request: OrderQueryRequest):
    try:
        from app.models.conversation import Conversation, Message, MessageRole

        conversation = Conversation(
            session_id="temp",
            user_id=request.user_id or "temp",
            context={"entities": {"order_id": request.order_id}}
        )
        conversation.add_message(Message(
            role=MessageRole.USER,
            content=f"查询订单 {request.order_id}" if request.order_id else "查询订单"
        ))

        response = await order_agent._query_order_status(request.order_id, conversation)

        return OrderQueryResponse(
            code=0,
            message="success",
            data={
                "content": response.content,
                "order": response.metadata.get("order")
            }
        )
    except Exception as e:
        logger.error(f"Order query error: {e}")
        return OrderQueryResponse(
            code=500,
            message=str(e),
            data=None
        )


class LogisticsQueryRequest(BaseModel):
    order_id: Optional[str] = None
    tracking_no: Optional[str] = None


class LogisticsQueryResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict]


@router.post("/logistics/query", response_model=LogisticsQueryResponse)
async def query_logistics(request: LogisticsQueryRequest):
    try:
        from app.models.conversation import Conversation, Message, MessageRole

        conversation = Conversation(
            session_id="temp",
            user_id="temp",
            context={"entities": {"order_id": request.order_id}}
        )
        conversation.add_message(Message(
            role=MessageRole.USER,
            content=f"查询物流 {request.order_id}" if request.order_id else "查询物流"
        ))

        response = await order_agent._query_logistics(request.order_id, conversation)

        return LogisticsQueryResponse(
            code=0,
            message="success",
            data={
                "content": response.content,
                "logistics": response.metadata.get("logistics")
            }
        )
    except Exception as e:
        logger.error(f"Logistics query error: {e}")
        return LogisticsQueryResponse(
            code=500,
            message=str(e),
            data=None
        )
