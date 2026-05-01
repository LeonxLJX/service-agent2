import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.intent_agent import IntentAgent

agent = IntentAgent()

test_messages = [
    "你好",
    "发货时间是几点？",
    "我的订单什么时候到？",
    "这件衣服多少钱？",
]

for msg in test_messages:
    print(f"\n测试消息: {msg}")
    result = agent.recognize(msg)
    print(f"意图: {result.get('intent')}")
    print(f"置信度: {result.get('confidence')}")
    print(f"实体: {result.get('entities')}")
