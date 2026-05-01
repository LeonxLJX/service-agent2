from pydantic_settings import BaseSettings
from typing import Optional
import yaml
import os
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "ecommerce-customer-service-agent"
    app_version: str = "1.0.0"
    debug: bool = False

    server_host: str = "0.0.0.0"
    server_port: int = 8000

    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    llm_api_base: str = "https://api.deepseek.com/v1"

    mimo_app_id: str = ""
    mimo_app_key: str = ""
    mimo_webhook_secret: str = ""
    mimo_api_base: str = "https://api.mimo.com/v1"

    database_type: str = "sqlite"
    database_path: str = "./data/ecommerce.db"

    vector_store_type: str = "faiss"
    vector_dimension: int = 1536

    knowledge_base_id: str = "default"
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.7

    intent_confidence_threshold: float = 0.6
    max_history_turns: int = 10
    human_intervention_threshold: float = 0.3

    class Config:
        env_file = ".env"
        extra = "ignore"

    @classmethod
    def load_from_yaml(cls, config_path: str = "config.yaml"):
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                if config_data and 'llm' in config_data:
                    llm_config = config_data['llm']
                    if 'api_key' in llm_config and '${LLM_API_KEY}' in str(llm_config['api_key']):
                        api_key_file = r"g:\新建文件夹 (10)\新建文件夹\111.txt"
                        if os.path.exists(api_key_file):
                            with open(api_key_file, 'r', encoding='utf-8') as key_file:
                                llm_config['api_key'] = key_file.read().strip()

            flat_config = {}
            for section, values in config_data.items():
                if isinstance(values, dict):
                    for key, value in values.items():
                        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                            env_var = value[2:-1]
                            value = os.getenv(env_var, "")
                        flat_config[key] = value

            return cls(**flat_config)
        return cls()


settings = Settings.load_from_yaml()
