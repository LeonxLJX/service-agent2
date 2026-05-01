import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.intent_agent import intent_agent
from app.models.conversation import Conversation, Message, MessageRole, IntentType


@pytest.fixture
def sample_conversation():
    conv = Conversation(
        session_id="test_session_001",
        user_id="test_user_001"
    )
    return conv


class TestIntentAgent:

    @pytest.mark.asyncio
    async def test_recognize_size_intent(self, sample_conversation):
        message = "这件衣服有没有大码的？"
        sample_conversation.add_message(Message(role=MessageRole.USER, content=message))

        result = intent_agent.recognize_intent(message, sample_conversation)

        assert result.intent == IntentType.SIZE_GUIDE
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_recognize_greeting_intent(self, sample_conversation):
        message = "你好"
        sample_conversation.add_message(Message(role=MessageRole.USER, content=message))

        result = intent_agent.recognize_intent(message, sample_conversation)

        assert result.intent == IntentType.GREETING
        assert result.confidence > 0.3

    @pytest.mark.asyncio
    async def test_recognize_price_intent(self, sample_conversation):
        message = "这件衣服多少钱？"
        sample_conversation.add_message(Message(role=MessageRole.USER, content=message))

        result = intent_agent.recognize_intent(message, sample_conversation)

        assert result.intent == IntentType.PRICE_QUERY
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_recognize_logistics_intent(self, sample_conversation):
        message = "我的快递到哪了？"
        sample_conversation.add_message(Message(role=MessageRole.USER, content=message))

        result = intent_agent.recognize_intent(message, sample_conversation)

        assert result.intent == IntentType.LOGISTICS_QUERY
        assert result.confidence > 0.4

    @pytest.mark.asyncio
    async def test_recognize_return_intent(self, sample_conversation):
        message = "我想退货"
        sample_conversation.add_message(Message(role=MessageRole.USER, content=message))

        result = intent_agent.recognize_intent(message, sample_conversation)

        assert result.intent == IntentType.RETURN_REQUEST
        assert result.confidence > 0.4

    @pytest.mark.asyncio
    async def test_entity_extraction_order_id(self, sample_conversation):
        message = "我的订单TK100001什么时候到？"
        sample_conversation.add_message(Message(role=MessageRole.USER, content=message))

        result = intent_agent.recognize_intent(message, sample_conversation)

        assert "order_id" in result.entities or "order" in str(result.entities).lower()

    @pytest.mark.asyncio
    async def test_entity_extraction_size(self, sample_conversation):
        message = "这件衣服有XL码的吗？"
        sample_conversation.add_message(Message(role=MessageRole.USER, content=message))

        result = intent_agent.recognize_intent(message, sample_conversation)

        assert "size" in result.entities or "xl" in result.entities.get("size", "").lower()

    @pytest.mark.asyncio
    async def test_process_with_greeting(self, sample_conversation):
        sample_conversation.add_message(Message(role=MessageRole.USER, content="你好"))

        response = await intent_agent.process(sample_conversation)

        assert response.success is True
        assert "您好" in response.content or "你好" in response.content
