import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.knowledge_agent import knowledge_agent
from app.models.conversation import Conversation, Message, MessageRole, IntentType


@pytest.fixture
def sample_conversation():
    conv = Conversation(
        session_id="test_session_002",
        user_id="test_user_002"
    )
    return conv


class TestKnowledgeAgent:

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_by_query(self, sample_conversation):
        query = "这件衣服有没有大码的"

        result = knowledge_agent.retrieve_knowledge(query, "size_guide", {})

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_with_intent(self, sample_conversation):
        query = "退货可以吗"
        intent = "return_request"

        result = knowledge_agent.retrieve_knowledge(query, intent, {})

        assert isinstance(result.items, list)
        if result.items:
            assert result.scores[0] > 0

    @pytest.mark.asyncio
    async def test_retrieve_knowledge_empty_result(self, sample_conversation):
        query = "这是一个完全不相关的问题 xyz123456"

        result = knowledge_agent.retrieve_knowledge(query, "unknown", {})

        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_format_knowledge_response(self, sample_conversation):
        from app.models.conversation import KnowledgeRetrievalResult, KnowledgeItem

        items = [
            KnowledgeItem(
                kb_id="faq",
                item_id="faq_001",
                category="测试",
                question="测试问题",
                answer="这是测试答案"
            )
        ]
        result = KnowledgeRetrievalResult(items=items, scores=[0.9])

        response = knowledge_agent._format_knowledge_response(result, "test")

        assert "测试答案" in response

    @pytest.mark.asyncio
    async def test_process_with_conversation(self, sample_conversation):
        sample_conversation.add_message(Message(role=MessageRole.USER, content="请问有的大码吗"))
        sample_conversation.context["current_intent"] = "size_guide"

        response = await knowledge_agent.process(sample_conversation)

        assert response.success is True
        assert len(response.content) > 0

    def test_load_knowledge_base(self):
        assert len(knowledge_agent.knowledge_base) > 0

    def test_knowledge_base_has_required_fields(self):
        for item in knowledge_agent.knowledge_base:
            assert item.kb_id
            assert item.question
            assert item.answer
