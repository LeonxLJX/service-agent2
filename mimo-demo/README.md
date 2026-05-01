# 适配小米 MiMo 大模型

本框架已适配小米 MiMo 大模型，支持 MiMo 接口一键接入、多轮 Agent 调用、工具编排。

## 🚀 快速运行

```bash
# 进入目录
cd mimo-demo

# 一键运行
python mimo_demo.py
```

## 📁 目录结构

```
mimo-demo/
├── mimo_demo.py      # MiMo 适配示例
├── mimo_adapter.py   # MiMo 适配器
├── requirements.txt  # 依赖
└── README.md         # 说明文档
```

## 🔧 依赖安装

```bash
pip install requests
```

## 📝 示例代码

```python
import requests

# MiMo API 配置
API_URL = "https://api.mimo.com/v1/chat/completions"
API_KEY = "your-mimo-api-key"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

data = {
    "model": "mimo-agent",
    "messages": [
        {"role": "user", "content": "帮我查询订单DD20260501001的状态"}
    ],
    "temperature": 0.7
}

response = requests.post(API_URL, headers=headers, json=data)
print(response.json())
```

## ⚡ 一键接入优势

| 特性 | 说明 |
|------|------|
| 🤖 多轮对话 | 支持上下文记忆，10+轮对话 |
| 🔧 工具编排 | 支持多个工具串联调用 |
| 📊 意图识别 | 自动识别用户意图并调用对应工具 |
| 💬 智能回复 | 生成自然语言回复 |
