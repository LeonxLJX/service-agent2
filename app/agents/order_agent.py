from app.agents.base import BaseAgent
from app.models.conversation import (
    Conversation, AgentResponse, OrderInfo, LogisticsInfo, AfterSalesInfo, IntentType
)
from app.config import settings
from loguru import logger
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random


class OrderAgent(BaseAgent):
    def __init__(self):
        super().__init__("OrderProcessingAgent")
        self.mock_orders = self._init_mock_orders()
        self.mock_logistics = self._init_mock_logistics()

    def _init_mock_orders(self) -> Dict[str, OrderInfo]:
        orders = {}
        base_date = datetime.now()

        for i in range(1, 6):
            order_id = f"TK{100000 + i}"
            status_options = ["pending", "paid", "shipped", "delivered", "completed"]
            status = status_options[random.randint(0, len(status_options) - 1)]

            created_days_ago = random.randint(1, 30)
            created_date = base_date - timedelta(days=created_days_ago)

            order = OrderInfo(
                order_id=order_id,
                status=status,
                items=[{
                    "product_id": f"P{1000 + i}",
                    "name": f"商品{i}",
                    "quantity": random.randint(1, 3),
                    "price": round(random.uniform(50, 500), 2)
                }],
                total_amount=round(random.uniform(100, 1500), 2),
                shipping={
                    "company": random.choice(["顺丰速运", "中通快递", "圆通速递", "韵达快递"]),
                    "tracking_no": f"SF{random.randint(1000000000, 9999999999)}",
                    "status": "运输中" if status == "shipped" else "已签收" if status == "delivered" else "待发货",
                    "estimated_delivery": (base_date + timedelta(days=3)).strftime("%Y-%m-%d") if status == "shipped" else None
                },
                created_at=created_date.strftime("%Y-%m-%d %H:%M:%S")
            )
            orders[order_id] = order

        return orders

    def _init_mock_logistics(self) -> Dict[str, LogisticsInfo]:
        logistics = {}
        base_date = datetime.now()

        for order_id, order in self.mock_orders.items():
            if order.shipping:
                tracking_no = order.shipping["tracking_no"]
                traces = [
                    {"time": (base_date - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), "status": "商品已从仓库发出"},
                    {"time": (base_date - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), "status": "商品到达中转站"},
                    {"time": base_date.strftime("%Y-%m-%d %H:%M"), "status": "商品运输中"},
                ]

                logistics[tracking_no] = LogisticsInfo(
                    order_id=order_id,
                    company=order.shipping["company"],
                    tracking_no=tracking_no,
                    status=order.shipping["status"],
                    traces=traces,
                    estimated_delivery=order.shipping.get("estimated_delivery")
                )

        return logistics

    async def process(self, conversation: Conversation, **kwargs) -> AgentResponse:
        user_message = conversation.history[-1].content if conversation.history else ""
        intent = conversation.context.get("current_intent", "unknown")
        entities = conversation.context.get("entities", {})

        order_id = entities.get("order_id")
        if not order_id:
            order_id = self._extract_order_id(user_message)

        if intent == IntentType.ORDER_STATUS.value:
            return await self._query_order_status(order_id, conversation)
        elif intent in [IntentType.LOGISTICS_QUERY.value, IntentType.DELIVERY_TIME.value]:
            return await self._query_logistics(order_id, conversation)
        elif intent == IntentType.RETURN_REQUEST.value:
            return await self._handle_return_request(order_id, user_message, conversation)
        elif intent == IntentType.EXCHANGE_REQUEST.value:
            return await self._handle_exchange_request(order_id, user_message, conversation)
        elif intent in [IntentType.REFUND_STATUS.value, IntentType.REFUND_APPLICATION.value]:
            return await self._handle_refund(order_id, user_message, conversation, intent)

        return self._create_response(
            content="抱歉，我没有理解您的订单相关问题，请提供更多信息。"
        )

    def _extract_order_id(self, message: str) -> Optional[str]:
        import re
        patterns = [
            r'[A-Z]{2}\d{10,}',
            r'订单[号]?[：:]?\s*([A-Z0-9]+)',
            r'([A-Z0-9]{10,})'
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                potential_id = match.group(1) if match.lastindex else match.group(0)
                for order_id in self.mock_orders:
                    if order_id.upper() == potential_id.upper():
                        return order_id

        return None

    async def _query_order_status(self, order_id: Optional[str], conversation: Conversation) -> AgentResponse:
        if not order_id:
            return self._create_response(
                content="好的，我来帮您查询订单状态。请提供您的订单号（以TK开头的10位号码），或者告诉我您的大致下单时间，我来帮您查找。",
                metadata={"need_order_id": True}
            )

        order = self.mock_orders.get(order_id)
        if not order:
            return self._create_response(
                content=f"抱歉，系统未找到订单号 {order_id} 的信息。请确认订单号是否正确，或联系人工客服查询。"
            )

        status_map = {
            "pending": "待支付",
            "paid": "已支付，待发货",
            "shipped": "已发货，运输中",
            "delivered": "已签收",
            "completed": "已完成"
        }

        response = f"您的订单 {order_id} 状态如下：\n"
        response += f"- 订单状态：{status_map.get(order.status, order.status)}\n"
        response += f"- 下单时间：{order.created_at}\n"
        response += f"- 订单金额：¥{order.total_amount:.2f}\n"

        if order.items:
            response += f"- 商品信息：{order.items[0]['name']} x{order.items[0]['quantity']}\n"

        return self._create_response(
            content=response,
            metadata={"order": order.model_dump()}
        )

    async def _query_logistics(self, order_id: Optional[str], conversation: Conversation) -> AgentResponse:
        if not order_id:
            return self._create_response(
                content="请提供您的订单号，我来帮您查询物流信息。"
            )

        order = self.mock_orders.get(order_id)
        if not order or not order.shipping:
            return self._create_response(
                content=f"抱歉，订单 {order_id} 没有物流信息或尚未发货。"
            )

        shipping = order.shipping
        response = f"您的订单物流信息如下：\n"
        response += f"- 物流公司：{shipping['company']}\n"
        response += f"- 运单号：{shipping['tracking_no']}\n"
        response += f"- 当前状态：{shipping['status']}\n"

        if shipping.get("estimated_delivery"):
            response += f"- 预计送达：{shipping['estimated_delivery']}\n"

        tracking_no = shipping["tracking_no"]
        logistics = self.mock_logistics.get(tracking_no)
        if logistics and logistics.traces:
            response += "\n物流轨迹：\n"
            for trace in logistics.traces[-3:]:
                response += f"- {trace['time']}：{trace['status']}\n"

        return self._create_response(
            content=response,
            metadata={"logistics": logistics.model_dump() if logistics else None}
        )

    async def _handle_return_request(self, order_id: Optional[str], reason: str, conversation: Conversation) -> AgentResponse:
        if not order_id:
            return self._create_response(
                content="好的，我来帮您申请退货。请提供您的订单号，并描述一下退货原因。"
            )

        order = self.mock_orders.get(order_id)
        if not order:
            return self._create_response(content=f"未找到订单 {order_id}")

        if order.status not in ["shipped", "delivered"]:
            return self._create_response(
                content=f"抱歉，订单 {order_id} 当前状态不支持退货（状态：{order.status}）。仅已发货和已签收的订单可以申请退货。"
            )

        ticket_id = f"RS{10000 + random.randint(1, 9999)}"
        response = f"退货申请已提交！\n"
        response += f"- 工单号：{ticket_id}\n"
        response += f"- 订单号：{order_id}\n"
        response += f"- 退货原因：{reason or '用户主动退货'}\n"
        response += f"- 预计处理时间：1-3个工作日\n"
        response += f"我们的客服人员将尽快与您联系，请保持电话畅通。"

        return self._create_response(
            content=response,
            metadata={"ticket_id": ticket_id, "type": "return"}
        )

    async def _handle_exchange_request(self, order_id: Optional[str], reason: str, conversation: Conversation) -> AgentResponse:
        if not order_id:
            return self._create_response(
                content="好的，我来帮您申请换货。请提供您的订单号，并说明想要换成的尺码或颜色。"
            )

        order = self.mock_orders.get(order_id)
        if not order:
            return self._create_response(content=f"未找到订单 {order_id}")

        ticket_id = f"EX{10000 + random.randint(1, 9999)}"
        response = f"换货申请已提交！\n"
        response += f"- 工单号：{ticket_id}\n"
        response += f"- 订单号：{order_id}\n"
        response += f"- 换货原因：{reason or '用户主动换货'}\n"
        response += f"- 预计处理时间：1-3个工作日\n"
        response += f"我们的客服人员将尽快与您联系，请保持电话畅通。"

        return self._create_response(
            content=response,
            metadata={"ticket_id": ticket_id, "type": "exchange"}
        )

    async def _handle_refund(self, order_id: Optional[str], reason: str, conversation: Conversation, intent: str) -> AgentResponse:
        if not order_id:
            return self._create_response(
                content="请提供您的订单号，我来帮您查询或申请退款。"
            )

        order = self.mock_orders.get(order_id)
        if not order:
            return self._create_response(content=f"未找到订单 {order_id}")

        if intent == IntentType.REFUND_STATUS.value:
            if order.status == "completed":
                refund_amount = order.total_amount
                response = f"您的订单 {order_id} 退款信息如下：\n"
                response += f"- 退款金额：¥{refund_amount:.2f}\n"
                response += f"- 退款状态：已退款\n"
                response += f"- 退款方式：原路退回\n"
                response += f"- 预计到账时间：1-7个工作日\n"
            else:
                response = f"您的订单 {order_id} 目前没有退款记录。\n"
                response += f"- 订单状态：{order.status}\n"
                response += f"- 订单金额：¥{order.total_amount:.2f}\n"

            return self._create_response(content=response)

        if order.status not in ["pending", "paid"]:
            return self._create_response(
                content=f"抱歉，订单 {order_id} 当前状态（{order.status}）不支持退款申请。"
            )

        ticket_id = f"RF{10000 + random.randint(1, 9999)}"
        response = f"退款申请已提交！\n"
        response += f"- 工单号：{ticket_id}\n"
        response += f"- 订单号：{order_id}\n"
        response += f"- 退款金额：¥{order.total_amount:.2f}\n"
        response += f"- 退款原因：{reason or '用户主动退款'}\n"
        response += f"- 预计处理时间：1-3个工作日\n"
        response += f"- 退款方式：原路退回\n"

        return self._create_response(
            content=response,
            metadata={"ticket_id": ticket_id, "type": "refund", "amount": order.total_amount}
        )


order_agent = OrderAgent()
