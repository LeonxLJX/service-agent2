import csv
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class Order:
    order_id: str
    user_id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    status: str
    platform: str
    created_at: str
    shipping_address: str
    receiver_name: str
    receiver_phone: str

@dataclass
class Product:
    product_id: str
    product_name: str
    category: str
    brand: str
    price: float
    stock: int
    size: str
    color: str
    description: str
    features: str

@dataclass
class Logistics:
    tracking_no: str
    order_id: str
    company: str
    status: str
    current_location: str
    estimated_delivery: str
    created_at: str
    updated_at: str
    traces: List[str]

@dataclass
class Refund:
    refund_id: str
    order_id: str
    user_id: str
    amount: float
    reason: str
    type: str
    status: str
    created_at: str
    processed_at: Optional[str]
    description: str

@dataclass
class User:
    user_id: str
    nickname: str
    phone: str
    platform: str
    level: str
    points: int
    total_orders: int
    total_amount: float
    created_at: str
    last_order_date: str
    vip_status: str

@dataclass
class Recommendation:
    product_id: str
    category: str
    product_name: str
    description: str
    price: float
    stock: int
    popularity: int
    tag1: str
    tag2: str
    tag3: str
    reason: str

@dataclass
class Coupon:
    coupon_id: str
    coupon_name: str
    type: str
    discount_amount: float
    min_order_amount: float
    applicable_products: str
    start_date: str
    end_date: str
    status: str
    remaining_count: int
    total_count: int


class DataService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.orders: List[Order] = []
        self.products: List[Product] = []
        self.logistics: List[Logistics] = []
        self.refunds: List[Refund] = []
        self.users: List[User] = []
        self.coupons: List[Coupon] = []
        self.recommendations: List[Recommendation] = []
        self._load_all_data()

    def _load_all_data(self):
        self._load_orders()
        self._load_products()
        self._load_logistics()
        self._load_refunds()
        self._load_users()
        self._load_coupons()
        self._load_recommendations()
        logger.info(f"Loaded {len(self.orders)} orders, {len(self.products)} products, {len(self.logistics)} logistics, {len(self.refunds)} refunds, {len(self.users)} users, {len(self.coupons)} coupons")

    def _load_orders(self):
        path = os.path.join(self.data_dir, "orders.csv")
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.orders.append(Order(
                    order_id=row['order_id'],
                    user_id=row['user_id'],
                    product_id=row['product_id'],
                    product_name=row['product_name'],
                    quantity=int(row['quantity']),
                    unit_price=float(row['unit_price']),
                    total_amount=float(row['total_amount']),
                    status=row['status'],
                    platform=row['platform'],
                    created_at=row['created_at'],
                    shipping_address=row['shipping_address'],
                    receiver_name=row['receiver_name'],
                    receiver_phone=row['receiver_phone']
                ))

    def _load_products(self):
        path = os.path.join(self.data_dir, "products.csv")
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.products.append(Product(
                    product_id=row['product_id'],
                    product_name=row['product_name'],
                    category=row['category'],
                    brand=row['brand'],
                    price=float(row['price']),
                    stock=int(row['stock']),
                    size=row['size'],
                    color=row['color'],
                    description=row['description'],
                    features=row['features']
                ))

    def _load_logistics(self):
        path = os.path.join(self.data_dir, "logistics.csv")
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.logistics.append(Logistics(
                    tracking_no=row['tracking_no'],
                    order_id=row['order_id'],
                    company=row['company'],
                    status=row['status'],
                    current_location=row['current_location'],
                    estimated_delivery=row['estimated_delivery'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    traces=row['traces'].split('|') if row['traces'] else []
                ))

    def _load_refunds(self):
        path = os.path.join(self.data_dir, "refunds.csv")
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.refunds.append(Refund(
                    refund_id=row['refund_id'],
                    order_id=row['order_id'],
                    user_id=row['user_id'],
                    amount=float(row['amount']),
                    reason=row['reason'],
                    type=row['type'],
                    status=row['status'],
                    created_at=row['created_at'],
                    processed_at=row['processed_at'] or None,
                    description=row['description']
                ))

    def _load_users(self):
        path = os.path.join(self.data_dir, "users.csv")
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.users.append(User(
                    user_id=row['user_id'],
                    nickname=row['nickname'],
                    phone=row['phone'],
                    platform=row['platform'],
                    level=row['level'],
                    points=int(row['points']),
                    total_orders=int(row['total_orders']),
                    total_amount=float(row['total_amount']),
                    created_at=row['created_at'],
                    last_order_date=row['last_order_date'],
                    vip_status=row['vip_status']
                ))

    def _load_coupons(self):
        path = os.path.join(self.data_dir, "coupons.csv")
        if not os.path.exists(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.coupons.append(Coupon(
                    coupon_id=row['coupon_id'],
                    coupon_name=row['coupon_name'],
                    type=row['type'],
                    discount_amount=float(row['discount_amount']),
                    min_order_amount=float(row['min_order_amount']),
                    applicable_products=row['applicable_products'],
                    start_date=row['start_date'],
                    end_date=row['end_date'],
                    status=row['status'],
                    remaining_count=int(row['remaining_count']),
                    total_count=int(row['total_count'])
                ))

    def _load_recommendations(self):
        path = os.path.join(self.data_dir, "recommendations.csv")
        if not os.path.exists(path):
            logger.warning(f"Recommendations file not found: {path}")
            return
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.recommendations.append(Recommendation(
                    product_id=row['product_id'],
                    category=row['category'],
                    product_name=row['product_name'],
                    description=row['description'],
                    price=float(row['price']),
                    stock=int(row['stock']),
                    popularity=int(row['popularity']),
                    tag1=row['tag1'],
                    tag2=row['tag2'],
                    tag3=row['tag3'],
                    reason=row['reason']
                ))

    def get_recommendations(self, category: str = None, keyword: str = None, limit: int = 5) -> List[Recommendation]:
        results = self.recommendations
        
        if category:
            results = [r for r in results if r.category == category]
        
        if keyword:
            keyword_lower = keyword.lower()
            results = [r for r in results if 
                      keyword_lower in r.product_name.lower() or 
                      keyword_lower in r.description.lower() or
                      keyword_lower in r.tag1.lower() or
                      keyword_lower in r.tag2.lower() or
                      keyword_lower in r.tag3.lower()]
        
        results.sort(key=lambda x: x.popularity, reverse=True)
        return results[:limit]

    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        for order in self.orders:
            if order.order_id == order_id:
                return order
        return None

    def get_orders_by_user(self, user_id: str) -> List[Order]:
        return [o for o in self.orders if o.user_id == user_id]

    def get_orders_by_status(self, status: str) -> List[Order]:
        return [o for o in self.orders if o.status == status]

    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        for product in self.products:
            if product.product_id == product_id:
                return product
        return None

    def get_product_by_name(self, name: str) -> List[Product]:
        return [p for p in self.products if name in p.product_name]

    def get_logistics_by_order(self, order_id: str) -> Optional[Logistics]:
        for log in self.logistics:
            if log.order_id == order_id:
                return log
        return None

    def get_refund_by_order(self, order_id: str) -> Optional[Refund]:
        for refund in self.refunds:
            if refund.order_id == order_id:
                return refund
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        for user in self.users:
            if user.user_id == user_id:
                return user
        return None

    def get_available_coupons(self) -> List[Coupon]:
        return [c for c in self.coupons if c.status == 'active']

    def search_by_keyword(self, keyword: str) -> Dict[str, List]:
        results = {
            'orders': [],
            'products': [],
            'logistics': [],
            'refunds': [],
            'users': [],
            'coupons': []
        }

        for order in self.orders:
            if keyword.lower() in order.product_name.lower() or keyword.lower() in order.order_id.lower():
                results['orders'].append(order)

        for product in self.products:
            if keyword.lower() in product.product_name.lower():
                results['products'].append(product)

        for logistics in self.logistics:
            if keyword.lower() in logistics.order_id.lower() or keyword.lower() in logistics.tracking_no.lower():
                results['logistics'].append(logistics)

        for refund in self.refunds:
            if keyword.lower() in refund.order_id.lower():
                results['refunds'].append(refund)

        for user in self.users:
            if keyword.lower() in user.nickname.lower() or keyword in user.phone:
                results['users'].append(user)

        return results

    def get_data_summary(self) -> str:
        return f"""当前数据概览：
- 订单总数：{len(self.orders)}
  - 已支付：{len([o for o in self.orders if o.status == 'paid'])}
  - 已发货：{len([o for o in self.orders if o.status == 'shipped'])}
  - 已送达：{len([o for o in self.orders if o.status == 'delivered'])}
  - 退款中：{len([o for o in self.orders if o.status == 'refunding'])}
- 商品总数：{len(self.products)}
- 物流记录：{len(self.logistics)}
- 退款记录：{len(self.refunds)}
- 用户总数：{len(self.users)}
- 可用优惠券：{len(self.get_available_coupons())}"""


data_service = DataService()
