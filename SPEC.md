# 电商商家客服智能处理系统 - 小米MIMO适配版

## 1. 项目概述

### 项目名称
`ecommerce-customer-service-agent` (电商客服智能Agent系统)

### 核心定位
基于多Agent协作的电商商家客服智能处理系统，解决中小商家多平台客服响应慢、重复咨询处理成本高、人工回复标准不统一的痛点。

### 目标用户
- 中小电商商家
- 多平台运营卖家（淘宝、京东、拼多多等）
- 需要自动化客服解决方案的电商企业

### 核心能力
- **意图识别**: 精准识别用户咨询意图（售前咨询、订单查询、售后问题、退换货等）
- **知识库检索**: 快速从商品知识库、FAQ库中检索相关信息
- **多轮对话**: 维护会话上下文，理解长链推理，生成自然流畅回复
- **订单处理**: 自动对接商品库存、物流、售后工单系统

### 性能指标
- 日均处理咨询量: 300+（单店铺）
- 响应时间: 从平均2分钟缩短至5秒
- 人工介入率降低: 65%
- 月节省客服人力: 约80小时
- 月Token消耗: 约120万
- 用户好评率提升: 18%

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        小米MIMO平台接入层                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  淘宝店铺   │  │  京东店铺   │  │  拼多多店铺  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent调度层 (Router)                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Intent Recognition Agent                  ││
│  │                        意图识别Agent                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│           ┌──────────────────┼──────────────────┐               │
│           ▼                  ▼                  ▼               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐       │
│  │ Knowledge Base │ │ Multi-turn     │ │ Order          │       │
│  │ Retrieval Agent│ │ Dialogue Agent │ │ Processing Agent│      │
│  │ 知识库检索Agent │ │ 多轮对话Agent   │ │ 订单处理Agent   │       │
│  └────────────────┘ └────────────────┘ └────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        业务系统对接层                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐     │
│  │  商品系统  │  │  库存系统  │  │  物流系统  │  │  售后系统  │     │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent详细设计

#### 2.2.1 意图识别Agent (Intent Recognition Agent)

**职责**: 接收用户消息，识别用户真实意图

**支持意图类型**:
| 意图类型 | 子意图 | 描述 |
|---------|-------|------|
| 售前咨询 | product_inquiry, size_guide, color_selection, price_query | 商品咨询、尺码、颜色、价格 |
| 订单查询 | order_status, logistics_query, delivery_time | 订单状态、物流、送达时间 |
| 售后问题 | return_request, exchange_request, complaint | 退货、换货、投诉 |
| 退款问题 | refund_status, refund_application | 退款状态、申请 |
| 投诉建议 | product_complaint, service_complaint, suggestion | 产品投诉、服务投诉、建议 |

**技术实现**:
- 基于规则+模型混合方式
- 使用关键词匹配 + 语义理解
- 支持模糊意图识别和意图澄清

#### 2.2.2 知识库检索Agent (Knowledge Base Retrieval Agent)

**职责**: 根据意图检索相关知识，生成回复依据

**知识库类型**:
| 知识库 | 内容 | 用途 |
|-------|------|------|
| 商品知识库 | 商品属性、规格、使用方法 | 售前咨询 |
| FAQ库 | 常见问题标准答案 | 常规咨询 |
| 政策库 | 退换货政策、运费险政策 | 售后问题 |
| 话术库 | 标准回复话术 | 回复生成 |

**技术实现**:
- 向量相似度检索
- BM25关键词检索
- 混合检索策略

#### 2.2.3 多轮对话Agent (Multi-turn Dialogue Agent)

**职责**: 维护对话上下文，生成自然流畅的回复

**核心能力**:
- 对话状态跟踪 (Dialogue State Tracking)
- 上下文理解与推理
- 回复生成与优化
- 多轮交互决策

**技术实现**:
- 基于历史对话的上下文管理
- LLM生成回复
- 情感分析与回复风格调整

#### 2.2.4 订单处理Agent (Order Processing Agent)

**职责**: 对接业务系统，处理订单相关操作

**支持操作**:
| 操作类型 | 描述 | 涉及系统 |
|---------|------|---------|
| 订单查询 | 根据订单号/用户信息查询订单 | 订单系统 |
| 物流查询 | 查询物流轨迹和状态 | 物流系统 |
| 退货申请 | 创建退货工单 | 售后系统 |
| 换货申请 | 创建换货工单 | 售后系统 |
| 退款查询 | 查询退款进度 | 财务系统 |

**技术实现**:
- API网关封装
- 业务逻辑编排
- 异常处理与重试

### 2.3 小米MIMO适配层

**MIMO平台特性**:
- 支持多渠道消息接入
- 提供Webhook回调机制
- 支持消息模板配置
- 具备完整的客服工作台集成能力

**适配层职责**:
- 消息格式转换
- 事件回调处理
- 消息推送管理
- 会话状态同步

## 3. 功能模块

### 3.1 核心功能清单

| 模块 | 功能 | 优先级 | 状态 |
|-----|------|-------|------|
| 意图识别 | 多意图识别 | P0 | 实现 |
| 意图识别 | 意图澄清 | P1 | 实现 |
| 意图识别 | 意图置信度 | P1 | 实现 |
| 知识库检索 | 向量检索 | P0 | 实现 |
| 知识库检索 | 关键词检索 | P0 | 实现 |
| 知识库检索 | 混合检索 | P1 | 实现 |
| 多轮对话 | 上下文管理 | P0 | 实现 |
| 多轮对话 | 回复生成 | P0 | 实现 |
| 多轮对话 | 对话策略 | P1 | 实现 |
| 订单处理 | 订单查询 | P0 | 实现 |
| 订单处理 | 物流查询 | P0 | 实现 |
| 订单处理 | 退换货 | P1 | 实现 |
| MIMO适配 | 消息接入 | P0 | 实现 |
| MIMO适配 | 消息推送 | P0 | 实现 |
| MIMO适配 | 事件回调 | P1 | 实现 |

### 3.2 用户交互流程

```
用户发送消息
     │
     ▼
┌─────────────┐
│ MIMO平台接收 │─────────────┐
└─────────────┘             │
     │                      │
     ▼                      │
┌─────────────┐             │
│ 消息格式转换 │             │
└─────────────┘             │
     │                      │
     ▼                      │
┌─────────────┐             │
│ 意图识别Agent│             │
└─────────────┘             │
     │                      │
     ├──────────────────────┤
     │                      │
     ▼                      ▼
┌─────────────┐      ┌─────────────┐
│ 知识库检索   │      │ 订单处理    │
│ Agent       │      │ Agent       │
└─────────────┘      └─────────────┘
     │                      │
     └──────────┬───────────┘
                │
                ▼
         ┌─────────────┐
         │ 多轮对话    │
         │ Agent       │
         └─────────────┘
                │
                ▼
         ┌─────────────┐
         │ 回复生成    │
         └─────────────┘
                │
                ▼
┌─────────────┐ ┌─────────────┐
│ MIMO平台推送 │ │ 人工介入判断 │
└─────────────┘ └─────────────┘
```

## 4. API接口设计

### 4.1 对外API

#### 4.1.1 消息接收接口

```
POST /api/v1/mimo/webhook
```

**请求体**:
```json
{
  "event": "message.receive",
  "platform": "taobao",
  "shop_id": "shop_12345",
  "customer": {
    "open_id": "user_abc123",
    "nickname": "买家小明"
  },
  "message": {
    "msg_id": "msg_123456",
    "type": "text",
    "content": "我想问一下这件衣服有没有大码的？"
  },
  "session": {
    "session_id": "session_789",
    "context": {}
  },
  "timestamp": 1704067200000
}
```

**响应体**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "msg_id": "msg_123456",
    "handled": true,
    "response": {
      "content": "您好！这款衣服有加大码的，有XL和XXL两个尺码可选。请问您平时穿什么尺码呢？"
    }
  }
}
```

#### 4.1.2 订单查询接口

```
GET /api/v1/orders/{order_id}
```

**响应体**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": "order_123456",
    "status": "shipped",
    "items": [
      {
        "product_id": "prod_001",
        "name": "夏季男士T恤",
        "quantity": 2,
        "price": 99.00
      }
    ],
    "total_amount": 198.00,
    "shipping": {
      "company": "顺丰速运",
      "tracking_no": "SF1234567890",
      "status": "运输中",
      "estimated_delivery": "2024-01-05"
    }
  }
}
```

#### 4.1.3 意图识别接口

```
POST /api/v1/intent/recognize
```

**请求体**:
```json
{
  "message": "我想问一下这件衣服有没有大码的？",
  "history": [
    {
      "role": "user",
      "content": "这件T恤多少钱？"
    },
    {
      "role": "assistant",
      "content": "这款T恤的价格是99元。"
    }
  ]
}
```

**响应体**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "intent": "product_inquiry",
    "sub_intent": "size_guide",
    "confidence": 0.95,
    "entities": {
      "product": "衣服",
      "attribute": "尺码"
    },
    "suggestions": ["查库存", "查看尺码表"]
  }
}
```

### 4.2 内部API

| 接口 | 方法 | 描述 |
|-----|------|------|
| /api/v1/agent/knowledge/retrieve | POST | 知识库检索 |
| /api/v1/agent/dialogue/generate | POST | 对话生成 |
| /api/v1/agent/order/query | POST | 订单查询 |
| /api/v1/agent/logistics/query | POST | 物流查询 |

## 5. 数据模型

### 5.1 核心实体

#### 5.1.1 对话会话 (Conversation)

```python
class Conversation:
    session_id: str           # 会话ID
    user_id: str              # 用户ID
    shop_id: str              # 店铺ID
    platform: str             # 平台 (taobao/jd/pdd)
    history: List[Message]     # 对话历史
    context: Dict             # 上下文信息
    current_intent: str       # 当前意图
    state: str                # 会话状态
    created_at: datetime      # 创建时间
    updated_at: datetime      # 更新时间
```

#### 5.1.2 消息 (Message)

```python
class Message:
    msg_id: str               # 消息ID
    role: str                 # user/assistant/system
    content: str               # 消息内容
    type: str                  # text/image/card
    metadata: Dict            # 元数据
    timestamp: datetime       # 时间戳
```

#### 5.1.3 知识条目 (KnowledgeItem)

```python
class KnowledgeItem:
    kb_id: str                # 知识库ID
    item_id: str              # 条目ID
    category: str             # 分类
    question: str              # 问题
    answer: str                # 答案
    embeddings: List[float]  # 向量
    metadata: Dict            # 扩展信息
    created_at: datetime      # 创建时间
```

### 5.2 数据库设计

#### 5.2.1 会话表 (conversations)

| 字段 | 类型 | 描述 |
|-----|------|------|
| id | BIGINT | 主键 |
| session_id | VARCHAR(64) | 会话ID |
| user_id | VARCHAR(64) | 用户ID |
| shop_id | VARCHAR(64) | 店铺ID |
| platform | VARCHAR(32) | 平台 |
| context | JSON | 上下文 |
| state | VARCHAR(32) | 状态 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 5.2.2 消息表 (messages)

| 字段 | 类型 | 描述 |
|-----|------|------|
| id | BIGINT | 主键 |
| session_id | VARCHAR(64) | 会话ID |
| role | VARCHAR(16) | 角色 |
| content | TEXT | 内容 |
| type | VARCHAR(32) | 类型 |
| metadata | JSON | 元数据 |
| timestamp | DATETIME | 时间戳 |

#### 5.2.3 知识库表 (knowledge_base)

| 字段 | 类型 | 描述 |
|-----|------|------|
| id | BIGINT | 主键 |
| kb_id | VARCHAR(64) | 知识库ID |
| category | VARCHAR(64) | 分类 |
| question | TEXT | 问题 |
| answer | TEXT | 答案 |
| embeddings | BLOB | 向量 |
| metadata | JSON | 扩展信息 |
| created_at | DATETIME | 创建时间 |

## 6. 技术实现

### 6.1 技术栈

| 层级 | 技术选型 | 说明 |
|-----|---------|------|
| 编程语言 | Python 3.10+ | 主要开发语言 |
| 异步框架 | FastAPI | 高性能API框架 |
| 数据库 | SQLite/PostgreSQL | 数据持久化 |
| 向量存储 | FAISS/Milvus | 向量检索 |
| LLM | OpenAI GPT-4 / 兼容API | 对话生成 |
| 日志 | loguru | 日志记录 |
| 配置 | pydantic-settings | 配置管理 |

### 6.2 项目结构

```
ecommerce-customer-service-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口
│   ├── config.py               # 配置管理
│   ├── api/                    # API层
│   │   ├── __init__.py
│   │   ├── router.py           # 路由配置
│   │   └── endpoints/          # 接口定义
│   │       ├── __init__.py
│   │       ├── mimo.py         # MIMO平台对接
│   │       ├── intent.py       # 意图识别接口
│   │       ├── knowledge.py    # 知识库接口
│   │       └── order.py        # 订单接口
│   ├── agents/                 # Agent层
│   │   ├── __init__.py
│   │   ├── base.py             # Agent基类
│   │   ├── intent_agent.py     # 意图识别Agent
│   │   ├── knowledge_agent.py   # 知识库检索Agent
│   │   ├── dialogue_agent.py    # 多轮对话Agent
│   │   └── order_agent.py       # 订单处理Agent
│   ├── services/               # 服务层
│   │   ├── __init__.py
│   │   ├── llm_service.py      # LLM服务
│   │   └── vector_service.py   # 向量服务
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── conversation.py    # 会话模型
│   │   ├── message.py          # 消息模型
│   │   └── knowledge.py        # 知识模型
│   ├── adapters/               # 适配器层
│   │   ├── __init__.py
│   │   └── mimo_adapter.py     # 小米MIMO适配器
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       └── helpers.py
├── tests/                      # 测试用例
│   ├── __init__.py
│   ├── test_intent_agent.py
│   ├── test_knowledge_agent.py
│   ├── test_dialogue_agent.py
│   └── test_order_agent.py
├── data/                       # 数据目录
│   └── knowledge_base/         # 知识库文件
│       ├── faq.json
│       └── product_knowledge.json
├── config.yaml                 # 配置文件
├── requirements.txt            # 依赖清单
├── SPEC.md                     # 项目文档
└── README.md                   # 项目说明
```

## 7. 配置说明

### 7.1 config.yaml

```yaml
app:
  name: "ecommerce-customer-service-agent"
  version: "1.0.0"
  debug: false

server:
  host: "0.0.0.0"
  port: 8000

llm:
  provider: "openai"  # openai/ernie/qwen
  api_key: "${LLM_API_KEY}"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 1000

mimo:
  app_id: "${MIMO_APP_ID}"
  app_key: "${MIMO_APP_KEY}"
  webhook_secret: "${MIMO_WEBHOOK_SECRET}"
  api_base: "https://api.mimo.com/v1"

database:
  type: "sqlite"  # sqlite/postgresql
  path: "./data/ecommerce.db"

vector_store:
  type: "faiss"  # faiss/milvus
  dimension: 1536

knowledge_base:
  default_kb_id: "default"
  retrieval_top_k: 5
  similarity_threshold: 0.7

agent:
  intent_confidence_threshold: 0.6
  max_history_turns: 10
  human_intervention_threshold: 0.3
```

## 8. 部署说明

### 8.1 环境要求

- Python 3.10+
- Redis (可选，用于缓存)
- FAISS (向量检索)

### 8.2 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export LLM_API_KEY="your-api-key"
export MIMO_APP_ID="your-app-id"
export MIMO_APP_KEY="your-app-key"

# 3. 初始化知识库
python -m app.scripts.init_knowledge_base

# 4. 启动服务
python -m app.main
```

## 9. 验收标准

### 9.1 功能验收

- [ ] MIMO平台消息接入正常
- [ ] 意图识别准确率 ≥ 90%
- [ ] 知识库检索响应时间 < 500ms
- [ ] 多轮对话上下文理解正确
- [ ] 订单查询功能完整
- [ ] 人工介入判断准确

### 9.2 性能验收

- [ ] 单次请求响应时间 < 5秒
- [ ] 日均处理量 ≥ 300
- [ ] 系统可用性 ≥ 99.9%

### 9.3 安全验收

- [ ] API密钥安全存储
- [ ] Webhook签名验证
- [ ] 输入内容安全过滤

## 10. 版本历史

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| 1.0.0 | 2024-01-01 | 初始版本，实现核心功能 |
