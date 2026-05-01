"""
小米 MiMo 大模型适配器
"""

import requests
from typing import List, Dict, Optional

class MiMoAdapter:
    """MiMo大模型适配器"""

    def __init__(self, api_key: str, api_url: str = "https://api.mimo.com/v1/chat/completions"):
        self.api_key = api_key
        self.api_url = api_url

    def chat(self, messages: List[Dict], model: str = "mimo-agent", temperature: float = 0.7) -> Dict:
        """发送聊天请求"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def chat_with_tools(self, messages: List[Dict], tools: List[Dict], model: str = "mimo-agent") -> Dict:
        """发送带工具调用的聊天请求"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "temperature": 0.7
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def parse_tool_calls(self, response: Dict) -> Optional[List[Dict]]:
        """解析工具调用"""
        choices = response.get("choices", [])
        if not choices:
            return None

        message = choices[0].get("message", {})
        return message.get("tool_calls")

    def get_content(self, response: Dict) -> str:
        """获取回复内容"""
        choices = response.get("choices", [])
        if not choices:
            return ""

        return choices[0].get("message", {}).get("content", "")

# ============== 使用示例 ==============
if __name__ == "__main__":
    # 初始化适配器
    adapter = MiMoAdapter(api_key="your-mimo-api-key")

    # 简单对话
    messages = [
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]

    response = adapter.chat(messages)
    print("简单对话:", adapter.get_content(response))

    # 带工具的对话
    messages = [
        {"role": "system", "content": "你是一个智能客服"},
        {"role": "user", "content": "帮我查一下订单DD20260501001的状态"}
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "query_order",
                "description": "查询订单",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"}
                    }
                }
            }
        }
    ]

    response = adapter.chat_with_tools(messages, tools)
    tool_calls = adapter.parse_tool_calls(response)

    if tool_calls:
        print("需要调用工具:", tool_calls)
    else:
        print("直接回复:", adapter.get_content(response))
