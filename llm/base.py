"""LLM 抽象基类和接口定义"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Message(BaseModel):
    """聊天消息"""
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """LLM 响应"""
    content: str
    model: str
    usage: Dict[str, int]  # {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 密钥
            model: 模型名称
            **kwargs: 其他配置参数（temperature, max_tokens, timeout, http_proxy 等）
        """
        self.api_key = api_key
        self.model = model
        self.temperature = kwargs.get('temperature', 0.7)
        self.max_tokens = kwargs.get('max_tokens', 4000)
        self.timeout = kwargs.get('timeout', 60)
        self.http_proxy = kwargs.get('http_proxy')
        self.https_proxy = kwargs.get('https_proxy')

    @abstractmethod
    def chat(self,
             messages: List[Message],
             model: Optional[str] = None,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> LLMResponse:
        """
        聊天接口

        Args:
            messages: 消息列表
            model: 模型名称（可选，覆盖默认值）
            temperature: 温度参数（可选，覆盖默认值）
            max_tokens: 最大 token 数（可选，覆盖默认值）

        Returns:
            LLMResponse: LLM 响应对象
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        计算 Token 数量

        Args:
            text: 输入文本

        Returns:
            int: Token 数量
        """
        pass

    def _validate_messages(self, messages: List[Message]) -> None:
        """验证消息格式"""
        if not messages:
            raise ValueError("消息列表不能为空")

        for msg in messages:
            if msg.role not in ["system", "user", "assistant"]:
                raise ValueError(f"无效的消息角色: {msg.role}")
            if not msg.content:
                raise ValueError("消息内容不能为空")
