"""LLM 客户端工厂"""
from typing import Dict, Any
from loguru import logger

from llm.base import BaseLLMClient
from llm.openai_client import OpenAIClient
from llm.anthropic_client import AnthropicClient
from llm.deepseek_client import DeepSeekClient
from llm.gemini_client import GeminiClient
from llm.glm_client import GLMClient
from llm.kimi_client import KimiClient


class LLMClientFactory:
    """LLM 客户端工厂"""

    # 支持的客户端类型
    SUPPORTED_CLIENTS = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "deepseek": DeepSeekClient,
        "gemini": GeminiClient,
        "glm": GLMClient,
        "kimi": KimiClient,
    }

    @classmethod
    def create(cls, client_type: str, **config) -> BaseLLMClient:
        """
        创建 LLM 客户端实例

        Args:
            client_type: 客户端类型（"openai" 或 "anthropic"）
            **config: 客户端配置参数

        Returns:
            BaseLLMClient: LLM 客户端实例

        Raises:
            ValueError: 不支持的客户端类型
        """
        client_type = client_type.lower()

        if client_type not in cls.SUPPORTED_CLIENTS:
            raise ValueError(
                f"不支持的客户端类型: {client_type}. "
                f"支持的类型: {', '.join(cls.SUPPORTED_CLIENTS.keys())}"
            )

        client_class = cls.SUPPORTED_CLIENTS[client_type]

        try:
            logger.info(f"创建 {client_type} 客户端: {config.get('model', 'default')}")
            return client_class(**config)
        except Exception as e:
            logger.error(f"创建 {client_type} 客户端失败: {e}")
            raise

    @classmethod
    def register_client(cls, client_type: str, client_class: type) -> None:
        """
        注册新的客户端类型

        Args:
            client_type: 客户端类型名称
            client_class: 客户端类（必须继承自 BaseLLMClient）
        """
        if not issubclass(client_class, BaseLLMClient):
            raise ValueError(f"{client_class} 必须继承自 BaseLLMClient")

        cls.SUPPORTED_CLIENTS[client_type.lower()] = client_class
        logger.info(f"已注册客户端类型: {client_type}")
