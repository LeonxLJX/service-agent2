import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.order_agent import order_agent
from app.models.conversation import Conversation, Message, MessageRole, IntentType


@pytest.fixture
def sample_conversation():
    conv = Conversation(
        session_id="test_session_004",
        user_id="test_user_004"
    )
    return conv


class TestOrderAgent:

    @pytest.mark.asyncio
    async def test_query_order_with_order_id(self, sample_conversation):
        sample_conversation.add_message(Message(role=MessageRole.USER, content="查询订单TK100001"))
        sample_conversation.context = {
            "current_intent": "order_status",
            "entities": {"order_id": "TK100001"}
        }

        response = await order_agent.process(sample_conversation)

        assert response.success is True
        assert "订单" in response.content or "未找到" in response.content

    @pytest.mark.asyncio
    async def test_query_order_without_order_id(self, sample_conversation):
        sample_conversation.add_message(Message(role=MessageRole.USER, content="帮我查一下订单"))
        sample_conversation.context = {"current_intent": "order_status"}

        response = await order_agent.process(sample_conversation)

        assert response.success is True
        assert "订单号" in response.content or "order_id" in response.content.lower()

    @pytest.mark.asyncio
    async def test_query_logistics(self, sample_conversation):
        sample_conversation.add_message(Message(role=MessageRole.USER, content="帮我查一下物流"))
        sample_conversation.context = {
            "current_intent": "logistics_query",
            "entities": {"order_id": "TK100001"}
        }

        response = await order_agent.process(sample_conversation)

        assert response.success is True

    @pytest.mark.asyncio
    async def test_handle_return_request_with_order_id(self, sample_conversation):
        sample_conversation.add_message(Message(role=MessageRole.USER, content="我要退货"))
        sample_conversation.context = {
            "current_intent": "return_request",
            "entities": {"order_id": "TK100001"}
        }

        response = await order_agent.process(sample_conversation)

        assert response.success is True
        assert "退货" in response.content or "工单" in response.content

    @pytest.mark.asyncio
    async def test_handle_exchange_request(self, sample_conversation):
        sample_conversation.add_message(Message(role=MessageRole.USER, content="我想换货"))
        sample_conversation.context = {
            "current_intent": "exchange_request",
            "entities": {"order_id": "TK100001"}
        }

        response = await order_agent.process(sample_conversation)

        assert response.success is True
        assert "换货" in response.content or "工单" in response.content

    @pytest.mark.asyncio
    async def test_handle_refund_query(self, sample_conversation):
        sample_conversation.add_message(Message(role=MessageRole.USER, content="退款什么时候到账"))
        sample_conversation.context = {
            "current_intent": "refund_status",
            "entities": {"order_id": "TK100001"}
        }

        response = await order_agent.process(sample_conversation)

        assert response.success is True

    def test_extract_order_id_from_message(self):
        message = "查询订单TK100001的状态"

        order_id = order_agent._extract_order_id(message)

        assert order_id == "TK100001"

    def test_extract_order_id_with_pattern(self):
        message = "我的订单号是 TK100002"

        order_id = order_agent._extract_order_id(message)

        assert order_id == "TK100002"

    def test_extract_order_id_not_found(self):
        message = "我没有订单号"

        order_id = order_agent._extract_order_id(message)

        assert order_id is None

    def test_mock_orders_exist(self):
        assert len(order_agent.mock_orders) > 0
        assert "TK100001" in order_agent.mock_orders
