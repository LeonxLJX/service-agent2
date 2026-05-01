from app.agents.base import BaseAgent
from app.models.conversation import (
    Conversation, AgentResponse, KnowledgeItem, KnowledgeRetrievalResult, IntentType
)
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service
from app.config import settings
from loguru import logger
from typing import List
import json
import os


class KnowledgeAgent(BaseAgent):
    def __init__(self):
        super().__init__("KnowledgeRetrievalAgent")
        self.knowledge_base: List[KnowledgeItem] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        kb_path = os.path.join("data", "knowledge_base")
        faq_path = os.path.join(kb_path, "faq.json")
        product_path = os.path.join(kb_path, "product_knowledge.json")

        if os.path.exists(faq_path):
            try:
                with open(faq_path, 'r', encoding='utf-8') as f:
                    faq_data = json.load(f)
                    for item in faq_data:
                        self.knowledge_base.append(KnowledgeItem(
                            kb_id="faq",
                            item_id=item.get("id", ""),
                            category=item.get("category", "faq"),
                            question=item.get("question", ""),
                            answer=item.get("answer", ""),
                            metadata=item.get("metadata", {})
                        ))
                logger.info(f"Loaded {len(faq_data)} FAQ items")
            except Exception as e:
                logger.error(f"Failed to load FAQ: {e}")

        if os.path.exists(product_path):
            try:
                with open(product_path, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
                    for item in product_data:
                        self.knowledge_base.append(KnowledgeItem(
                            kb_id="product",
                            item_id=item.get("id", ""),
                            category=item.get("category", "product"),
                            question=item.get("question", ""),
                            answer=item.get("answer", ""),
                            metadata=item.get("metadata", {})
                        ))
                logger.info(f"Loaded {len(product_data)} product knowledge items")
            except Exception as e:
                logger.error(f"Failed to load product knowledge: {e}")

        for item in self.knowledge_base:
            vector = vector_service.text_to_vector(item.question + " " + item.answer)
            vector_service.add_vector(vector, item.model_dump())

    async def process(self, conversation: Conversation, **kwargs) -> AgentResponse:
        user_message = conversation.history[-1].content if conversation.history else ""
        intent = conversation.context.get("current_intent", "unknown")
        entities = conversation.context.get("entities", {})

        retrieval_result = self.retrieve_knowledge(user_message, intent, entities)

        if not retrieval_result.items:
            return self._create_response(
                content="抱歉，我在知识库中没有找到相关信息，建议您联系人工客服获取帮助。",
                metadata={"retrieval_result": retrieval_result.model_dump()}
            )

        answer = self._format_knowledge_response(retrieval_result, intent)

        return self._create_response(
            content=answer,
            metadata={"retrieval_result": retrieval_result.model_dump()}
        )

    def retrieve_knowledge(
        self,
        query: str,
        intent: str,
        entities: dict
    ) -> KnowledgeRetrievalResult:
        query_vector = vector_service.text_to_vector(query)
        search_results = vector_service.search(query_vector, top_k=settings.retrieval_top_k)

        items = []
        scores = []

        for idx, distance, metadata in search_results:
            similarity = 1.0 / (1.0 + distance)
            if similarity >= settings.similarity_threshold:
                items.append(KnowledgeItem(**metadata))
                scores.append(similarity)

        if not items and entities.get("product"):
            product_query = entities["product"]
            product_vector = vector_service.text_to_vector(product_query)
            product_results = vector_service.search(product_vector, top_k=3)
            for idx, distance, metadata in product_results:
                similarity = 1.0 / (1.0 + distance)
                if similarity >= settings.similarity_threshold * 0.8:
                    items.append(KnowledgeItem(**metadata))
                    scores.append(similarity)

        return KnowledgeRetrievalResult(items=items, scores=scores)

    def _format_knowledge_response(
        self,
        retrieval_result: KnowledgeRetrievalResult,
        intent: str
    ) -> str:
        if not retrieval_result.items:
            return ""

        top_item = retrieval_result.items[0]
        response = top_item.answer

        if len(retrieval_result.items) > 1:
            response += "\n\n如果您想了解更多信息，请告诉我：\n"
            for i, item in enumerate(retrieval_result.items[1:3], 1):
                response += f"{i}. {item.question}\n"

        return response


knowledge_agent = KnowledgeAgent()
