"""Anthropic Claude 适配器"""
from typing import List, Dict, Any
from llm.base import Message
from llm.providers.base_adapter import BaseAdapter


class AnthropicAdapter(BaseAdapter):
    """Anthropic Claude 适配器 - 专用API"""

    def format_request(self,
                      messages: List[Message],
                      model: str,
                      temperature: float,
                      max_tokens: int) -> Dict[str, Any]:
        """格式化API请求"""
        # Anthropic API uses different message format
        # Separate system message from user/assistant messages
        system_message = None
        api_messages = []

        for msg in messages:
            if msg.role == 'system':
                system_message = msg.content
            else:
                api_messages.append({'role': msg.role, 'content': msg.content})

        request_params = {
            'model': model,
            'messages': api_messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }

        if system_message:
            request_params['system'] = system_message

        return request_params

    def parse_response(self, response: Any) -> Dict[str, Any]:
        """解析API响应"""
        return {
            'content': response.content[0].text,
            'model': response.model,
            'usage': {
                'prompt_tokens': response.usage.input_tokens,
                'completion_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
        }
