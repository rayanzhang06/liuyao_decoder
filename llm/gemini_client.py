"""Google Gemini 客户端实现"""
import time
from typing import List, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from llm.base import BaseLLMClient, Message, LLMResponse


class GeminiClient(BaseLLMClient):
    """Google Gemini 客户端"""

    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        """
        初始化 Gemini 客户端

        Args:
            api_key: Google API 密钥
            model: 模型名称（默认 gemini-pro）
            **kwargs: 其他配置参数
        """
        super().__init__(api_key, model, **kwargs)

        try:
            import google.generativeai as genai
            self.genai = genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("请安装 google-generativeai 库: pip install google-generativeai")

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
        调用 Gemini Chat API

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

        logger.info(f"调用 Gemini API: model={model}, messages={len(messages)}")

        try:
            start_time = time.time()

            # Gemini 需要特殊的消息格式处理
            # 提取 system 消息并作为指令
            system_instruction = None
            chat_history = []
            user_message = None

            for msg in messages:
                if msg.role == "system":
                    # 合并所有 system 消息
                    if system_instruction is None:
                        system_instruction = msg.content
                    else:
                        system_instruction += "\n\n" + msg.content
                elif msg.role == "user":
                    # 最后一个 user 消息作为当前输入
                    user_message = msg.content
                elif msg.role == "assistant":
                    # assistant 消息作为历史
                    chat_history.append({
                        "role": "model",
                        "parts": [msg.content]
                    })

            # 如果有 system instruction，重新创建模型
            if system_instruction:
                self.client = self.genai.GenerativeModel(
                    model,
                    system_instruction=system_instruction
                )

            # 创建聊天会话
            if chat_history:
                chat = self.client.start_chat(history=chat_history)
            else:
                chat = self.client.start_chat()

            # 生成配置
            generation_config = self.genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # 发送消息
            response = chat.send_message(
                user_message,
                generation_config=generation_config
            )

            elapsed_time = time.time() - start_time

            logger.info(f"Gemini API 响应成功: 耗时 {elapsed_time:.2f}s")

            # Gemini 的 token 统计可能不可用
            return LLMResponse(
                content=response.text,
                model=model,
                usage={
                    "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                    "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
                }
            )

        except Exception as e:
            logger.error(f"Gemini API 调用失败: {e}")
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
            # 使用 Gemini 的 token 计数器
            return self.client.count_tokens(text).total_tokens
        except Exception as e:
            logger.warning(f"Gemini token 计算失败: {e}，使用粗略估算")
            # 粗略估算：中文 1 token ≈ 0.75 个字符，英文 1 token ≈ 4 个字符
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 0.75 + other_chars / 4)
