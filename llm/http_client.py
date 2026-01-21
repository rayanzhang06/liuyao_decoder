"""通用LLM客户端 - 统一多个提供商的API调用"""
import time
from typing import List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from llm.base import BaseLLMClient, Message, LLMResponse
from llm.provider_config import get_provider_config
from llm.providers import (
    KimiAdapter, GLMAdapter, DeepSeekAdapter,
    OpenAIAdapter, AnthropicAdapter, GeminiAdapter
)


# 适配器映射
ADAPTERS = {
    'kimi': KimiAdapter,
    'glm': GLMAdapter,
    'deepseek': DeepSeekAdapter,
    'openai': OpenAIAdapter,
    'anthropic': AnthropicAdapter,
    'gemini': GeminiAdapter
}


class UniversalLLMClient(BaseLLMClient):
    """通用LLM客户端 - 支持多个提供商"""

    def __init__(self, provider_type: str, **kwargs):
        """
        初始化通用LLM客户端

        Args:
            provider_type: 提供商类型 (kimi, glm, deepseek, openai, anthropic, gemini)
            **kwargs: 其他配置参数 (api_key, model, temperature, max_tokens, timeout, etc.)
        """
        # 获取提供商配置
        self.provider_type = provider_type
        self.provider_config = get_provider_config(provider_type)

        # 从kwargs中提取参数并初始化基类
        # 注意：不要再次传递api_key和model，避免"got multiple values"错误
        super().__init__(**kwargs)

        # 创建适配器
        adapter_class = ADAPTERS.get(provider_type)
        if not adapter_class:
            raise ValueError(f"不支持的提供商类型: {provider_type}")
        self.adapter = adapter_class(self.provider_config)

        # 初始化提供商客户端
        self._init_client()

    def _init_client(self):
        """初始化提供商客户端"""
        try:
            if self.provider_config.import_name == 'openai':
                from openai import OpenAI
                init_args = self.adapter.get_client_init_args(
                    self.api_key,
                    http_proxy=self.http_proxy,
                    https_proxy=self.https_proxy
                )
                self.client = OpenAI(**init_args)

            elif self.provider_config.import_name == 'zhipuai':
                import zhipuai
                init_args = self.adapter.get_client_init_args(self.api_key)
                self.client = zhipuai.ZhipuAI(**init_args)

            elif self.provider_config.import_name == 'anthropic':
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)

            elif self.provider_config.import_name == 'google.generativeai':
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)

            else:
                raise ImportError(f"未知的提供商导入模块: {self.provider_config.import_name}")

            logger.info(f"初始化 {self.provider_config.name} 客户端成功")

        except ImportError as e:
            raise ImportError(f"请安装 {self.provider_config.import_name} 库: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    def chat(self,
             messages: List[Message],
             model: Optional[str] = None,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> LLMResponse:
        """
        调用提供商API

        Args:
            messages: 消息列表
            model: 模型名称（可选）
            temperature: 温度参数（可选）
            max_tokens: 最大 token 数（可选）

        Returns:
            LLMResponse: LLM 响应对象
        """
        self._validate_messages(messages)

        # 使用提供的参数或默认值
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens

        # 格式化请求
        request_params = self.adapter.format_request(messages, model, temperature, max_tokens)

        logger.info(f"调用 {self.provider_config.name} API: model={model}, messages={len(messages)}")

        try:
            start_time = time.time()

            # 调用API
            if self.provider_config.is_openai_compatible:
                # OpenAI兼容接口
                response = self.client.chat.completions.create(
                    **request_params,
                    timeout=self.timeout
                )
            elif self.provider_type == 'glm':
                # GLM专用接口
                response = self.client.chat.completions.create(**request_params)
            elif self.provider_type == 'anthropic':
                # Anthropic专用接口
                response = self.client.messages.create(**request_params)
            elif self.provider_type == 'gemini':
                # Gemini专用接口
                response = self.client.generate_content(**request_params)
            else:
                raise ValueError(f"未实现的提供商类型: {self.provider_type}")

            elapsed_time = time.time() - start_time
            logger.info(f"{self.provider_config.name} API 响应成功: 耗时 {elapsed_time:.2f}s")

            # 解析响应
            parsed = self.adapter.parse_response(response)

            return LLMResponse(
                content=parsed['content'],
                model=parsed['model'],
                usage=parsed['usage']
            )

        except Exception as e:
            logger.error(f"{self.provider_config.name} API 调用失败: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        计算 Token 数量

        Args:
            text: 输入文本

        Returns:
            int: Token 数量
        """
        try:
            import tiktoken

            # 大多数提供商使用 cl100k_base 编码器（与 GPT-4 相同）
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            return len(tokens)

        except ImportError:
            logger.warning("tiktoken 未安装，使用粗略估算：1 token ≈ 0.75 个中文字符")
            # 粗略估算：中文 1 token ≈ 0.75 个字符，英文 1 token ≈ 4 个字符
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 0.75 + other_chars / 4)
