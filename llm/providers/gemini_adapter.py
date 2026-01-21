"""Google Gemini 适配器"""
from typing import List, Dict, Any
from llm.base import Message
from llm.providers.base_adapter import BaseAdapter


class GeminiAdapter(BaseAdapter):
    """Google Gemini 适配器 - 专用API"""

    def format_request(self,
                      messages: List[Message],
                      model: str,
                      temperature: float,
                      max_tokens: int) -> Dict[str, Any]:
        """格式化API请求"""
        # Gemini uses a different API structure
        # For now, we'll keep the original client implementation
        # This is a placeholder for future unification
        return {
            'model': model,
            'messages': [msg.model_dump() for msg in messages],
            'temperature': temperature,
            'max_tokens': max_tokens
        }

    def parse_response(self, response: Any) -> Dict[str, Any]:
        """解析API响应"""
        # Gemini response parsing
        # This is a placeholder - the actual implementation needs more work
        return {
            'content': str(response.text),
            'model': 'gemini',
            'usage': {
                'prompt_tokens': response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                'completion_tokens': response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                'total_tokens': response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }
        }
