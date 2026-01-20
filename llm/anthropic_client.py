"""Anthropic Claude 客户端实现"""
import time
from typing import List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from llm.base import BaseLLMClient, Message, LLMResponse


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude 客户端"""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", **kwargs):
        """
        初始化 Anthropic 客户端

        Args:
            api_key: Anthropic API 密钥
            model: 模型名称（默认 claude-3-opus-20240229）
            **kwargs: 其他配置参数（timeout, http_proxy, https_proxy）
        """
        super().__init__(api_key, model, **kwargs)

        try:
            import anthropic
            from anthropic import Anthropic, DefaultHttpxClient

            self.anthropic = anthropic

            # 配置代理
            proxies = {}
            if self.http_proxy:
                proxies["http://"] = self.http_proxy
            if self.https_proxy:
                proxies["https://"] = self.https_proxy

            # 创建 httpx 客户端
            if proxies:
                import httpx
                http_client = httpx.Client(proxies=proxies, timeout=self.timeout)
                logger.info(f"Anthropic 客户端使用代理: {proxies}")
                self.client = Anthropic(api_key=api_key, http_client=http_client)
            else:
                self.client = Anthropic(api_key=api_key, max_retries=3, timeout=self.timeout)

        except ImportError:
            raise ImportError("请安装 anthropic 库: pip install anthropic")

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
        调用 Anthropic Claude API

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

        # Claude 需要特殊处理 system 消息
        system_message = None
        user_messages = []

        for msg in messages:
            if msg.role == "system":
                # 提取所有 system 消息并合并
                if system_message is None:
                    system_message = msg.content
                else:
                    system_message += "\n\n" + msg.content
            else:
                user_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        logger.info(f"调用 Anthropic API: model={model}, messages={len(messages)}")

        try:
            start_time = time.time()

            # 构建请求参数
            request_params = {
                "model": model,
                "messages": user_messages,
                "max_tokens": max_tokens,
                "timeout": self.timeout
            }

            # 只有在有 system 消息时才添加 system 参数
            if system_message:
                request_params["system"] = system_message

            response = self.client.messages.create(**request_params)

            elapsed_time = time.time() - start_time

            logger.info(f"Anthropic API 响应成功: 耗时 {elapsed_time:.2f}s")

            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            )

        except Exception as e:
            logger.error(f"Anthropic API 调用失败: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        计算 Token 数量

        Claude 使用特殊的 token 计算方式

        Args:
            text: 输入文本

        Returns:
            int: Token 数量
        """
        try:
            import anthropic

            # 使用 Anthropic 的 token 计算器
            # 注意：这个方法可能在某些版本的 anthropic 库中不可用
            return self.client.count_tokens(text)

        except (ImportError, AttributeError):
            logger.warning("无法使用 anthropic 的 token 计算器，使用粗略估算")
            # 粗略估算：中文 1 token ≈ 0.75 个字符，英文 1 token ≈ 4 个字符
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 0.75 + other_chars / 4)
