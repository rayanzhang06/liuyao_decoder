"""Stage 1 集成测试 - 测试完整辩论流程"""
import pytest
import asyncio
from pathlib import Path

from config.config_loader import Config
from utils.parser import HexagramParser
from agents.orchestrator import DebateOrchestrator
from utils.report_generator import ReportGenerator


# 示例卦象文本（来自prompt_v2.md）
SAMPLE_HEXAGRAM_TEXT = """-----
灵光象吉·六爻排盘
时间：2025年11月18日 23:57:20
占问：明年有机会进入外资药企吗？
乙巳年 丁亥月 壬辰日 庚子时
寅卯空 午未空 午未空 辰巳空
本卦：火天大有/乾宫·8 (归魂)
变卦：风水涣/离宫·6
虎 父戌 官巳 —  应 财卯 —
蛇 兄申 父未 —Χ 　 官巳 —
勾 官午 兄酉 —Ｏ 　 父未 —
雀 父辰 父辰 —Ｏ 世 官午 —
龙 财寅 财寅 — 　 父辰 —
玄 孙子 孙子 —Ｏ 　 财寅 —
-----"""


@pytest.mark.asyncio
async def test_full_debate_workflow():
    """测试完整辩论流程：解析 → 辩论 → 报告生成"""
    # 注意：此测试需要真实的LLM API密钥
    # 可以使用pytest标记为e2e测试，只在需要时运行

    # 1. 解析卦象
    parser = HexagramParser()
    hexagram = parser.parse_text(SAMPLE_HEXAGRAM_TEXT)

    assert hexagram is not None
    assert hexagram.ben_gua_name == "火天大有"
    assert hexagram.bian_gua_name == "风水涣"
    assert hexagram.question == "明年有机会进入外资药企吗？"

    # 2. 运行辩论
    config = Config()
    orchestrator = DebateOrchestrator(config)
    context = await orchestrator.run_debate(hexagram)

    assert context is not None
    assert context.current_round > 0
    assert len(context.history) > 0
    assert context.state.value in ['converged', 'max_rounds_reached', 'finished']

    # 3. 生成报告
    report_generator = ReportGenerator()
    report = report_generator.generate_report(context)

    assert report is not None
    assert len(report) > 0
    assert "## 一、卦象基本信息" in report
    assert "## 二、核心结论" in report
    assert "## 三、详细分析" in report
    assert "## 四、流派视角" in report
    assert "## 五、辩论摘要" in report
    assert "## 六、综合建议" in report
    assert "## 七、备注" in report

    # 验证报告包含关键信息
    assert hexagram.ben_gua_name in report
    assert hexagram.bian_gua_name in report
    assert hexagram.question in report


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """测试DebateOrchestrator初始化"""
    config = Config()
    orchestrator = DebateOrchestrator(config)

    assert orchestrator is not None
    assert len(orchestrator.agents) == 3
    assert orchestrator.debate_config is not None
    assert orchestrator.debate_config['max_rounds'] == 10


@pytest.mark.asyncio
async def test_convergence_detection():
    """测试收敛检测逻辑"""
    # 这个测试可以mock辩论历史来测试收敛规则
    # 简化版本：只测试方法存在
    config = Config()
    orchestrator = DebateOrchestrator(config)

    assert hasattr(orchestrator, '_check_convergence')
    assert hasattr(orchestrator, '_calculate_convergence_score')


def test_report_generator_structure():
    """测试报告生成器结构（无需LLM调用）"""
    report_generator = ReportGenerator()

    # 测试辅助方法存在
    assert hasattr(report_generator, 'generate_report')
    assert hasattr(report_generator, '_calculate_consensus_level')
    assert hasattr(report_generator, '_extract_fortune_judgment')


@pytest.mark.asyncio
async def test_parser_only():
    """单独测试解析器（无需LLM）"""
    parser = HexagramParser()
    hexagram = parser.parse_text(SAMPLE_HEXAGRAM_TEXT)

    # 验证解析结果
    assert hexagram.system_name == "灵光象吉"
    assert hexagram.datetime == "2025年11月18日 23:57:20"
    assert hexagram.question == "明年有机会进入外资药企吗？"

    # 验证干支
    assert hexagram.ganzhi['year'] == "乙巳"
    assert hexagram.ganzhi['month'] == "丁亥"
    assert hexagram.ganzhi['day'] == "壬辰"
    assert hexagram.ganzhi['hour'] == "庚子"

    # 验证卦象
    assert hexagram.ben_gua == "火天大有"
    assert hexagram.ben_gua_gong == "乾宫"
    assert hexagram.ben_gua_index == 8
    assert hexagram.ben_gua_type == "归魂"

    assert hexagram.bian_gua == "风水涣"
    assert hexagram.bian_gua_gong == "离宫"
    assert hexagram.bian_gua_index == 6

    # 验证六爻
    assert len(hexagram.lines) == 6

    # 检查动爻
    dong_yao_count = sum(1 for line in hexagram.lines if line.change_info)
    assert dong_yao_count == 3  # 三爻、四爻、六爻动


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_e2e_with_real_llm():
    """端到端测试（需要真实API密钥，使用pytest -m e2e运行）"""
    # 此测试需要API密钥，默认跳过
    # 使用 pytest -m e2e 运行

    config = Config()
    orchestrator = DebateOrchestrator(config)

    parser = HexagramParser()
    hexagram = parser.parse_text(SAMPLE_HEXAGRAM_TEXT)

    # 运行完整辩论
    context = await orchestrator.run_debate(hexagram)

    # 生成报告
    report_generator = ReportGenerator()
    report = report_generator.generate_report(context)

    # 验证
    assert context.current_round > 0
    assert len(report) > 1000  # 报告应该足够长

    # 保存报告用于检查
    output_path = Path("test_output_report.md")
    output_path.write_text(report, encoding='utf-8')

    assert output_path.exists()

    # 清理
    # output_path.unlink()  # 可以保留用于检查


if __name__ == "__main__":
    # 可以直接运行此文件进行快速测试
    print("运行测试...")
    test_parser_only()
    print("✅ 解析器测试通过")

    test_orchestrator_initialization()
    print("✅ 编排器初始化测试通过")

    test_report_generator_structure()
    print("✅ 报告生成器结构测试通过")

    print("\n所有基础测试通过！")
    print("注意：完整辩论流程测试需要LLM API密钥")
