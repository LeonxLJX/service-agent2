from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.config import settings
from loguru import logger
import hashlib
import hmac
import time


class MIMOMessage(BaseModel):
    msg_id: str = Field(default="", description="消息ID")
    msg_type: str = Field(default="text", description="消息类型")
    content: str = Field(default="", description="消息内容")
    sender_id: str = Field(default="", description="发送者ID")
    sender_nickname: str = Field(default="", description="发送者昵称")
    receiver_id: str = Field(default="", description="接收者ID")
    timestamp: int = Field(default=0, description="时间戳")


class MIMOSession(BaseModel):
    session_id: str = Field(default="", description="会话ID")
    user_id: str = Field(default="", description="用户ID")
    shop_id: str = Field(default="", description="店铺ID")
    platform: str = Field(default="", description="平台")
    context: Dict[str, Any] = Field(default_factory=dict, description="会话上下文")


class MIMOWebhookEvent(BaseModel):
    event: str = Field(default="", description="事件类型")
    platform: str = Field(default="", description="平台")
    shop_id: str = Field(default="", description="店铺ID")
    customer: Dict[str, str] = Field(default_factory=dict, description="客户信息")
    message: Dict[str, Any] = Field(default_factory=dict, description="消息内容")
    session: Dict[str, Any] = Field(default_factory=dict, description="会话信息")
    timestamp: int = Field(default=0, description="时间戳")


class MIMOResponse(BaseModel):
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="状态信息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="响应数据")


class MIMOMessagePayload(BaseModel):
    msg_id: str = Field(default="", description="消息ID")
    content: str = Field(default="", description="消息内容")
    msg_type: str = Field(default="text", description="消息类型")


class MimoAdapter:
    def __init__(self):
        self.app_id = settings.mimo_app_id
        self.app_key = settings.mimo_app_key
        self.api_base = settings.mimo_api_base
        self.webhook_secret = settings.mimo_webhook_secret

    def verify_webhook_signature(self, signature: str, timestamp: int, body: str) -> bool:
        if not self.webhook_secret:
            return True

        expected_signature = self._generate_signature(timestamp, body)
        return hmac.compare_digest(signature, expected_signature)

    def _generate_signature(self, timestamp: int, body: str) -> str:
        data = f"{timestamp}:{body}"
        return hmac.new(
            self.webhook_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

    def parse_webhook_event(self, body: Dict[str, Any]) -> Optional[MIMOWebhookEvent]:
        try:
            return MIMOWebhookEvent(**body)
        except Exception as e:
            logger.error(f"Failed to parse webhook event: {e}")
            return None

    def format_message_for_send(self, content: str, msg_type: str = "text") -> Dict[str, Any]:
        return {
            "msg_id": f"msg_{int(time.time() * 1000)}",
            "content": content,
            "msg_type": msg_type,
            "timestamp": int(time.time() * 1000)
        }

    def format_response(
        self,
        msg_id: str,
        handled: bool = True,
        content: str = "",
        need_human_intervention: bool = False
    ) -> MIMOResponse:
        response_data = {
            "msg_id": msg_id,
            "handled": handled,
            "response": {
                "content": content
            }
        }

        if need_human_intervention:
            response_data["response"]["need_human_intervention"] = True

        return MIMOResponse(
            code=0,
            message="success",
            data=response_data
        )

    def convert_to_conversation(self, event: MIMOWebhookEvent) -> Dict[str, Any]:
        return {
            "session_id": event.session.get("session_id", ""),
            "user_id": event.customer.get("open_id", ""),
            "shop_id": event.shop_id,
            "platform": event.platform,
            "context": event.session.get("context", {})
        }

    def build_quick_replies(self, suggestions: List[str]) -> List[Dict[str, str]]:
        quick_replies = []
        for suggestion in suggestions[:4]:
            quick_replies.append({
                "title": suggestion,
                "action_type": "reply",
                "content": suggestion
            })
        return quick_replies


mimo_adapter = MimoAdapter()
