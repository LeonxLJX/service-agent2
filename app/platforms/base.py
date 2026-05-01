from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import httpx
import asyncio
from loguru import logger


class Platform(Enum):
    TAOBAO = "taobao"
    PINDUODUO = "pinduoduo"
    DOUYIN = "douyin"
    WEIXIN = "weixin"


@dataclass
class OrderInfo:
    order_id: str
    platform: str
    status: str
    buyer_nick: str
    created_at: str
    total_amount: float
    items: List[Dict]
    shipping_address: Dict
    logistics_info: Optional[Dict] = None


@dataclass
class LogisticsInfo:
    company: str
    tracking_no: str
    status: str
    estimated_delivery: Optional[str] = None
    traces: List[Dict] = None


@dataclass
class RefundInfo:
    refund_id: str
    order_id: str
    reason: str
    amount: float
    status: str
    created_at: str


class BasePlatformAdapter(ABC):
    def __init__(self, app_key: str, app_secret: str, session: str = ""):
        self.app_key = app_key
        self.app_secret = app_secret
        self.session = session
        self.base_url = ""
        self.timeout = 10.0

    @abstractmethod
    async def get_order_detail(self, order_id: str) -> Optional[OrderInfo]:
        pass

    @abstractmethod
    async def get_logistics_info(self, order_id: str) -> Optional[LogisticsInfo]:
        pass

    @abstractmethod
    async def get_refund_list(self, order_id: str) -> List[RefundInfo]:
        pass

    @abstractmethod
    async def create_refund(self, order_id: str, reason: str, amount: float) -> Optional[RefundInfo]:
        pass

    @abstractmethod
    async def get_item_info(self, item_id: str) -> Optional[Dict]:
        pass

    async def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}{endpoint}"
                if method.upper() == "GET":
                    response = await client.get(url, params=params)
                else:
                    response = await client.post(url, json=data, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"Request timeout: {endpoint}")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"success": False, "error": str(e)}


class TaobaoAdapter(BasePlatformAdapter):
    def __init__(self, app_key: str, app_secret: str, session: str = ""):
        super().__init__(app_key, app_secret, session)
        self.base_url = "https://gw.api.taobao.com/router/rest"
        self.app_key = app_key

    async def get_order_detail(self, order_id: str) -> Optional[OrderInfo]:
        params = {
            "method": "taobao.trade.get",
            "app_key": self.app_key,
            "session": self.session,
            "order_id": order_id,
            "fields": "tid,status,buyer_nick,created,total_fee,orders,receiver_address"
        }
        result = await self._make_request("GET", "", params=params)
        if result.get("trade_get_response", {}).get("trade"):
            trade = result["trade_get_response"]["trade"]
            return OrderInfo(
                order_id=str(trade["tid"]),
                platform="taobao",
                status=self._map_order_status(trade["status"]),
                buyer_nick=trade.get("buyer_nick", ""),
                created_at=trade.get("created", ""),
                total_amount=float(trade.get("total_fee", 0)),
                items=trade.get("orders", []),
                shipping_address=trade.get("receiver_address", {})
            )
        return None

    async def get_logistics_info(self, order_id: str) -> Optional[LogisticsInfo]:
        params = {
            "method": "taobao.logistics.trace.get",
            "app_key": self.app_key,
            "session": self.session,
            "tid": order_id,
            "seller_nick": "seller"
        }
        result = await self._make_request("GET", "", params=params)
        if result.get("logistics_trace_get_response"):
            trace = result["logistics_trace_get_response"]
            return LogisticsInfo(
                company=trace.get("company_name", ""),
                tracking_no=trace.get("out_sid", ""),
                status=trace.get("status", ""),
                traces=trace.get("traces", [])
            )
        return None

    async def get_refund_list(self, order_id: str) -> List[RefundInfo]:
        params = {
            "method": "taobao.refunds.get",
            "app_key": self.app_key,
            "session": self.session,
            "fields": "refund_id,oid,status,created,refund_fee,reason"
        }
        result = await self._make_request("GET", "", params=params)
        refunds = []
        if result.get("refunds_get_response"):
            for item in result["refunds_get_response"].get("refunds", []):
                refunds.append(RefundInfo(
                    refund_id=str(item["refund_id"]),
                    order_id=str(item["oid"]),
                    reason=item.get("reason", ""),
                    amount=float(item.get("refund_fee", 0)),
                    status=self._map_refund_status(item.get("status", "")),
                    created_at=item.get("created", "")
                ))
        return refunds

    async def create_refund(self, order_id: str, reason: str, amount: float) -> Optional[RefundInfo]:
        params = {
            "method": "taobao.refund.create",
            "app_key": self.app_key,
            "session": self.session,
            "tid": order_id,
            "reason": reason,
            "refund_fee": str(amount)
        }
        result = await self._make_request("GET", "", params=params)
        if result.get("refund_create_response", {}).get("refund"):
            refund = result["refund_create_response"]["refund"]
            return RefundInfo(
                refund_id=str(refund["refund_id"]),
                order_id=order_id,
                reason=reason,
                amount=amount,
                status="WAIT_SELLER_AGREE",
                created_at=refund.get("created", "")
            )
        return None

    async def get_item_info(self, item_id: str) -> Optional[Dict]:
        params = {
            "method": "taobao.item.get",
            "app_key": self.app_key,
            "session": self.session,
            "num_iid": item_id,
            "fields": "num_iid,title,price,stock,pic_url,props,item_imgs"
        }
        result = await self._make_request("GET", "", params=params)
        if result.get("item_get_response", {}).get("item"):
            return result["item_get_response"]["item"]
        return None

    def _map_order_status(self, status: str) -> str:
        status_map = {
            "WAIT_BUYER_PAY": "待付款",
            "WAIT_SELLER_SEND_GOODS": "待发货",
            "WAIT_BUYER_CONFIRM_GOODS": "已发货",
            "TRADE_CLOSED": "交易关闭",
            "TRADE_FINISHED": "交易完成"
        }
        return status_map.get(status, status)

    def _map_refund_status(self, status: str) -> str:
        status_map = {
            "WAIT_SELLER_AGREE": "待商家同意",
            "WAIT_BUYER_RETURN_GOODS": "待买家退货",
            "WAIT_SELLER_CONFIRM_GOODS": "退货已退货",
            "REFUND_SUCCESS": "退款成功",
            "REFUND_CLOSED": "退款关闭"
        }
        return status_map.get(status, status)


class PinduoduoAdapter(BasePlatformAdapter):
    def __init__(self, app_key: str, app_secret: str, session: str = ""):
        super().__init__(app_key, app_secret, session)
        self.base_url = "https://gw-api.pinduoduo.com/api/router"

    async def get_order_detail(self, order_id: str) -> Optional[OrderInfo]:
        data = {
            "api_type": 1,
            "api_name": "pdd.order.number.get",
            "order_number": order_id,
            "session_key": self.session
        }
        result = await self._make_request("POST", "", data=data)
        if result.get("order_number_get_response"):
            order = result["order_number_get_response"]
            return OrderInfo(
                order_id=order.get("order_number", ""),
                platform="pinduoduo",
                status=self._map_order_status(order.get("order_status", "")),
                buyer_nick=order.get("buyer_name", ""),
                created_at=order.get("create_time", ""),
                total_amount=float(order.get("order_amount", 0)),
                items=order.get("goods_list", []),
                shipping_address=order.get("address", {})
            )
        return None

    async def get_logistics_info(self, order_id: str) -> Optional[LogisticsInfo]:
        data = {
            "api_type": 1,
            "api_name": "pdd.logistics.trace.get",
            "order_number": order_id,
            "session_key": self.session
        }
        result = await self._make_request("POST", "", data=data)
        if result.get("logistics_trace_get_response"):
            trace = result["logistics_trace_get_response"]
            return LogisticsInfo(
                company=trace.get("logistics_name", ""),
                tracking_no=trace.get("tracking_number", ""),
                status=trace.get("status", ""),
                traces=trace.get("trace_list", [])
            )
        return None

    async def get_refund_list(self, order_id: str) -> List[RefundInfo]:
        data = {
            "api_type": 1,
            "api_name": "pdd.refund.list.get",
            "order_number": order_id,
            "session_key": self.session
        }
        result = await self._make_request("POST", "", data=data)
        refunds = []
        if result.get("refund_list_get_response"):
            for item in result["refund_list_get_response"].get("refund_list", []):
                refunds.append(RefundInfo(
                    refund_id=str(item["refund_id"]),
                    order_id=order_id,
                    reason=item.get("reason", ""),
                    amount=float(item.get("refund_amount", 0)),
                    status=self._map_refund_status(item.get("status", "")),
                    created_at=item.get("create_time", "")
                ))
        return refunds

    async def create_refund(self, order_id: str, reason: str, amount: float) -> Optional[RefundInfo]:
        data = {
            "api_type": 1,
            "api_name": "pdd.refund.create",
            "order_number": order_id,
            "reason": reason,
            "refund_amount": amount,
            "session_key": self.session
        }
        result = await self._make_request("POST", "", data=data)
        if result.get("refund_create_response"):
            refund = result["refund_create_response"]
            return RefundInfo(
                refund_id=str(refund["refund_id"]),
                order_id=order_id,
                reason=reason,
                amount=amount,
                status="WAIT_SELLER_AGREE",
                created_at=refund.get("create_time", "")
            )
        return None

    async def get_item_info(self, item_id: str) -> Optional[Dict]:
        data = {
            "api_type": 1,
            "api_name": "pdd.goods.info.get",
            "goods_id": item_id,
            "session_key": self.session
        }
        result = await self._make_request("POST", "", data=data)
        if result.get("goods_info_get_response", {}).get("goods_info"):
            return result["goods_info_get_response"]["goods_info"]
        return None

    def _map_order_status(self, status: str) -> str:
        status_map = {
            "1": "待付款",
            "2": "待发货",
            "3": "已发货",
            "4": "已签收",
            "5": "拼团中",
            "6": "交易完成",
            "7": "取消订单",
            "8": "退款中",
            "9": "退款成功"
        }
        return status_map.get(status, status)

    def _map_refund_status(self, status: str) -> str:
        status_map = {
            "1": "待处理",
            "2": "商家同意",
            "3": "商家拒绝",
            "4": "退款成功",
            "5": "退款关闭"
        }
        return status_map.get(status, status)


class DouyinAdapter(BasePlatformAdapter):
    def __init__(self, app_key: str, app_secret: str, session: str = ""):
        super().__init__(app_key, app_secret, session)
        self.base_url = "https://open.douyin.com"

    async def get_order_detail(self, order_id: str) -> Optional[OrderInfo]:
        params = {
            "access_token": self.session,
            "order_id": order_id
        }
        result = await self._make_request("GET", "/order/detail", params=params)
        if result.get("data", {}).get("order"):
            order = result["data"]["order"]
            return OrderInfo(
                order_id=order.get("order_id", ""),
                platform="douyin",
                status=self._map_order_status(order.get("status", "")),
                buyer_nick=order.get("user_info", {}).get("nickname", ""),
                created_at=order.get("create_time", ""),
                total_amount=float(order.get("total_amount", 0)),
                items=order.get("product_info", []),
                shipping_address=order.get("address_info", {})
            )
        return None

    async def get_logistics_info(self, order_id: str) -> Optional[LogisticsInfo]:
        params = {
            "access_token": self.session,
            "order_id": order_id
        }
        result = await self._make_request("GET", "/order/logistics", params=params)
        if result.get("data"):
            trace = result["data"]
            return LogisticsInfo(
                company=trace.get("company_name", ""),
                tracking_no=trace.get("tracking_no", ""),
                status=trace.get("status", ""),
                estimated_delivery=trace.get("estimated_delivery_time", ""),
                traces=trace.get("trace_list", [])
            )
        return None

    async def get_refund_list(self, order_id: str) -> List[RefundInfo]:
        params = {
            "access_token": self.session,
            "order_id": order_id
        }
        result = await self._make_request("GET", "/order/refund/list", params=params)
        refunds = []
        if result.get("data", {}).get("refund_list"):
            for item in result["data"]["refund_list"]:
                refunds.append(RefundInfo(
                    refund_id=str(item["refund_id"]),
                    order_id=order_id,
                    reason=item.get("reason", ""),
                    amount=float(item.get("refund_amount", 0)),
                    status=self._map_refund_status(item.get("status", "")),
                    created_at=item.get("create_time", "")
                ))
        return refunds

    async def create_refund(self, order_id: str, reason: str, amount: float) -> Optional[RefundInfo]:
        data = {
            "access_token": self.session,
            "order_id": order_id,
            "reason": reason,
            "refund_amount": amount
        }
        result = await self._make_request("POST", "/order/refund/apply", data=data)
        if result.get("data", {}).get("refund_id"):
            refund = result["data"]
            return RefundInfo(
                refund_id=str(refund["refund_id"]),
                order_id=order_id,
                reason=reason,
                amount=amount,
                status="PENDING",
                created_at=refund.get("create_time", "")
            )
        return None

    async def get_item_info(self, item_id: str) -> Optional[Dict]:
        params = {
            "access_token": self.session,
            "product_id": item_id
        }
        result = await self._make_request("GET", "/product/detail", params=params)
        if result.get("data", {}).get("product"):
            return result["data"]["product"]
        return None

    def _map_order_status(self, status: str) -> str:
        status_map = {
            "10": "待付款",
            "20": "待发货",
            "30": "已发货",
            "40": "已签收",
            "100": "已完成",
            "110": "已取消",
            "120": "退款中",
            "130": "退款成功"
        }
        return status_map.get(status, status)

    def _map_refund_status(self, status: str) -> str:
        status_map = {
            "10": "待处理",
            "20": "商家处理中",
            "30": "退款成功",
            "40": "退款失败",
            "50": "已撤销"
        }
        return status_map.get(status, status)


class PlatformAdapterFactory:
    _adapters = {
        Platform.TAOBAO: TaobaoAdapter,
        Platform.PINDUODUO: PinduoduoAdapter,
        Platform.DOUYIN: DouyinAdapter,
    }

    @classmethod
    def get_adapter(cls, platform: Platform, app_key: str = "", app_secret: str = "", session: str = "") -> BasePlatformAdapter:
        adapter_class = cls._adapters.get(platform)
        if adapter_class:
            return adapter_class(app_key, app_secret, session)
        raise ValueError(f"Unsupported platform: {platform}")

    @classmethod
    def register_adapter(cls, platform: Platform, adapter_class: type):
        cls._adapters[platform] = adapter_class
