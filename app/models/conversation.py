from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    CARD = "card"
    TEMPLATE = "template"


class Message(BaseModel):
    msg_id: str = Field(default="", description="消息ID")
    role: MessageRole = Field(default=MessageRole.USER, description="角色")
    content: str = Field(default="", description="消息内容")
    type: MessageType = Field(default=MessageType.TEXT, description="消息类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class Conversation(BaseModel):
    session_id: str = Field(default="", description="会话ID")
    user_id: str = Field(default="", description="用户ID")
    shop_id: str = Field(default="", description="店铺ID")
    platform: str = Field(default="taobao", description="平台")
    history: List[Message] = Field(default_factory=list, description="对话历史")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    current_intent: Optional[str] = Field(default=None, description="当前意图")
    state: str = Field(default="active", description="会话状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    def add_message(self, message: Message):
        self.history.append(message)
        self.updated_at = datetime.now()

    def get_history_text(self, max_turns: int = 10) -> str:
        recent_history = self.history[-max_turns * 2:] if len(self.history) > max_turns * 2 else self.history
        return "\n".join([f"{msg.role.value}: {msg.content}" for msg in recent_history])


class IntentType(str, Enum):
    PRODUCT_INQUIRY = "product_inquiry"
    SIZE_GUIDE = "size_guide"
    COLOR_SELECTION = "color_selection"
    PRICE_QUERY = "price_query"
    ORDER_STATUS = "order_status"
    LOGISTICS_QUERY = "logistics_query"
    DELIVERY_TIME = "delivery_time"
    RETURN_REQUEST = "return_request"
    EXCHANGE_REQUEST = "exchange_request"
    COMPLAINT = "complaint"
    REFUND_STATUS = "refund_status"
    REFUND_APPLICATION = "refund_application"
    PRODUCT_COMPLAINT = "product_complaint"
    SERVICE_COMPLAINT = "service_complaint"
    SUGGESTION = "suggestion"
    GREETING = "greeting"
    UNKNOWN = "unknown"


class IntentRecognitionResult(BaseModel):
    intent: IntentType = Field(default=IntentType.UNKNOWN, description="主意图")
    sub_intent: Optional[str] = Field(default=None, description="子意图")
    confidence: float = Field(default=0.0, description="置信度")
    entities: Dict[str, str] = Field(default_factory=dict, description="识别的实体")
    suggestions: List[str] = Field(default_factory=list, description="建议操作")


class KnowledgeItem(BaseModel):
    kb_id: str = Field(default="default", description="知识库ID")
    item_id: str = Field(default="", description="条目ID")
    category: str = Field(default="", description="分类")
    question: str = Field(default="", description="问题")
    answer: str = Field(default="", description="答案")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class KnowledgeRetrievalResult(BaseModel):
    items: List[KnowledgeItem] = Field(default_factory=list, description="检索结果")
    scores: List[float] = Field(default_factory=list, description="相似度分数")


class OrderInfo(BaseModel):
    order_id: str = Field(default="", description="订单ID")
    status: str = Field(default="", description="订单状态")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="商品列表")
    total_amount: float = Field(default=0.0, description="总金额")
    shipping: Optional[Dict[str, Any]] = Field(default=None, description="物流信息")
    created_at: str = Field(default="", description="创建时间")


class LogisticsInfo(BaseModel):
    order_id: str = Field(default="", description="订单ID")
    company: str = Field(default="", description="物流公司")
    tracking_no: str = Field(default="", description="运单号")
    status: str = Field(default="", description="物流状态")
    traces: List[Dict[str, str]] = Field(default_factory=list, description="物流轨迹")
    estimated_delivery: Optional[str] = Field(default=None, description="预计送达时间")


class AfterSalesInfo(BaseModel):
    ticket_id: str = Field(default="", description="工单ID")
    type: str = Field(default="", description="售后类型")
    status: str = Field(default="", description="处理状态")
    description: str = Field(default="", description="问题描述")
    created_at: str = Field(default="", description="创建时间")


class AgentResponse(BaseModel):
    success: bool = Field(default=True, description="是否成功")
    content: str = Field(default="", description="回复内容")
    intent: Optional[IntentType] = Field(default=None, description="识别的意图")
    need_human_intervention: bool = Field(default=False, description="是否需要人工介入")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
