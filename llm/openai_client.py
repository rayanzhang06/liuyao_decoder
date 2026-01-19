"""OpenAI GPT 客户端实现"""
import time
from typing import List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from llm.base import BaseLLMClient, Message, LLMResponse


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT 客户端"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", **kwargs):
        """
        初始化 OpenAI 客户端

        Args:
            api_key: OpenAI API 密钥
            model: 模型名称（默认 gpt-4-turbo-preview）
            **kwargs: 其他配置参数
        """
        super().__init__(api_key, model, **kwargs)

        try:
            import openai
            self.openai = openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("请安装 openai 库: pip install openai")

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
        调用 OpenAI Chat API

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

        # 转换消息格式
        api_messages = [msg.model_dump() for msg in messages]

        logger.info(f"调用 OpenAI API: model={model}, messages={len(messages)}")

        try:
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )

            elapsed_time = time.time() - start_time

            logger.info(f"OpenAI API 响应成功: 耗时 {elapsed_time:.2f}s")

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )

        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        计算 Token 数量

        使用 tiktoken 库进行精确计算

        Args:
            text: 输入文本

        Returns:
            int: Token 数量
        """
        try:
            import tiktoken

            # 获取模型的编码器
            try:
                encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # 如果模型不在编码器列表中，使用 cl100k_base（GPT-4 的编码器）
                encoding = tiktoken.get_encoding("cl100k_base")

            # 计算 token 数量
            tokens = encoding.encode(text)
            return len(tokens)

        except ImportError:
            logger.warning("tiktoken 未安装，使用粗略估算：1 token ≈ 0.75 个中文字符")
            # 粗略估算：中文 1 token ≈ 0.75 个字符，英文 1 token ≈ 4 个字符
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 0.75 + other_chars / 4)
