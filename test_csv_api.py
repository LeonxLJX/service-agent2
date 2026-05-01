import requests
import json

url = "http://localhost:8000/api/v1/chat"

test_cases = [
    ("你好", "测试打招呼"),
    ("我想查一下DD20260501002这个订单", "测试订单查询"),
    ("DD20260501005的物流信息是什么", "测试物流查询"),
    ("连衣裙多少钱", "测试商品价格查询"),
    ("T恤有货吗", "测试商品库存查询"),
    ("你们发货时间是几点", "测试发货时间咨询"),
]

print("=" * 60)
print("电商客服系统测试")
print("=" * 60)

for message, desc in test_cases:
    print(f"\n【{desc}】输入: {message}")
    try:
        response = requests.post(url, json={"message": message})
        result = response.json()

        if result.get("code") == 0:
            data = result.get("data", {})
            print(f"回复: {data.get('reply', 'N/A')}")
            print(f"意图: {data.get('intent', 'N/A')} | 置信度: {data.get('confidence', 0)}")
        else:
            print(f"错误: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"请求失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
