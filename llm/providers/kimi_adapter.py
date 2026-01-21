"""Kimi (Moonshot) 适配器"""
from typing import List, Dict, Any
from llm.base import Message
from llm.providers.base_adapter import BaseAdapter


class KimiAdapter(BaseAdapter):
    """Kimi (Moonshot) 适配器 - OpenAI兼容"""

    def format_request(self,
                      messages: List[Message],
                      model: str,
                      temperature: float,
                      max_tokens: int) -> Dict[str, Any]:
        """格式化API请求"""
        return {
            'model': model,
            'messages': [msg.model_dump() for msg in messages],
            'temperature': temperature,
            'max_tokens': max_tokens
        }

    def parse_response(self, response: Any) -> Dict[str, Any]:
        """解析API响应"""
        return {
            'content': response.choices[0].message.content,
            'model': response.model,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        }
