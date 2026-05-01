from typing import Optional, Dict, List
import time
from loguru import logger
from app.platforms import Platform, PlatformAdapterFactory, OrderInfo, LogisticsInfo, RefundInfo
from app.services.performance_service import (
    cache_service,
    cached,
    token_optimizer,
    response_time_optimizer
)


class OrderService:
    def __init__(self):
        self.platform_adapters: Dict[Platform, any] = {}

    def register_platform(self, platform: Platform, adapter):
        self.platform_adapters[platform] = adapter
        logger.info(f"Registered platform adapter: {platform.value}")

    @cached(cache_type="order", ttl=60)
    async def get_order_detail(self, order_id: str, platform: str = "taobao") -> Optional[OrderInfo]:
        start_time = time.time()
        try:
            platform_enum = Platform(platform)
            adapter = self.platform_adapters.get(platform_enum)
            if not adapter:
                logger.warning(f"No adapter for platform: {platform}")
                return self._get_mock_order(order_id, platform)

            order_info = await adapter.get_order_detail(order_id)
            duration = time.time() - start_time
            response_time_optimizer.check_sla("order", duration)
            return order_info
        except Exception as e:
            logger.error(f"Error getting order detail: {e}")
            return self._get_mock_order(order_id, platform)

    @cached(cache_type="logistics", ttl=300)
    async def get_logistics_info(self, order_id: str, platform: str = "taobao") -> Optional[LogisticsInfo]:
        start_time = time.time()
        try:
            platform_enum = Platform(platform)
            adapter = self.platform_adapters.get(platform_enum)
            if not adapter:
                return self._get_mock_logistics(order_id)

            logistics_info = await adapter.get_logistics_info(order_id)
            duration = time.time() - start_time
            response_time_optimizer.check_sla("logistics", duration)
            return logistics_info
        except Exception as e:
            logger.error(f"Error getting logistics: {e}")
            return self._get_mock_logistics(order_id)

    async def get_order_with_logistics(self, order_id: str, platform: str = "taobao") -> Dict:
        start_time = time.time()

        order_task = self.get_order_detail(order_id, platform)
        logistics_task = self.get_logistics_info(order_id, platform)

        order_info, logistics_info = await response_time_optimizer.parallel_process(
            order_task, logistics_task
        )

        result = {
            "order": order_info,
            "logistics": logistics_info,
            "query_time": time.time() - start_time
        }

        return result

    def _get_mock_order(self, order_id: str, platform: str) -> OrderInfo:
        return OrderInfo(
            order_id=order_id,
            platform=platform,
            status="已发货",
            buyer_nick="客户***",
            created_at="2024-01-01 10:00:00",
            total_amount=299.00,
            items=[{"name": "商品A", "num": 1, "price": 299.00}],
            shipping_address={"name": "张三", "phone": "138****8888", "address": "北京市朝阳区xxx"}
        )

    def _get_mock_logistics(self, order_id: str) -> LogisticsInfo:
        return LogisticsInfo(
            company="顺丰速运",
            tracking_no="SF1234567890",
            status="运输中",
            estimated_delivery="2024-01-05",
            traces=[
                {"time": "2024-01-03 14:30", "status": "商品已从仓库发出"},
                {"time": "2024-01-03 18:00", "status": "商品到达北京中转站"},
                {"time": "2024-01-04 09:30", "status": "商品运输中"}
            ]
        )


class RefundService:
    def __init__(self):
        self.platform_adapters: Dict[Platform, any] = {}

    def register_platform(self, platform: Platform, adapter):
        self.platform_adapters[platform] = adapter

    async def get_refund_list(self, order_id: str, platform: str = "taobao") -> List[RefundInfo]:
        try:
            platform_enum = Platform(platform)
            adapter = self.platform_adapters.get(platform_enum)
            if not adapter:
                return self._get_mock_refunds(order_id)

            return await adapter.get_refund_list(order_id)
        except Exception as e:
            logger.error(f"Error getting refund list: {e}")
            return self._get_mock_refunds(order_id)

    async def create_refund(
        self,
        order_id: str,
        reason: str,
        amount: float,
        platform: str = "taobao"
    ) -> Optional[RefundInfo]:
        try:
            platform_enum = Platform(platform)
            adapter = self.platform_adapters.get(platform_enum)
            if not adapter:
                return self._get_mock_refund(order_id, reason, amount)

            refund = await adapter.create_refund(order_id, reason, amount)
            if refund:
                cache_service.invalidate_order(order_id)
            return refund
        except Exception as e:
            logger.error(f"Error creating refund: {e}")
            return self._get_mock_refund(order_id, reason, amount)

    def _get_mock_refunds(self, order_id: str) -> List[RefundInfo]:
        return [
            RefundInfo(
                refund_id="R001",
                order_id=order_id,
                reason="尺码不合适",
                amount=99.00,
                status="待处理",
                created_at="2024-01-02 15:30:00"
            )
        ]

    def _get_mock_refund(self, order_id: str, reason: str, amount: float) -> RefundInfo:
        return RefundInfo(
            refund_id=f"R{int(time.time())}",
            order_id=order_id,
            reason=reason,
            amount=amount,
            status="待处理",
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )


class ProductService:
    def __init__(self):
        self.platform_adapters: Dict[Platform, any] = {}

    def register_platform(self, platform: Platform, adapter):
        self.platform_adapters[platform] = adapter

    @cached(cache_type="item", ttl=600)
    async def get_item_info(self, item_id: str, platform: str = "taobao") -> Optional[Dict]:
        try:
            platform_enum = Platform(platform)
            adapter = self.platform_adapters.get(platform_enum)
            if not adapter:
                return self._get_mock_item(item_id)

            return await adapter.get_item_info(item_id)
        except Exception as e:
            logger.error(f"Error getting item info: {e}")
            return self._get_mock_item(item_id)

    async def get_items_by_category(self, category: str) -> List[Dict]:
        return [
            {"item_id": "1001", "title": "2024新款羽绒服", "price": 599.00, "stock": 50},
            {"item_id": "1002", "title": "加绒保暖内衣套装", "price": 129.00, "stock": 200},
            {"item_id": "1003", "title": "运动休闲鞋", "price": 359.00, "stock": 80},
        ]

    async def search_items(self, keyword: str, platform: str = "taobao") -> List[Dict]:
        mock_results = [
            {"item_id": "1001", "title": f"{keyword} - 商品1", "price": 199.00, "sales": 1000},
            {"item_id": "1002", "title": f"{keyword} - 商品2", "price": 299.00, "sales": 800},
            {"item_id": "1003", "title": f"{keyword} - 商品3", "price": 399.00, "sales": 500},
        ]
        return mock_results

    def _get_mock_item(self, item_id: str) -> Dict:
        return {
            "item_id": item_id,
            "title": f"商品{item_id}",
            "price": 299.00,
            "stock": 100,
            "sales": 5000,
            "description": "这是商品的详细描述",
            "images": ["http://example.com/img1.jpg"],
            "props": [
                {"name": "颜色", "value": "黑色/白色/蓝色"},
                {"name": "尺码", "value": "S/M/L/XL/XXL"}
            ]
        }


class BusinessOrchestrator:
    def __init__(self):
        self.order_service = OrderService()
        self.refund_service = RefundService()
        self.product_service = ProductService()
        self._register_mock_adapters()

    def _register_mock_adapters(self):
        for platform in [Platform.TAOBAO, Platform.PINDUODUO, Platform.DOUYIN]:
            mock_adapter = MockPlatformAdapter()
            self.order_service.register_platform(platform, mock_adapter)
            self.refund_service.register_platform(platform, mock_adapter)
            self.product_service.register_platform(platform, mock_adapter)

    async def handle_order_query(self, order_id: str, platform: str = "taobao") -> Dict:
        start_time = time.time()

        intent_task = None
        order_task = self.order_service.get_order_detail(order_id, platform)
        logistics_task = self.order_service.get_logistics_info(order_id, platform)

        results = await response_time_optimizer.parallel_process(
            intent_task, order_task, logistics_task
        )

        duration = time.time() - start_time
        response_time_optimizer.check_sla("total", duration)

        return {
            "code": 0,
            "message": "success",
            "data": {
                "order": results[1] if len(results) > 1 else None,
                "logistics": results[2] if len(results) > 2 else None,
                "response_time": round(duration, 3)
            }
        }

    async def handle_refund_request(
        self,
        order_id: str,
        reason: str,
        amount: float,
        platform: str = "taobao"
    ) -> Dict:
        start_time = time.time()

        refund = await self.refund_service.create_refund(order_id, reason, amount, platform)

        duration = time.time() - start_time

        return {
            "code": 0,
            "message": "success",
            "data": {
                "refund_id": refund.refund_id if refund else None,
                "status": refund.status if refund else "failed",
                "response_time": round(duration, 3)
            }
        }

    async def handle_product_query(self, item_id: str, platform: str = "taobao") -> Dict:
        item = await self.product_service.get_item_info(item_id, platform)
        return {
            "code": 0,
            "message": "success",
            "data": item
        }

    async def handle_search(self, keyword: str, platform: str = "taobao") -> Dict:
        items = await self.product_service.search_items(keyword, platform)
        return {
            "code": 0,
            "message": "success",
            "data": {
                "items": items,
                "total": len(items)
            }
        }


class MockPlatformAdapter:
    async def get_order_detail(self, order_id: str):
        return OrderInfo(
            order_id=order_id,
            platform="taobao",
            status="已发货",
            buyer_nick="客户***",
            created_at="2024-01-01 10:00:00",
            total_amount=299.00,
            items=[{"name": "商品A", "num": 1, "price": 299.00}],
            shipping_address={"name": "张三", "phone": "138****8888", "address": "北京市朝阳区xxx"}
        )

    async def get_logistics_info(self, order_id: str):
        return LogisticsInfo(
            company="顺丰速运",
            tracking_no="SF1234567890",
            status="运输中",
            estimated_delivery="2024-01-05",
            traces=[
                {"time": "2024-01-03 14:30", "status": "商品已从仓库发出"},
                {"time": "2024-01-03 18:00", "status": "商品到达北京中转站"},
                {"time": "2024-01-04 09:30", "status": "商品运输中"}
            ]
        )

    async def get_refund_list(self, order_id: str):
        return [
            RefundInfo(
                refund_id="R001",
                order_id=order_id,
                reason="尺码不合适",
                amount=99.00,
                status="待处理",
                created_at="2024-01-02 15:30:00"
            )
        ]

    async def create_refund(self, order_id: str, reason: str, amount: float):
        return RefundInfo(
            refund_id=f"R{int(time.time())}",
            order_id=order_id,
            reason=reason,
            amount=amount,
            status="待处理",
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )

    async def get_item_info(self, item_id: str):
        return {
            "item_id": item_id,
            "title": f"商品{item_id}",
            "price": 299.00,
            "stock": 100,
            "sales": 5000,
            "props": [
                {"name": "颜色", "value": "黑色/白色/蓝色"},
                {"name": "尺码", "value": "S/M/L/XL/XXL"}
            ]
        }


business_orchestrator = BusinessOrchestrator()
order_service = business_orchestrator.order_service
refund_service = business_orchestrator.refund_service
product_service = business_orchestrator.product_service
