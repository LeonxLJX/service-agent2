import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.dialogue_agent import dialogue_agent
from app.models.conversation import Conversation, Message, MessageRole


@pytest.fixture
def sample_conversation():
    conv = Conversation(
        session_id="test_session_003",
        user_id="test_user_003"
    )
    conv.add_message(Message(role=MessageRole.USER, content="这件T恤多少钱？"))
    conv.add_message(Message(role=MessageRole.ASSISTANT, content="这款T恤的价格是99元。"))
    conv.add_message(Message(role=MessageRole.USER, content="有没有大码的？"))
    return conv


class TestDialogueAgent:

    @pytest.mark.asyncio
    async def test_process_with_context(self, sample_conversation):
        response = await dialogue_agent.process(sample_conversation)

        assert response.success is True
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_process_with_knowledge_context(self, sample_conversation):
        response = await dialogue_agent.process(
            sample_conversation,
            knowledge_content="这件T恤有S、M、L、XL、XXL五个尺码可选。",
            knowledge_context="用户正在咨询尺码问题"
        )

        assert response.success is True
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_build_messages_with_history(self, sample_conversation):
        messages = dialogue_agent._build_messages(sample_conversation, "", "")

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert any(msg["role"] == "user" for msg in messages)
        assert any(msg["role"] == "assistant" for msg in messages)

    @pytest.mark.asyncio
    async def test_generate_follow_up(self, sample_conversation):
        context = "用户问尺码，我们推荐了XL码，用户说可以。"

        follow_up = dialogue_agent.generate_follow_up(sample_conversation, context)

        assert isinstance(follow_up, str)
        assert len(follow_up) > 0

    @pytest.mark.asyncio
    async def test_empty_conversation(self):
        conv = Conversation(session_id="empty", user_id="empty")

        response = await dialogue_agent.process(conv)

        assert response.success is True
