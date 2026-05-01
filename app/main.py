from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from loguru import logger
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.api.router import api_router
from app.agents.intent_agent import IntentAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.dialogue_agent import DialogueAgent


def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.debug else "INFO"
    )
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="DEBUG" if settings.debug else "INFO"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)

    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/knowledge_base", exist_ok=True)

    yield

    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="电商商家客服智能处理系统 - 多Agent协作架构",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_dir = os.path.join(base_dir, "app", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, "app", "static", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.post("/api/v1/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    session_id = data.get("session_id", "default")

    if not message:
        return {"code": -1, "message": "请输入消息", "data": {}}

    logger.info(f"收到消息: {message}")

    intent_agent = IntentAgent()
    knowledge_agent = KnowledgeAgent()
    dialogue_agent = DialogueAgent()
    from app.services.data_service import data_service

    if not hasattr(chat, 'conversation_history'):
        chat.conversation_history = {}
    if session_id not in chat.conversation_history:
        chat.conversation_history[session_id] = []
    chat.conversation_history[session_id].append({"role": "user", "content": message})

    history_text = "\n".join([f"{'用户' if h['role']=='user' else '小e'}: {h['content']}" for h in chat.conversation_history[session_id][-6:]])

    intent_result = intent_agent.recognize(message)
    logger.info(f"识别结果: {intent_result}")
    intent = intent_result.get("intent", "unknown")
    confidence = intent_result.get("confidence", 0.0)
    entities = intent_result.get("entities", {})
    reply = ""

    knowledge_context = knowledge_agent.retrieve_knowledge(message, intent, entities)
    logger.info(f"知识库检索结果: {knowledge_context}")

    extra_info = ""
    
    if intent in ["order_query", "order_status"] and confidence > 0.5:
        order_id = entities.get("order_id") or entities.get("order")
        if order_id:
            order = data_service.get_order_by_id(order_id)
            if order:
                status_map = {
                    "paid": "已支付，等待商家发货",
                    "shipped": "已发货，正在配送途中",
                    "in_transit": "运输中，即将送达",
                    "delivered": "已送达签收",
                    "refunding": "退款处理中"
                }
                status_desc = status_map.get(order.status, order.status)
                
                logistics = data_service.get_logistics_by_order(order_id)
                logistics_info = ""
                if logistics:
                    traces_text = "\n".join([f"  {i+1}. {t}" for i, t in enumerate(logistics.traces)]) if logistics.traces else "暂无轨迹"
                    logistics_info = f"""
【物流分析】
├ 快递公司: {logistics.company}
├ 运单号: {logistics.tracking_no}
├ 当前状态: {logistics.status}
├ 实时位置: {logistics.current_location}
└ 预计送达: {logistics.estimated_delivery}

【物流轨迹】
{traces_text}"""

                recs = data_service.get_recommendations(keyword=order.product_name, limit=3)
                related_products = ""
                if recs:
                    related_products = "【同类商品推荐】" + "".join([f"\n├ {r.product_name} - ￥{r.price}\n│   热销{r.popularity}件，好评如潮" for r in recs])

                coupons = data_service.get_available_coupons()
                available_coupons = ""
                if coupons:
                    top_coupons = coupons[:3]
                    available_coupons = "【当前可用优惠】" + "".join([f"\n├ {c.coupon_name}: 满{c.min_order_amount}减{c.discount_amount}元" for c in top_coupons])

                extra_info = f"""
═══════════════════════════════════════════
                    📋 订单分析报告
═══════════════════════════════════════════

【基本信息】
├ 订单编号: {order.order_id}
├ 商品名称: {order.product_name}
├ 购买数量: {order.quantity}件
├ 订单金额: ￥{order.total_amount}
├ 订单状态: {status_desc}
├ 购买平台: {order.platform}
├ 下单时间: {order.created_at}

【收货信息】
├ 收件人: {order.receiver_name}
└ 收货地址: {order.shipping_address}
{logistics_info}
{related_products}
{available_coupons}

【小e智能建议】
"""
                if order.status == "paid":
                    extra_info += "✅ 您的订单已支付成功，商家会在24小时内安排发货哦~\n"
                    extra_info += "💡 温馨提示：如有急需发货的商品，建议您联系商家说明情况，小e帮您催促~"
                elif order.status == "shipped":
                    extra_info += "🚚 您的宝贝已发出，正在配送途中，请保持电话畅通~\n"
                    extra_info += "💡 温馨提示：预计1-2天内送达，如联系不上快递可联系商家协查~"
                elif order.status == "in_transit":
                    extra_info += "📦 您的宝贝正在派送中，快递小哥正在努力配送~\n"
                    extra_info += "💡 温馨提示：预计今天或明天送达，请注意查收哦~"
                elif order.status == "delivered":
                    extra_info += "🎉 恭喜您！订单已签收，记得检查商品是否完好~\n"
                    extra_info += "💡 温馨提示：如有质量问题，7天内可申请退换货哦~"
                
                logger.info(f"查询到订单: {order}")
            else:
                extra_info = f"\n\n═══════════════════════════════════════════\n                    🔍 订单查询结果\n═══════════════════════════════════════════\n\n未查询到订单 {order_id} 的信息。\n\n【小e建议】\n1. 请核对订单号是否正确\n2. 订单号格式示例：DD20260501001\n3. 如有疑问可联系人工客服帮您查询\n═══════════════════════════════════════════"
    
    elif intent == "coupon_query" or "优惠" in message or "促销" in message or "券" in message:
        coupons = data_service.get_available_coupons()
        if coupons:
            cash_coupons = [c for c in coupons if c.type == 'cash']
            percent_coupons = [c for c in coupons if c.type == 'percentage']
            
            cash_list = "".join([f"\n├ {c.coupon_name}: 满{c.min_order_amount}减{c.discount_amount}元 (剩余{c.remaining_count}张)" for c in cash_coupons[:5]]) if cash_coupons else "\n└ 暂无现金券"
            percent_list = "".join([f"\n├ {c.coupon_name}: 满{c.min_order_amount}享{int(c.discount_amount*100)}折 (剩余{c.remaining_count}张)" for c in percent_coupons[:5]]) if percent_coupons else "\n└ 暂无折扣券"
            
            extra_info = f"""
═══════════════════════════════════════════
                  🎫 优惠券分析报告
═══════════════════════════════════════════

【现金券】
{cash_list}

【折扣券】
{percent_list}

【小e省钱攻略】
"""
            recs = data_service.get_recommendations(limit=3)
            if recs:
                total_price = sum([r.price for r in recs[:3]])
                extra_info += f"✅ 凑单建议：购买以上3款热销商品(总计￥{total_price})，可以使用满100减20券~\n"
            extra_info += "💡 温馨提示：优惠券数量有限，先到先得哦~\n"
            extra_info += "═══════════════════════════════════════════"
            logger.info(f"查询到优惠券: {coupons}")
    
    elif intent == "product_query" and confidence > 0.5:
        product_name = entities.get("product")
        if product_name:
            recs = data_service.get_recommendations(keyword=product_name, limit=5)
            if recs:
                rec_details = ""
                for i, r in enumerate(recs, 1):
                    rec_details += f"""
{i}. 【{r.category}】{r.product_name}
   ├ 价格: ￥{r.price}
   ├ 特色: {r.description}
   ├ 标签: {r.tag1} | {r.tag2} | {r.tag3}
   ├ 热度: {r.popularity}人已购
   └ 推荐理由: {r.reason}"""
                
                extra_info = f"""
═══════════════════════════════════════════
                🛍️ 商品推荐报告
═══════════════════════════════════════════

根据您的需求，为您推荐以下商品：
{rec_details}

【小e选购建议】
"""
                if recs:
                    avg_price = sum([r.price for r in recs]) / len(recs)
                    extra_info += f"📊 平均价格: ￥{avg_price:.2f}\n"
                    extra_info += f"💡 热销冠军: {recs[0].product_name} (已售{recs[0].popularity}件)\n"
                    extra_info += "💡 小e建议：根据您的喜好，第一款和第三款特别适合您哦~\n"
                extra_info += "═══════════════════════════════════════════"
                logger.info(f"查询到推荐: {recs}")
            else:
                extra_info = f"\n\n═══════════════════════════════════════════\n                🔍 商品查询结果\n═══════════════════════════════════════════\n\n没有找到与「{product_name}」相关的商品。\n\n【小e建议】\n1. 尝试其他关键词，如：连衣裙、T恤、鞋子\n2. 浏览我们的热销榜单\n3. 联系人工客服获取更多帮助\n═══════════════════════════════════════════"
    
    elif "推荐" in message or "帮我挑" in message or "有什么好看的" in message or "热销" in message:
        recs = data_service.get_recommendations(limit=6)
        if recs:
            categories = {}
            for r in recs:
                if r.category not in categories:
                    categories[r.category] = []
                categories[r.category].append(r)
            
            category_recs = ""
            for cat, items in categories.items():
                category_recs += f"\n【{cat}专区】"
                for item in items[:2]:
                    category_recs += f"\n├ {item.product_name} - ￥{item.price}"
            
            extra_info = f"""
═══════════════════════════════════════════
              ⭐ 智能推荐报告
═══════════════════════════════════════════

小e根据您的购物偏好，为您精心挑选了以下商品：
{category_recs}

【小e推荐亮点】
"""
            if recs:
                extra_info += f"🔥 本周爆款: {recs[0].product_name}\n"
                extra_info += f"💎 高性价比: {recs[2].product_name} (仅￥{recs[2].price})\n"
                extra_info += f"👑 品质之选: {recs[1].product_name}\n"
                extra_info += f"\n【搭配推荐】购买连衣裙+运动鞋，立享夏装8折优惠~\n"
            extra_info += "═══════════════════════════════════════════"
            logger.info(f"查询到推荐: {recs}")

    elif intent == "logistics_query" and confidence > 0.5:
        order_id = entities.get("order_id") or entities.get("order")
        if order_id:
            logistics = data_service.get_logistics_by_order(order_id)
            order = data_service.get_order_by_id(order_id)
            if logistics:
                traces_text = "\n".join([f"  {i+1}. {t}" for i, t in enumerate(logistics.traces)]) if logistics.traces else "暂无轨迹信息"
                
                status_analysis = ""
                if logistics.status == "in_transit":
                    status_analysis = "【物流状态分析】您的包裹正在运输途中，预计很快送达，请保持电话畅通~"
                elif logistics.status == "delivered":
                    status_analysis = "【物流状态分析】您的包裹已签收，记得检查商品是否完好无损哦~"
                elif logistics.status == "shipped":
                    status_analysis = "【物流状态分析】您的包裹已发货，正在等待快递揽收，请耐心等待~"
                
                extra_info = f"""
═══════════════════════════════════════════
              📦 物流追踪报告
═══════════════════════════════════════════

【物流详情】
├ 快递公司: {logistics.company}
├ 运单号码: {logistics.tracking_no}
├ 当前状态: {logistics.status}
├ 实时位置: {logistics.current_location}
└ 预计送达: {logistics.estimated_delivery}

【完整轨迹】
{traces_text}

{status_analysis}
═══════════════════════════════════════════"""
                logger.info(f"查询到物流: {logistics}")

    knowledge_with_data = str(knowledge_context) + extra_info

    if extra_info and any(key in intent for key in ["order", "coupon", "product", "logistics", "recommend"]):
        reply = knowledge_with_data
    else:
        full_context = f"对话历史:\n{history_text}\n\n" if history_text else ""
        full_prompt = full_context + knowledge_with_data

        if intent in ["greeting", "goodbye", "thanks"] and confidence > 0.7:
            reply = dialogue_agent.generate_reply(message, intent, full_prompt)
        elif confidence > 0.6:
            reply = dialogue_agent.generate_reply(message, intent, full_prompt, entities)
        else:
            reply = dialogue_agent.generate_reply(message, intent, full_prompt)

    chat.conversation_history[session_id].append({"role": "assistant", "content": reply})
    logger.info(f"最终回复: {reply}")

    return {
        "code": 0,
        "message": "success",
        "data": {
            "reply": reply,
            "intent": intent,
            "confidence": confidence,
            "entities": entities
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug
    )
