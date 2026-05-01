"""
小米 MiMo 大模型适配示例
快速接入多Agent电商客服系统
"""

import requests
import json
import time

# ============== MiMo API 配置 ==============
MIMO_API_URL = "https://api.mimo.com/v1/chat/completions"
MIMO_API_KEY = "your-mimo-api-key"  # 请替换为您的MiMo API Key

# ============== 工具定义 ==============
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "查询订单状态和详细信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单号"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_logistics",
            "description": "查询物流追踪信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "tracking_no": {"type": "string", "description": "运单号"}
                },
                "required": ["tracking_no"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_coupon",
            "description": "查询可用优惠券",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"}
                },
                "required": ["user_id"]
            }
        }
    }
]

# ============== 模拟数据 ==============
MOCK_DATA = {
    "DD20260501001": {
        "order_id": "DD20260501001",
        "status": "shipped",
        "product": "夏季连衣裙",
        "amount": 199.00,
        "logistics": "SF1234567890",
        "estimate": "2026-05-03"
    },
    "DD20260501002": {
        "order_id": "DD20260501002",
        "status": "delivered",
        "product": "运动休闲鞋",
        "amount": 299.00,
        "logistics": "YT9876543210",
        "estimate": "已签收"
    }
}

# ============== 工具实现 ==============
def query_order(order_id: str) -> dict:
    """查询订单"""
    order = MOCK_DATA.get(order_id)
    if order:
        status_map = {
            "paid": "已支付，等待发货",
            "shipped": "已发货，运输中",
            "delivered": "已签收"
        }
        return {
            "success": True,
            "data": {
                "订单号": order["order_id"],
                "商品": order["product"],
                "金额": f"￥{order['amount']}",
                "状态": status_map.get(order["status"], order["status"]),
                "快递": order["logistics"],
                "预计送达": order["estimate"]
            }
        }
    return {"success": False, "error": f"未找到订单 {order_id}"}

def query_logistics(tracking_no: str) -> dict:
    """查询物流"""
    for order_id, order in MOCK_DATA.items():
        if order["logistics"] == tracking_no:
            return {
                "success": True,
                "data": {
                    "运单号": tracking_no,
                    "快递": "顺丰速运",
                    "状态": "运输中",
                    "当前位置": "杭州转运中心",
                    "轨迹": ["已发出", "杭州入库", "转运中", "派送中"]
                }
            }
    return {"success": False, "error": f"未找到物流 {tracking_no}"}

def query_coupon(user_id: str) -> dict:
    """查询优惠券"""
    return {
        "success": True,
        "data": [
            {"name": "新人专享券", "amount": 20, "condition": "满100可用"},
            {"name": "夏季特惠券", "amount": 30, "condition": "满200可用"},
            {"name": "会员专属券", "amount": 50, "condition": "满300可用"}
        ]
    }

# ============== MiMo API 调用 ==============
def call_mimo(messages: list, tools: list = None) -> dict:
    """调用MiMo大模型"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MIMO_API_KEY}"
    }

    payload = {
        "model": "mimo-agent",
        "messages": messages,
        "temperature": 0.7
    }

    if tools:
        payload["tools"] = tools

    try:
        response = requests.post(MIMO_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def agent_loop(user_message: str):
    """Agent多轮对话循环"""
    messages = [
        {"role": "system", "content": "你是一个智能电商客服，名字叫小e。你的工作是帮用户查询订单、物流、优惠券等信息。"}
    ]
    messages.append({"role": "user", "content": user_message})

    print(f"\n👤 用户: {user_message}")

    while True:
        # 调用MiMo
        result = call_mimo(messages, TOOLS)

        if "error" in result:
            print(f"❌ API错误: {result['error']}")
            break

        choices = result.get("choices", [])
        if not choices:
            break

        assistant_message = choices[0]["message"]
        messages.append(assistant_message)

        # 检查是否需要调用工具
        if "tool_calls" in assistant_message:
            for tool_call in assistant_message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])

                print(f"🔧 调用工具: {func_name}({args})")

                # 执行工具
                if func_name == "query_order":
                    tool_result = query_order(**args)
                elif func_name == "query_logistics":
                    tool_result = query_logistics(**args)
                elif func_name == "query_coupon":
                    tool_result = query_coupon(**args)
                else:
                    tool_result = {"error": f"未知工具: {func_name}"}

                # 添加工具结果
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
                print(f"📋 工具结果: {tool_result}")
        else:
            # 最终回复
            content = assistant_message.get("content", "")
            print(f"🤖 小e: {content}")
            break

    return messages

# ============== 主程序 ==============
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 小米 MiMo 大模型电商客服示例")
    print("=" * 50)

    # 示例对话
    examples = [
        "帮我查一下订单DD20260501001",
        "这个订单什么时候能到？",
        "有什么优惠券可以用？"
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{'='*20} 示例{i} {'='*20}")
        agent_loop(example)
        time.sleep(1)

    print("\n" + "=" * 50)
    print("✅ 示例运行完成！")
    print("=" * 50)
