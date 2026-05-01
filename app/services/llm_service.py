from openai import OpenAI
from typing import Optional, List, Dict, Any
from app.config import settings
from loguru import logger


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_api_base
        )
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return f"抱歉，我现在无法回答您的问题，请稍后再试。"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return f"抱歉，我现在无法回答您的问题，请稍后再试。"

    def extract_entities(self, text: str, entity_types: List[str]) -> Dict[str, str]:
        prompt = f"""从以下文本中提取实体信息：
文本：{text}
需要提取的实体类型：{', '.join(entity_types)}

请以JSON格式返回，格式为：{{"实体类型": "提取的实体值"}}
如果没有找到某个实体，该实体值为空字符串。"""

        system_message = """你是一个实体识别专家，负责从用户输入中提取关键信息。
只返回JSON格式的结果，不要包含其他内容。"""

        try:
            result = self.generate(prompt, system_message)
            import json
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                return json.loads(result[start_idx:end_idx])
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")

        return {entity_type: "" for entity_type in entity_types}


llm_service = LLMService()
