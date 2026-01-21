"""LLM 客户端工厂"""
import os
from typing import Dict, Any
from loguru import logger

from llm.base import BaseLLMClient
from llm.http_client import UniversalLLMClient


class LLMClientFactory:
    """LLM 客户端工厂"""

    # 支持的客户端类型 - 使用统一的UniversalLLMClient
    SUPPORTED_CLIENTS = {
        "openai": "openai",
        "anthropic": "anthropic",
        "deepseek": "deepseek",
        "gemini": "gemini",
        "glm": "glm",
        "kimi": "kimi",
    }

    @classmethod
    def create(cls, client_type: str, **config) -> BaseLLMClient:
        """
        创建 LLM 客户端实例

        Args:
            client_type: 客户端类型（"openai", "anthropic", "kimi", "glm", "deepseek", "gemini"）
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

        # 自动从环境变量读取代理配置（如果没有在 config 中指定）
        if 'http_proxy' not in config and os.getenv('HTTP_PROXY'):
            config['http_proxy'] = os.getenv('HTTP_PROXY')
        if 'https_proxy' not in config and os.getenv('HTTPS_PROXY'):
            config['https_proxy'] = os.getenv('HTTPS_PROXY')

        # 对于国际提供商，如果没有设置代理，记录警告
        international_providers = ['openai', 'anthropic', 'gemini']
        if client_type in international_providers:
            if not config.get('http_proxy') and not config.get('https_proxy'):
                logger.warning(f"{client_type} 是国际提供商，建议配置代理以避免连接超时")

        try:
            logger.info(f"创建 {client_type} 客户端: {config.get('model', 'default')}")
            # 使用统一的UniversalLLMClient
            return UniversalLLMClient(provider_type=client_type, **config)
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
