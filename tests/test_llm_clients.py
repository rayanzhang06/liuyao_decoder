"""测试 LLM 客户端"""
import os
import pytest

from llm.base import Message
from llm.factory import LLMClientFactory
from config.config_loader import Config

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"未设置 {name}，跳过测试")
    return value


@pytest.mark.e2e
def test_kimi_client():
    """测试 Kimi 客户端"""
    api_key = _require_env("KIMI_API_KEY")

    client = LLMClientFactory.create("kimi", api_key=api_key, model="moonshot-v1-8k")
    messages = [Message(role="user", content="你好，请用一句话介绍一下你自己。")]
    response = client.chat(messages)

    assert response.content
    assert response.model

    text = "这是一个测试文本，用于验证 token 计算功能。"
    token_count = client.count_tokens(text)
    assert token_count > 0


@pytest.mark.e2e
def test_glm_client():
    """测试 GLM 客户端"""
    api_key = _require_env("GLM_API_KEY")
    client = LLMClientFactory.create("glm", api_key=api_key, model="glm-4")
    messages = [Message(role="user", content="你好，请用一句话介绍一下你自己。")]
    response = client.chat(messages)

    assert response.content
    assert response.model

    text = "这是一个测试文本，用于验证 token 计算功能。"
    token_count = client.count_tokens(text)
    assert token_count > 0


@pytest.mark.e2e
def test_deepseek_client():
    """测试 DeepSeek 客户端"""
    api_key = _require_env("DEEPSEEK_API_KEY")
    client = LLMClientFactory.create("deepseek", api_key=api_key, model="deepseek-chat")
    messages = [Message(role="user", content="你好，请用一句话介绍一下你自己。")]
    response = client.chat(messages)

    assert response.content
    assert response.model

    text = "这是一个测试文本，用于验证 token 计算功能。"
    token_count = client.count_tokens(text)
    assert token_count > 0


@pytest.mark.e2e
def test_gemini_client():
    """测试 Gemini 客户端"""
    api_key = _require_env("GEMINI_API_KEY")
    client = LLMClientFactory.create("gemini", api_key=api_key, model="gemini-pro")
    messages = [Message(role="user", content="你好，请用一句话介绍一下你自己。")]
    response = client.chat(messages)

    assert response.content
    assert response.model

    text = "这是一个测试文本，用于验证 token 计算功能。"
    token_count = client.count_tokens(text)
    assert token_count > 0


@pytest.mark.e2e
def test_openai_client():
    """测试 OpenAI 客户端"""
    api_key = _require_env("OPENAI_API_KEY")
    client = LLMClientFactory.create("openai", api_key=api_key, model="gpt-4-turbo-preview")
    messages = [Message(role="user", content="你好，请用一句话介绍一下你自己。")]
    response = client.chat(messages)

    assert response.content
    assert response.model

    text = "这是一个测试文本，用于验证 token 计算功能。"
    token_count = client.count_tokens(text)
    assert token_count > 0


@pytest.mark.e2e
def test_anthropic_client():
    """测试 Anthropic 客户端"""
    api_key = _require_env("ANTHROPIC_API_KEY")
    client = LLMClientFactory.create("anthropic", api_key=api_key, model="claude-3-opus-20240229")
    messages = [Message(role="user", content="你好，请用一句话介绍一下你自己。")]
    response = client.chat(messages)

    assert response.content
    assert response.model

    text = "这是一个测试文本，用于验证 token 计算功能。"
    token_count = client.count_tokens(text)
    assert token_count > 0


def test_config_loading():
    """测试配置加载"""
    config = Config()

    assert config.get_default_llm_client()
    assert config.get_debate_config()
    assert config.get_storage_config()

    for agent_name in ["traditional", "xiangshu", "mangpai"]:
        agent_config = config.get_agent_config(agent_name)
        assert agent_config.get("llm_client")
        assert agent_config.get("school")
