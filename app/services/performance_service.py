import time
import hashlib
import json
from typing import Any, Optional, Dict, Callable
from functools import wraps
from dataclasses import dataclass, field
from collections import OrderedDict
import asyncio
from loguru import logger


@dataclass
class CacheEntry:
    value: Any
    timestamp: float
    ttl: float

    def is_expired(self) -> bool:
        if self.ttl <= 0:
            return False
        return time.time() - self.timestamp > self.ttl


class LRUCache:
    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            return None
        self.cache.move_to_end(key)
        return entry.value

    def set(self, key: str, value: Any, ttl: float = 300):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = CacheEntry(value=value, timestamp=time.time(), ttl=ttl)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        self.cache.clear()

    def size(self) -> int:
        return len(self.cache)


class CacheService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.order_cache = LRUCache(max_size=500)
        self.logistics_cache = LRUCache(max_size=500)
        self.item_cache = LRUCache(max_size=1000)
        self.intent_cache = LRUCache(max_size=100)
        self.knowledge_cache = LRUCache(max_size=200)

    def get_order(self, key: str) -> Optional[Dict]:
        return self.order_cache.get(key)

    def set_order(self, key: str, value: Dict, ttl: float = 60):
        self.order_cache.set(key, value, ttl)

    def get_logistics(self, key: str) -> Optional[Dict]:
        return self.logistics_cache.get(key)

    def set_logistics(self, key: str, value: Dict, ttl: float = 300):
        self.logistics_cache.set(key, value, ttl)

    def get_item(self, key: str) -> Optional[Dict]:
        return self.item_cache.get(key)

    def set_item(self, key: str, value: Dict, ttl: float = 600):
        self.item_cache.set(key, value, ttl)

    def get_intent(self, key: str) -> Optional[Dict]:
        return self.intent_cache.get(key)

    def set_intent(self, key: str, value: Dict, ttl: float = 3600):
        self.intent_cache.set(key, value, ttl)

    def get_knowledge(self, key: str) -> Optional[Dict]:
        return self.knowledge_cache.get(key)

    def set_knowledge(self, key: str, value: Dict, ttl: float = 1800):
        self.knowledge_cache.set(key, value, ttl)

    def invalidate_order(self, order_id: str):
        pattern = f"order:{order_id}"
        self.order_cache.delete(pattern)
        self.logistics_cache.delete(f"logistics:{order_id}")

    def clear_all(self):
        self.order_cache.clear()
        self.logistics_cache.clear()
        self.item_cache.clear()
        self.intent_cache.clear()
        self.knowledge_cache.clear()


cache_service = CacheService()


def cached(cache_type: str = "order", ttl: float = 300):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key_parts = [func.__name__] + list(args) + [str(kwargs)]
            cache_key = hashlib.md5(":".join(str(p) for p in cache_key_parts).encode()).hexdigest()

            if cache_type == "order":
                cached_value = cache_service.get_order(cache_key)
            elif cache_type == "logistics":
                cached_value = cache_service.get_logistics(cache_key)
            elif cache_type == "item":
                cached_value = cache_service.get_item(cache_key)
            elif cache_type == "intent":
                cached_value = cache_service.get_intent(cache_key)
            elif cache_type == "knowledge":
                cached_value = cache_service.get_knowledge(cache_key)
            else:
                cached_value = None

            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_value

            result = await func(*args, **kwargs)

            if result is not None:
                if cache_type == "order":
                    cache_service.set_order(cache_key, result, ttl)
                elif cache_type == "logistics":
                    cache_service.set_logistics(cache_key, result, ttl)
                elif cache_type == "item":
                    cache_service.set_item(cache_key, result, ttl)
                elif cache_type == "intent":
                    cache_service.set_intent(cache_key, result, ttl)
                elif cache_type == "knowledge":
                    cache_service.set_knowledge(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


class TokenOptimizer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.intent_summary_cache = {}
        self.dialogue_history_cache = {}
        self.max_history_length = 10
        self.compression_threshold = 0.7

    def compress_history(self, history: list) -> list:
        if len(history) <= self.max_history_length:
            return history

        compressed = history[:3]
        compressed.append({"role": "system", "content": f"[...{len(history) - 6}条对话已压缩...]"})
        compressed.extend(history[-3:])

        return compressed

    def should_compress(self, history: list) -> bool:
        total_length = sum(len(str(h.get("content", ""))) for h in history)
        estimated_tokens = total_length // 4
        return estimated_tokens > 2000

    def optimize_prompt(self, prompt: str, max_tokens: int = 500) -> str:
        if len(prompt) <= max_tokens * 4:
            return prompt

        sentences = prompt.split("。")
        compressed = ""
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) > max_tokens * 3:
                break
            compressed += sentence + "。"
            current_length += len(sentence)

        return compressed + "[内容已压缩]"

    def batch_intent_check(self, messages: list) -> Optional[str]:
        if len(messages) < 3:
            return None

        recent_intents = []
        for msg in messages[-5:]:
            if "intent" in msg:
                recent_intents.append(msg["intent"])

        if len(set(recent_intents)) == 1:
            return recent_intents[0]
        return None

    def get_cached_summary(self, user_id: str) -> Optional[str]:
        return self.dialogue_history_cache.get(user_id)

    def cache_summary(self, user_id: str, summary: str):
        self.dialogue_history_cache[user_id] = summary


token_optimizer = TokenOptimizer()


class ResponseTimeOptimizer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.prefetch_tasks = {}
        self.concurrent_limits = {}
        self.sla_thresholds = {
            "intent": 0.5,
            "knowledge": 0.8,
            "order": 1.0,
            "dialogue": 1.5,
            "total": 3.0
        }

    async def concurrent_api_call(self, calls: list, max_concurrent: int = 3) -> list:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_call(call):
            async with semaphore:
                return await call

        return await asyncio.gather(*[bounded_call(call) for call in calls])

    def check_sla(self, operation: str, duration: float) -> bool:
        threshold = self.sla_thresholds.get(operation, 1.0)
        passed = duration <= threshold
        if not passed:
            logger.warning(f"SLA breach for {operation}: {duration:.3f}s > {threshold}s")
        return passed

    async def prefetch_data(self, order_id: str, platform_adapter):
        task = asyncio.create_task(
            platform_adapter.get_order_detail(order_id)
        )
        self.prefetch_tasks[order_id] = task

    async def get_prefetched(self, order_id: str) -> Optional[Any]:
        if order_id in self.prefetch_tasks:
            task = self.prefetch_tasks.pop(order_id)
            try:
                return await asyncio.wait_for(task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.error(f"Prefetch timeout for order {order_id}")
                return None
        return None

    async def parallel_process(self, intent_task, knowledge_task, order_task=None):
        tasks = [intent_task]
        if knowledge_task:
            tasks.append(knowledge_task)
        if order_task:
            tasks.append(order_task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)

        return processed_results


response_time_optimizer = ResponseTimeOptimizer()
