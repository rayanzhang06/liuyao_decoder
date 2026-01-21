"""GLM (ZhipuAI) 适配器"""
from typing import List, Dict, Any
from llm.base import Message
from llm.providers.base_adapter import BaseAdapter


class GLMAdapter(BaseAdapter):
    """GLM 适配器 - 使用专用SDK"""

    def format_request(self,
                      messages: List[Message],
                      model: str,
                      temperature: float,
                      max_tokens: int) -> Dict[str, Any]:
        """格式化API请求"""
        return {
            'model': model,
            'messages': [{'role': msg.role, 'content': msg.content} for msg in messages],
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

    def get_client_init_args(self, api_key: str, **kwargs) -> Dict[str, Any]:
        """获取客户端初始化参数"""
        args = {'api_key': api_key}
        # GLM uses base_url in a different way
        if self.config.base_url:
            args['base_url'] = self.config.base_url
        return args
