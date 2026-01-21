"""LLM 提供商配置"""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ProviderConfig:
    """提供商配置"""
    name: str                          # 提供商名称
    base_url: str                      # API 基础URL
    auth_type: str                     # 认证类型 ('api_key', 'bearer', 'custom')
    auth_header: str                   # 认证头名称 (如 'Authorization', 'x-api-key')
    auth_prefix: str = ""              # 认证前缀 (如 'Bearer ')
    is_openai_compatible: bool = False # 是否兼容OpenAI API格式
    import_name: Optional[str] = None  # 需要导入的模块名
    client_class: Optional[str] = None # 客户端类名


# 提供商配置字典
PROVIDER_CONFIGS: Dict[str, ProviderConfig] = {
    'kimi': ProviderConfig(
        name='Kimi (Moonshot)',
        base_url='https://api.moonshot.cn/v1',
        auth_type='api_key',
        auth_header='Authorization',
        auth_prefix='Bearer ',
        is_openai_compatible=True,
        import_name='openai',
        client_class='OpenAI'
    ),
    'glm': ProviderConfig(
        name='GLM (ZhipuAI)',
        base_url='https://open.bigmodel.cn/api/coding/paas/v4',
        auth_type='api_key',
        auth_header='Authorization',
        auth_prefix='Bearer ',
        is_openai_compatible=False,  # 使用专用SDK
        import_name='zhipuai',
        client_class='ZhipuAI'
    ),
    'deepseek': ProviderConfig(
        name='DeepSeek',
        base_url='https://api.deepseek.com/v1',
        auth_type='api_key',
        auth_header='Authorization',
        auth_prefix='Bearer ',
        is_openai_compatible=True,
        import_name='openai',
        client_class='OpenAI'
    ),
    'openai': ProviderConfig(
        name='OpenAI',
        base_url='https://api.openai.com/v1',
        auth_type='api_key',
        auth_header='Authorization',
        auth_prefix='Bearer ',
        is_openai_compatible=True,
        import_name='openai',
        client_class='OpenAI'
    ),
    'anthropic': ProviderConfig(
        name='Anthropic Claude',
        base_url='https://api.anthropic.com/v1',
        auth_type='api_key',
        auth_header='x-api-key',
        auth_prefix='',
        is_openai_compatible=False,
        import_name='anthropic',
        client_class='Anthropic'
    ),
    'gemini': ProviderConfig(
        name='Google Gemini',
        base_url='https://generativelanguage.googleapis.com/v1',
        auth_type='api_key',
        auth_header='x-goog-api-key',
        auth_prefix='',
        is_openai_compatible=False,
        import_name='google.generativeai',
        client_class='genai'
    )
}


def get_provider_config(provider_name: str) -> ProviderConfig:
    """
    获取提供商配置

    Args:
        provider_name: 提供商名称

    Returns:
        ProviderConfig: 提供商配置

    Raises:
        ValueError: 如果提供商不存在
    """
    if provider_name not in PROVIDER_CONFIGS:
        raise ValueError(f"不支持的LLM提供商: {provider_name}。支持的提供商: {list(PROVIDER_CONFIGS.keys())}")
    return PROVIDER_CONFIGS[provider_name]


def get_openai_compatible_providers() -> list:
    """
    获取所有兼容OpenAI API的提供商列表

    Returns:
        list: 提供商名称列表
    """
    return [
        name for name, config in PROVIDER_CONFIGS.items()
        if config.is_openai_compatible
    ]
