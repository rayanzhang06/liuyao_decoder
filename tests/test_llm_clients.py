"""测试 LLM 客户端"""
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.base import Message
from llm.factory import LLMClientFactory
from config.config_loader import Config

# 加载环境变量
load_dotenv()


def test_kimi_client():
    """测试 Kimi 客户端"""
    api_key = os.getenv("KIMI_API_KEY")

    if not api_key:
        print("⚠️  跳过 Kimi 测试：未设置 KIMI_API_KEY")
        return

    print("\n" + "="*50)
    print("测试 Kimi 客户端")
    print("="*50)

    try:
        client = LLMClientFactory.create("kimi", api_key=api_key, model="moonshot-v1-8k")

        messages = [
            Message(role="user", content="你好，请用一句话介绍一下你自己。")
        ]

        response = client.chat(messages)

        print(f"✅ Kimi API 调用成功")
        print(f"模型: {response.model}")
        print(f"响应: {response.content[:100]}...")
        print(f"Token 使用: {response.usage}")

        # 测试 token 计算
        text = "这是一个测试文本，用于验证 token 计算功能。"
        token_count = client.count_tokens(text)
        print(f"Token 计算: '{text}' -> {token_count} tokens")

    except Exception as e:
        print(f"❌ Kimi 测试失败: {e}")


def test_glm_client():
    """测试 GLM 客户端"""
    api_key = os.getenv("GLM_API_KEY")

    if not api_key:
        print("⚠️  跳过 GLM 测试：未设置 GLM_API_KEY")
        return

    print("\n" + "="*50)
    print("测试 GLM 客户端")
    print("="*50)

    try:
        client = LLMClientFactory.create("glm", api_key=api_key, model="glm-4")

        messages = [
            Message(role="user", content="你好，请用一句话介绍一下你自己。")
        ]

        response = client.chat(messages)

        print(f"✅ GLM API 调用成功")
        print(f"模型: {response.model}")
        print(f"响应: {response.content[:100]}...")
        print(f"Token 使用: {response.usage}")

        # 测试 token 计算
        text = "这是一个测试文本，用于验证 token 计算功能。"
        token_count = client.count_tokens(text)
        print(f"Token 计算: '{text}' -> {token_count} tokens")

    except Exception as e:
        print(f"❌ GLM 测试失败: {e}")


def test_deepseek_client():
    """测试 DeepSeek 客户端"""
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        print("⚠️  跳过 DeepSeek 测试：未设置 DEEPSEEK_API_KEY")
        return

    print("\n" + "="*50)
    print("测试 DeepSeek 客户端")
    print("="*50)

    try:
        client = LLMClientFactory.create("deepseek", api_key=api_key, model="deepseek-chat")

        messages = [
            Message(role="user", content="你好，请用一句话介绍一下你自己。")
        ]

        response = client.chat(messages)

        print(f"✅ DeepSeek API 调用成功")
        print(f"模型: {response.model}")
        print(f"响应: {response.content[:100]}...")
        print(f"Token 使用: {response.usage}")

        # 测试 token 计算
        text = "这是一个测试文本，用于验证 token 计算功能。"
        token_count = client.count_tokens(text)
        print(f"Token 计算: '{text}' -> {token_count} tokens")

    except Exception as e:
        print(f"❌ DeepSeek 测试失败: {e}")


def test_gemini_client():
    """测试 Gemini 客户端"""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("⚠️  跳过 Gemini 测试：未设置 GEMINI_API_KEY")
        return

    print("\n" + "="*50)
    print("测试 Gemini 客户端")
    print("="*50)

    try:
        client = LLMClientFactory.create("gemini", api_key=api_key, model="gemini-pro")

        messages = [
            Message(role="user", content="你好，请用一句话介绍一下你自己。")
        ]

        response = client.chat(messages)

        print(f"✅ Gemini API 调用成功")
        print(f"模型: {response.model}")
        print(f"响应: {response.content[:100]}...")
        print(f"Token 使用: {response.usage}")

        # 测试 token 计算
        text = "这是一个测试文本，用于验证 token 计算功能。"
        token_count = client.count_tokens(text)
        print(f"Token 计算: '{text}' -> {token_count} tokens")

    except Exception as e:
        print(f"❌ Gemini 测试失败: {e}")


def test_openai_client():
    """测试 OpenAI 客户端"""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("⚠️  跳过 OpenAI 测试：未设置 OPENAI_API_KEY")
        return

    print("\n" + "="*50)
    print("测试 OpenAI 客户端")
    print("="*50)

    try:
        client = LLMClientFactory.create("openai", api_key=api_key, model="gpt-4-turbo-preview")

        messages = [
            Message(role="user", content="你好，请用一句话介绍一下你自己。")
        ]

        response = client.chat(messages)

        print(f"✅ OpenAI API 调用成功")
        print(f"模型: {response.model}")
        print(f"响应: {response.content[:100]}...")
        print(f"Token 使用: {response.usage}")

        # 测试 token 计算
        text = "这是一个测试文本，用于验证 token 计算功能。"
        token_count = client.count_tokens(text)
        print(f"Token 计算: '{text}' -> {token_count} tokens")

    except Exception as e:
        print(f"❌ OpenAI 测试失败: {e}")


def test_anthropic_client():
    """测试 Anthropic 客户端"""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("⚠️  跳过 Anthropic 测试：未设置 ANTHROPIC_API_KEY")
        return

    print("\n" + "="*50)
    print("测试 Anthropic 客户端")
    print("="*50)

    try:
        client = LLMClientFactory.create("anthropic", api_key=api_key, model="claude-3-opus-20240229")

        messages = [
            Message(role="user", content="你好，请用一句话介绍一下你自己。")
        ]

        response = client.chat(messages)

        print(f"✅ Anthropic API 调用成功")
        print(f"模型: {response.model}")
        print(f"响应: {response.content[:100]}...")
        print(f"Token 使用: {response.usage}")

        # 测试 token 计算
        text = "这是一个测试文本，用于验证 token 计算功能。"
        token_count = client.count_tokens(text)
        print(f"Token 计算: '{text}' -> {token_count} tokens")

    except Exception as e:
        print(f"❌ Anthropic 测试失败: {e}")


def test_config_loading():
    """测试配置加载"""
    print("\n" + "="*50)
    print("测试配置加载")
    print("="*50)

    try:
        config = Config()

        print(f"✅ 配置文件加载成功")
        print(f"默认 LLM 客户端: {config.get_default_llm_client()}")
        print(f"辩论配置: {config.get_debate_config()}")
        print(f"存储配置: {config.get_storage_config()}")

        # 测试获取各 Agent 配置
        for agent_name in ["traditional", "xiangshu", "mangpai"]:
            agent_config = config.get_agent_config(agent_name)
            print(f"  {agent_name}: {agent_config['llm_client']} - {agent_config['school']}")

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("六爻解读多 Agent 系统 - LLM 客户端测试")
    print("="*50)

    # 测试配置加载
    test_config_loading()

    # 测试各个 LLM 客户端（优先测试国内模型）
    test_kimi_client()
    test_glm_client()
    test_deepseek_client()
    test_gemini_client()
    test_openai_client()
    test_anthropic_client()

    print("\n" + "="*50)
    print("测试完成")
    print("="*50)
    print("\n提示：")
    print("1. 如果看到 '⚠️  跳过 xxx 测试'，请在 .env 文件中配置相应的 API_KEY")
    print("2. 如果看到 '✅ API 调用成功'，说明该客户端工作正常")
    print("3. 如果看到 '❌ 测试失败'，请检查 API_KEY 是否正确")
    print("4. 国内推荐使用 Kimi、GLM 或 DeepSeek（无需代理）")
