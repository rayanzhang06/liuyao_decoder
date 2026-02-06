"""测试 Agent 独立解读功能"""
import os
from loguru import logger
import pytest

from config.config_loader import Config
from agents.agent_factory import AgentFactory
from utils.parser import HexagramParser


# 示例卦象文本（来自真实卦象）
SAMPLE_HEXAGRAM_TEXT = """
文王·六爻排盘
时间：2025年01月19日 12:00
占问：我能否在近期内找到满意的工作？

甲辰年  丁丑月  乙未日  壬午时
戌亥空    寅卯空    辰巳空    寅卯空

本卦：火天大有/乾宫·8 (归魂)
变卦：风水涣/离宫·6

六爻：
青龙 官巳 — 世
玄武 财未 —
白虎 父辰 —
螣蛇 财卯 — 应
勾陈 官巳 —
朱雀 父未 —
"""


@pytest.mark.e2e
def test_agent_interpretation():
    """测试三个 Agent 的独立解读功能"""

    logger.info("=" * 60)
    logger.info("开始测试 Agent 独立解读功能")
    logger.info("=" * 60)

    # 1. 加载配置
    logger.info("\n1. 加载配置...")
    config_loader = Config()
    logger.info(f"默认 LLM 客户端: {config_loader.get_default_llm_client()}")

    # 2. 解析卦象文本
    logger.info("\n2. 解析卦象文本...")
    parser = HexagramParser()
    hexagram = parser.parse_text(SAMPLE_HEXAGRAM_TEXT)
    logger.info(f"卦象解析成功: {hexagram.ben_gua_name} → {hexagram.bian_gua_name}")
    logger.info(f"问题: {hexagram.question}")

    # 3. 检查环境变量
    agent_types = ["traditional", "xiangshu", "mangpai"]
    required_envs = set()
    for agent_type in agent_types:
        llm_client = config_loader.get_agent_config(agent_type).get("llm_client")
        if llm_client:
            key_name = f"{llm_client.upper()}_API_KEY"
            required_envs.add(key_name)

    missing = [name for name in required_envs if not os.getenv(name)]
    if missing:
        pytest.skip(f"缺少 API Key: {', '.join(sorted(missing))}")

    # 4. 创建三个 Agent（使用统一工厂）
    logger.info("\n4. 初始化三个 Agent...")
    traditional_agent = AgentFactory.create_from_config(config_loader, "traditional")
    xiangshu_agent = AgentFactory.create_from_config(config_loader, "xiangshu")
    mangpai_agent = AgentFactory.create_from_config(config_loader, "mangpai")

    logger.info("✓ 所有 Agent 初始化完成")

    # 5. 执行独立解读
    logger.info("\n5. 执行独立解读...")
    logger.info("=" * 60)

    agents = [
        ("传统正宗派", traditional_agent),
        ("象数派", xiangshu_agent),
        ("盲派", mangpai_agent)
    ]

    results = []

    for school_name, agent in agents:
        logger.info(f"\n【{school_name}】正在解读...")
        try:
            response = agent.interpret(hexagram)
            results.append({
                "school": school_name,
                "response": response,
                "success": True
            })

            logger.info(f"✓ {school_name} 解读完成")
            logger.info(f"  置信度: {response.confidence}/10")
            logger.info(f"  模型: {response.metadata.get('model', 'unknown')}")
            usage = response.metadata.get('usage', {})
            logger.info(f"  Token 使用: {usage.get('total_tokens', 'unknown')}")

            # 显示部分内容
            content_lines = response.content.split('\n')[:10]
            logger.info(f"  内容预览:")
            for line in content_lines:
                logger.info(f"    {line}")

        except Exception as e:
            logger.error(f"✗ {school_name} 解读失败: {e}")
            results.append({
                "school": school_name,
                "response": None,
                "success": False,
                "error": str(e)
            })

    # 6. 总结结果
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)

    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)

    logger.info(f"\n成功: {success_count}/{total_count}")

    for result in results:
        if result["success"]:
            logger.info(f"✓ {result['school']}: 置信度 {result['response'].confidence}/10")
        else:
            logger.info(f"✗ {result['school']}: {result.get('error', '未知错误')}")

    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)

    assert all(r["success"] for r in results)
