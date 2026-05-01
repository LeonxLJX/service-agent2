import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.vector_service import vector_service
from app.agents.knowledge_agent import KnowledgeItem
from loguru import logger


def init_knowledge_base():
    logger.info("Initializing knowledge base...")

    vector_service.init_index()
    logger.info(f"Vector index initialized")

    kb_path = os.path.join("data", "knowledge_base")
    os.makedirs(kb_path, exist_ok=True)

    faq_path = os.path.join(kb_path, "faq.json")
    if os.path.exists(faq_path):
        with open(faq_path, 'r', encoding='utf-8') as f:
            faq_data = json.load(f)
            logger.info(f"Loaded {len(faq_data)} FAQ items")

    product_path = os.path.join(kb_path, "product_knowledge.json")
    if os.path.exists(product_path):
        with open(product_path, 'r', encoding='utf-8') as f:
            product_data = json.load(f)
            logger.info(f"Loaded {len(product_data)} product knowledge items")

    sample_items = [
        KnowledgeItem(
            kb_id="faq",
            item_id="sample_001",
            category="sample",
            question="请问这件衣服有货吗",
            answer="您好，这款衣服目前有货，可以正常下单。"
        ),
        KnowledgeItem(
            kb_id="faq",
            item_id="sample_002",
            category="sample",
            question="退换货政策是什么",
            answer="您好，我们支持7天无理由退换货（特殊商品除外）。"
        ),
    ]

    for item in sample_items:
        vector = vector_service.text_to_vector(item.question + " " + item.answer)
        vector_service.add_vector(vector, item.model_dump())

    logger.info(f"Added {len(sample_items)} sample knowledge items")
    logger.info("Knowledge base initialization completed!")


if __name__ == "__main__":
    init_knowledge_base()
