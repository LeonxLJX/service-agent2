from app.agents.base import BaseAgent
from app.models.conversation import (
    Conversation, AgentResponse, IntentType
)
from app.services.llm_service import llm_service
from loguru import logger


class DialogueAgent(BaseAgent):
    def __init__(self):
        super().__init__("MultiTurnDialogueAgent")
        self.system_prompt = """你是一个专业的电商客服助手，名字叫小e。你需要：
1. 基于对话上下文，理解用户的真实需求
2. 回答用户的问题时，要专业、热情、有耐心
3. 如果知识库提供了参考信息，优先基于参考信息回答
4. 如果知识库没有相关信息，使用你的电商知识来回答
5. 保持回复简洁明了，每条回复不超过100字
6. 如果遇到无法解决的问题，引导用户联系人工客服
7. 不要编造商品信息或订单信息，如果有不确定的信息，请明确说明
"""

    async def process(self, conversation: Conversation, **kwargs) -> AgentResponse:
        knowledge_content = kwargs.get("knowledge_content", "")
        knowledge_context = kwargs.get("knowledge_context", "")

        messages = self._build_messages(conversation, knowledge_content, knowledge_context)

        response_text = llm_service.chat(messages)

        if not response_text:
            return self._create_response(
                content="抱歉，我现在无法回答您的问题，请稍后再试。",
                need_human_intervention=True
            )

        return self._create_response(
            content=response_text,
            metadata={"agent": self.name}
        )

    def _build_messages(
        self,
        conversation: Conversation,
        knowledge_content: str,
        knowledge_context: str
    ) -> list:
        messages = [{"role": "system", "content": self.system_prompt}]

        if knowledge_context:
            context_addition = f"\n\n参考信息：\n{knowledge_context}"
            messages[0]["content"] += context_addition

        history_text = conversation.get_history_text(max_turns=settings.max_history_turns)
        if history_text:
            history_lines = history_text.split("\n")
            for line in history_lines:
                if line.startswith("user:"):
                    messages.append({
                        "role": "user",
                        "content": line[5:].strip()
                    })
                elif line.startswith("assistant:"):
                    messages.append({
                        "role": "assistant",
                        "content": line[10:].strip()
                    })

        if knowledge_content:
            knowledge_prompt = f"\n\n请基于以下参考信息回答用户问题：\n{knowledge_content}\n\n用户问题：{conversation.history[-1].content if conversation.history else ''}"
            if messages[-1]["role"] == "user":
                messages[-1]["content"] += knowledge_prompt
            else:
                messages.append({
                    "role": "user",
                    "content": conversation.history[-1].content + knowledge_prompt
                })
        else:
            if messages[-1]["role"] != "user" and conversation.history:
                messages.append({
                    "role": "user",
                    "content": conversation.history[-1].content
                })

        return messages

    def generate_follow_up(self, conversation: Conversation, context: str) -> str:
        prompt = f"""基于以下对话上下文和参考信息，生成一个合适的跟进问题：

对话上下文：
{context}

请生成一个简短的跟进问题，帮助用户进一步咨询或确认信息。问题应该简洁、自然。
只输出问题本身，不要包含其他内容。"""

        follow_up = llm_service.generate(
            prompt,
            system_message="你是一个专业的客服助手，生成简短的跟进问题。",
            max_tokens=50
        )

        return follow_up if follow_up else ""

    def generate_reply(self, message: str, intent: str, knowledge_content: str = "", entities: dict = None) -> str:
        entities = entities or {}
        
        general_knowledge_prompts = [
            "什么是", "怎么", "如何", "为什么", "哪里", "什么时候", "谁", "多少", "好吗", "可以吗",
            "有用吗", "有效果吗", "步骤", "方法", "教程", "介绍", "说明", "解释", "道理",
            "原因", "区别", "不同", "哪个好", "怎么样", "如何做", "干嘛用的", "有什么用"
        ]
        
        is_general_question = any(kw in message for kw in general_knowledge_prompts) and intent in ["unknown", "闲聊", "greeting"]
        
        if is_general_question:
            prompt = f"""你是一个知识渊博的智能助手，名字叫小e。你的回答要像百度百科一样专业、全面、有帮助。

用户问题：{message}

请直接回答用户的问题：
1. 回答要专业、准确、有深度
2. 可以适当举例说明
3. 如果是操作类问题，给出清晰步骤
4. 回答长度适中（100-200字），信息量要丰富
5. 遇到不清楚的问题，坦诚说明并提供替代建议

请直接输出回答内容："""
        else:
            prompt = f"""你是一个专业的电商客服助手小e，现在需要回答用户的问题。

用户问题：{message}
识别意图：{intent}
提取实体：{entities}

参考信息：{knowledge_content if knowledge_content else '无'}

请基于以上信息，用自然友好的语言回答用户问题：
1. 如果有参考信息，优先使用参考信息
2. 回复要简洁明了，不要超过100字
3. 如果无法回答，引导用户联系人工客服
4. 保持专业和礼貌

请直接输出回复内容：
"""

        reply = llm_service.generate(
            prompt,
            system_message=self.system_prompt if not is_general_question else "你是一个知识渊博的智能助手，名叫小e。你的任务是专业、耐心地回答用户的各种问题，帮助用户解决问题。你的回答要像百度百科一样权威、全面、有帮助。",
            max_tokens=300 if is_general_question else 150
        )

        if not reply:
            reply = "抱歉，小e暂时无法回答这个问题，换个问题试试？或者联系人工客服获取帮助～"

        return reply.strip()


from app.config import settings
dialogue_agent = DialogueAgent()
