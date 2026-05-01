import requests
import json

url = "http://localhost:8000/api/v1/chat"

test_messages = [
    "你好",
    "发货时间是几点？",
    "这件衣服多少钱？",
]

for msg in test_messages:
    print(f"\n===== 测试消息: {msg} =====")
    data = {"message": msg}
    headers = {"Content-Type": "application/json; charset=utf-8"}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        print(f"回复: {result.get('data', {}).get('reply')}")
        print(f"意图: {result.get('data', {}).get('intent')}")
        print(f"置信度: {result.get('data', {}).get('confidence')}")
    except Exception as e:
        print(f"请求失败: {e}")
