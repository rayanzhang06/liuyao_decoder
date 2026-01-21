"""适配器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from llm.base import Message


class BaseAdapter(ABC):
    """LLM 提供商适配器基类"""

    def __init__(self, provider_config):
        """
        初始化适配器

        Args:
            provider_config: 提供商配置
        """
        self.config = provider_config

    @abstractmethod
    def format_request(self,
                      messages: List[Message],
                      model: str,
                      temperature: float,
                      max_tokens: int) -> Dict[str, Any]:
        """
        格式化API请求

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            Dict: 格式化后的请求参数
        """
        pass

    @abstractmethod
    def parse_response(self, response: Any) -> Dict[str, Any]:
        """
        解析API响应

        Args:
            response: 原始API响应

        Returns:
            Dict: 包含 content, model, usage 的字典
        """
        pass

    def get_client_init_args(self, api_key: str, **kwargs) -> Dict[str, Any]:
        """
        获取客户端初始化参数

        Args:
            api_key: API密钥
            **kwargs: 其他参数

        Returns:
            Dict: 客户端初始化参数
        """
        args = {
            'api_key': api_key
        }

        # 设置base_url（如果支持）
        if self.config.base_url:
            args['base_url'] = self.config.base_url

        # 设置代理（如果提供）
        if kwargs.get('http_proxy'):
            import httpx
            args['http_client'] = httpx.Client(
                proxies=kwargs['http_proxy']
            )

        return args
