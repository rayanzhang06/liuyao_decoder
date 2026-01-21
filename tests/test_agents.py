"""测试 Agent 独立解读功能"""
import os
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_loader import Config
from llm.factory import LLMClientFactory
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

    # 3. 创建 LLM 客户端
    logger.info("\n3. 创建 LLM 客户端...")

    # 为每个 Agent 获取对应的 LLM 客户端配置
    traditional_config = config_loader.get_agent_config("traditional")
    xiangshu_config = config_loader.get_agent_config("xiangshu")
    mangpai_config = config_loader.get_agent_config("mangpai")

    # 获取 LLM 客户端类型
    traditional_llm_type = traditional_config.get("llm_client")
    xiangshu_llm_type = xiangshu_config.get("llm_client")
    mangpai_llm_type = mangpai_config.get("llm_client")

    # 获取 LLM 客户端配置
    traditional_llm_config = config_loader.get_llm_config(traditional_llm_type)
    xiangshu_llm_config = config_loader.get_llm_config(xiangshu_llm_type)
    mangpai_llm_config = config_loader.get_llm_config(mangpai_llm_type)

    # 创建 LLM 客户端实例
    traditional_llm = LLMClientFactory.create(traditional_llm_type, **traditional_llm_config)
    xiangshu_llm = LLMClientFactory.create(xiangshu_llm_type, **xiangshu_llm_config)
    mangpai_llm = LLMClientFactory.create(mangpai_llm_type, **mangpai_llm_config)

    logger.info(f"传统正宗派使用: {traditional_llm.__class__.__name__}")
    logger.info(f"象数派使用: {xiangshu_llm.__class__.__name__}")
    logger.info(f"盲派使用: {mangpai_llm.__class__.__name__}")

    # 4. 创建三个 Agent
    logger.info("\n4. 初始化三个 Agent...")

    # 获取 prompt 文件路径
    prompts_dir = project_root / "prompts"
    traditional_prompt = str(prompts_dir / "traditional.md")
    xiangshu_prompt = str(prompts_dir / "xiangshu.md")
    mangpai_prompt = str(prompts_dir / "mangpai.md")

    # 使用 AgentFactory 创建 Agent
    traditional_agent = AgentFactory.create("traditional", traditional_llm, traditional_prompt)
    xiangshu_agent = AgentFactory.create("xiangshu", xiangshu_llm, xiangshu_prompt)
    mangpai_agent = AgentFactory.create("mangpai", mangpai_llm, mangpai_prompt)

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

    return results


if __name__ == "__main__":
    # 配置日志
    logger.remove()  # 移除默认处理器
    logger.add(sys.stdout, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")

    # 运行测试
    try:
        results = test_agent_interpretation()
        sys.exit(0 if all(r["success"] for r in results) else 1)
    except Exception as e:
        logger.exception(f"测试执行失败: {e}")
        sys.exit(1)
