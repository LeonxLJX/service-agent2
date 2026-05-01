from app.agents.base import BaseAgent
from app.models.conversation import (
    Conversation, AgentResponse, IntentType, IntentRecognitionResult
)
from app.services.llm_service import llm_service
from app.services.performance_service import cache_service
from app.config import settings
from loguru import logger
import re
import time


class IntentAgent(BaseAgent):
    def __init__(self):
        super().__init__("IntentRecognitionAgent")
        self.intent_keywords = {
            IntentType.PRODUCT_INQUIRY: ["产品", "商品", "这件", "那个", "有没有", "卖", "款式", "型号"],
            IntentType.SIZE_GUIDE: ["尺码", "大小", "尺寸", "s码", "m码", "l码", "xl", "xxl", "加大", "小码"],
            IntentType.COLOR_SELECTION: ["颜色", "色", "白色", "黑色", "蓝色", "红色", "粉色", "绿色"],
            IntentType.PRICE_QUERY: ["价格", "多少钱", "价", "便宜", "贵", "折扣", "优惠", "活动"],
            IntentType.ORDER_STATUS: ["订单", "买了", "下单", "订单号", "还没到", "收到"],
            IntentType.LOGISTICS_QUERY: ["物流", "快递", "发货", "到哪了", "什么时候到", "运单", "追踪"],
            IntentType.DELIVERY_TIME: ["送达", "几天到", "多久", "时间", "发货时间"],
            IntentType.RETURN_REQUEST: ["退货", "不要了", "退掉", "取消订单"],
            IntentType.EXCHANGE_REQUEST: ["换货", "换", "换一个", "换成"],
            IntentType.COMPLAINT: ["投诉", "差评", "质量问题", "损坏", "破", "烂"],
            IntentType.REFUND_STATUS: ["退款", "退钱", "钱什么时候到", "退款进度"],
            IntentType.REFUND_APPLICATION: ["申请退款", "要退款", "退款"],
            IntentType.GREETING: ["你好", "您好", "在吗", "在不在", "hi", "hello", "嗨"],
        }
        self.greeting_intents = [IntentType.GREETING]
        self.order_intents = [IntentType.ORDER_STATUS, IntentType.LOGISTICS_QUERY, IntentType.DELIVERY_TIME]

        self.platform_keywords = {
            "taobao": ["淘宝", "天猫", "taobao", "tmall"],
            "pinduoduo": ["拼多多", "pdd", "多多"],
            "douyin": ["抖音", "douyin", "字节"],
            "weixin": ["微信", "weixin", "视频号"]
        }

    def recognize(self, message: str) -> dict:
        start_time = time.time()

        cache_key = f"intent:{hashlib.md5(message.encode()).hexdigest()}"
        cached_result = cache_service.get_intent(cache_key)
        if cached_result:
            logger.debug(f"Intent cache hit: {cache_key}")
            return cached_result

        intent_result = self._recognize_intent(message)

        result_dict = {
            "intent": intent_result.intent.value if intent_result.intent else "unknown",
            "sub_intent": intent_result.sub_intent,
            "confidence": intent_result.confidence,
            "entities": intent_result.entities,
            "suggestions": intent_result.suggestions,
            "platform": intent_result.entities.get("platform", "unknown"),
            "processing_time": time.time() - start_time
        }

        cache_service.set_intent(cache_key, result_dict, ttl=3600)

        return result_dict

    def _recognize_intent(self, message: str) -> IntentRecognitionResult:
        message_lower = message.lower()
        scores = {}

        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
            if score > 0:
                scores[intent] = score

        if not scores:
            return IntentRecognitionResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0
            )

        top_intent = max(scores.items(), key=lambda x: x[1])[0]
        confidence = min(0.95, 0.5 + scores[top_intent] * 0.15)

        entities = self._extract_entities(message, top_intent)

        suggestions = self._get_suggestions(top_intent)

        return IntentRecognitionResult(
            intent=top_intent,
            sub_intent=self._get_sub_intent(message, top_intent),
            confidence=confidence,
            entities=entities,
            suggestions=suggestions
        )

    def _extract_entities(self, message: str, intent: IntentType) -> dict:
        entities = {}

        order_id_patterns = [
            r'[A-Z]{2}\d{10,15}',
            r'\d{12,18}',
            r'TK\d{8,}',
            r'DD\d{8,}',
        ]
        for pattern in order_id_patterns:
            order_ids = re.findall(pattern, message, re.IGNORECASE)
            if order_ids:
                entities["order_id"] = order_ids[0]
                break

        size_pattern = r'(S|M|L|XL|XXL|\d{2})码?'
        sizes = re.findall(size_pattern, message, re.IGNORECASE)
        if sizes:
            entities["size"] = sizes[0].upper()

        color_keywords = {
            "白色": "white", "黑色": "black", "蓝色": "blue", "红色": "red",
            "粉色": "pink", "绿色": "green", "黄色": "yellow", "紫色": "purple", "灰色": "gray"
        }
        for color_name, color_en in color_keywords.items():
            if color_name in message:
                entities["color"] = color_name
                entities["color_en"] = color_en
                break

        price_pattern = r'(\d+(?:\.\d{1,2})?)(?:元|块|钱)?'
        prices = re.findall(price_pattern, message)
        if prices and any(kw in message for kw in ["价格", "多少钱", "便宜", "贵"]):
            entities["price"] = float(prices[0])

        item_id_pattern = r'(?:商品|产品|货号|编号)(?:\s*[：:])?\s*(\d+)'
        item_ids = re.findall(item_id_pattern, message)
        if item_ids:
            entities["item_id"] = item_ids[0]

        platform = self._extract_platform(message)
        if platform:
            entities["platform"] = platform

        refund_reason_keywords = ["尺码不合适", "颜色不喜欢", "质量问题", "发错货", "与描述不符", "不想买了", "后悔了"]
        for reason in refund_reason_keywords:
            if reason in message:
                entities["refund_reason"] = reason
                break

        return entities

    def _extract_platform(self, message: str) -> str:
        for platform, keywords in self.platform_keywords.items():
            for keyword in keywords:
                if keyword.lower() in message.lower():
                    return platform
        return "taobao"

    async def process(self, conversation: Conversation, **kwargs) -> AgentResponse:
        user_message = conversation.history[-1].content if conversation.history else ""

        intent_result = self._recognize_intent(user_message)

        if intent_result.confidence < settings.intent_confidence_threshold:
            return self._create_response(
                content="抱歉，我没有完全理解您的问题，能否重新描述一下？",
                metadata={"intent": intent_result.model_dump()}
            )

        conversation.current_intent = intent_result.intent.value
        conversation.context["entities"] = intent_result.entities

        response_content = self._generate_intent_response(intent_result)

        return self._create_response(
            content=response_content,
            metadata={"intent": intent_result.model_dump()}
        )

    def _get_sub_intent(self, message: str, intent: IntentType) -> str:
        if intent == IntentType.PRODUCT_INQUIRY:
            if any(kw in message for kw in ["有没有", "卖", "款"]):
                return "product_availability"
            return "product_info"

        if intent in [IntentType.ORDER_STATUS, IntentType.LOGISTICS_QUERY]:
            return intent.value

        return intent.value

    def _get_suggestions(self, intent: IntentType) -> list:
        suggestions_map = {
            IntentType.PRODUCT_INQUIRY: ["查看商品详情", "查看库存", "尺码推荐"],
            IntentType.SIZE_GUIDE: ["查看尺码表", "查看身材推荐"],
            IntentType.PRICE_QUERY: ["查看最新价格", "查看优惠活动"],
            IntentType.ORDER_STATUS: ["查看订单详情", "查看物流"],
            IntentType.LOGISTICS_QUERY: ["查看物流详情", "催促发货"],
            IntentType.RETURN_REQUEST: ["申请退货", "查看退货政策"],
            IntentType.GREETING: ["推荐热门商品", "查看最新活动"],
        }
        return suggestions_map.get(intent, ["继续咨询"])

    def _generate_intent_response(self, intent_result: IntentRecognitionResult) -> str:
        if intent_result.intent == IntentType.GREETING:
            return "您好！我是智能客服，很高兴为您服务。请问有什么可以帮您？"

        if intent_result.intent == IntentType.SIZE_GUIDE:
            return "好的，我来帮您查询一下尺码信息。请问您平时穿什么尺码呢？或者您可以告诉我您的身高体重，我帮您推荐合适的尺码。"

        if intent_result.intent == IntentType.PRICE_QUERY:
            return "好的，我来帮您查询这件商品的价格信息。请稍等..."

        if intent_result.intent == IntentType.ORDER_STATUS:
            return "好的，我来帮您查询一下订单状态。请提供您的订单号。"

        if intent_result.intent == IntentType.LOGISTICS_QUERY:
            return "好的，我来帮您查询物流信息。请提供一下您的订单号或运单号。"

        if intent_result.intent == IntentType.RETURN_REQUEST:
            return "好的，我来帮您处理退货申请。请问是什么原因要退货呢？"

        if intent_result.intent == IntentType.REFUND_STATUS:
            return "好的，我来帮您查询一下退款进度。请提供您的订单号。"

        return ""


import hashlib
intent_agent = IntentAgent()
