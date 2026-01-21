"""报告生成器 - 生成符合prompt_v2.md规范的最终解读报告"""
import re
import json
from typing import Dict, List, Any, Optional
from loguru import logger

from storage.models import DebateContext, SchoolType, AgentResponse


class ReportGenerator:
    """报告生成器 - 将辩论结果转换为结构化的markdown报告"""

    def __init__(self):
        """初始化报告生成器"""
        pass

    def generate_report(self, context: DebateContext) -> str:
        """
        生成最终markdown报告

        重最终结论及解析，轻辩论过程

        Args:
            context: 辩论上下文

        Returns:
            str: Markdown格式的报告
        """
        sections = []

        # 一、卦象基本信息（简洁）
        sections.append(self._generate_section_1(context))

        # 二、核心结论（强化，作为报告主体）
        sections.append(self._generate_section_2(context))

        # 三、详细解析（基于最终一致观点）
        sections.append(self._generate_section_3(context))

        # 四、综合建议（强化）
        sections.append(self._generate_section_4(context))

        # 五、备注（简化）
        sections.append(self._generate_section_5(context))

        report = '\n\n'.join(sections)

        return report

    def _generate_section_1(self, context: DebateContext) -> str:
        """生成第一部分：卦象基本信息"""
        hexagram = context.hexagram

        # 统计动爻数量
        dong_yao_count = sum(1 for line in hexagram.lines if line.change_info)

        return f"""## 一、卦象基本信息

**卦名变换**：{hexagram.ben_gua_name} → {hexagram.bian_gua_name}

**问卜时间**：{hexagram.datetime}

**问题**：{hexagram.question}

**卦象结构**：
- 本卦：{hexagram.ben_gua}（{hexagram.ben_gua_gong}宫·第{hexagram.ben_gua_index}卦 - {hexagram.ben_gua_type}）
- 变卦：{hexagram.bian_gua}（{hexagram.bian_gua_gong}宫·第{hexagram.bian_gua_index}卦）
- 动爻：{dong_yao_count}个
"""

    def _generate_section_2(self, context: DebateContext) -> str:
        """生成第二部分：核心结论（强化版）"""
        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)

        # 计算共识度
        consensus_level = self._calculate_consensus_level(responses)

        # 提取主流观点（综合各流派的判断）
        mainstream_judgment = self._extract_mainstream_judgment(responses)
        mainstream_timing = self._extract_mainstream_timing(responses)
        mainstream_rationale = self._extract_mainstream_rationale(responses)

        return f"""## 二、核心结论

### 2.1 综合判断

**【共识度：{consensus_level}】**

{mainstream_judgment}

**核心依据**：
{mainstream_rationale}

### 2.2 应期推断

{mainstream_timing}

### 2.3 关键建议

{self._extract_key_suggestions(responses)}
"""

    def _generate_section_3(self, context: DebateContext) -> str:
        """生成第三部分：详细解析（基于最终一致观点）"""
        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)
        hexagram = context.hexagram

        content = "## 三、详细解析\n\n"

        # 3.1 用神分析
        content += "### 3.1 用神分析\n\n"
        content += self._extract_integrated_yongshen_analysis(responses) + "\n\n"

        # 3.2 动爻解析
        dong_yao_lines = [line for line in hexagram.lines if line.change_info]
        if dong_yao_lines:
            content += "### 3.2 动爻解析\n\n"
            for line in dong_yao_lines:
                content += f"**{line.position}爻**（{line.liuqin}·{line.wuxing}）：\n\n"
                content += self._extract_integrated_dongyao_analysis(responses, line) + "\n\n"

        # 3.3 卦象结构分析
        content += "### 3.3 卦象结构分析\n\n"
        content += self._extract_integrated_structure_analysis(responses, hexagram) + "\n\n"

        return content

    def _generate_section_4(self, context: DebateContext) -> str:
        """生成第四部分：综合建议（强化版）"""
        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)

        content = "## 四、综合建议\n\n"

        # 4.1 短期行动
        content += "### 4.1 短期行动（1-3个月）\n\n"
        content += self._extract_short_term_suggestions(responses) + "\n\n"

        # 4.2 中期规划
        content += "### 4.2 中期规划（3-6个月）\n\n"
        content += self._extract_mid_term_plans(responses) + "\n\n"

        # 4.3 风险提示
        content += "### 4.3 风险提示\n\n"
        content += self._extract_risk_warnings(responses) + "\n\n"

        # 4.4 宜忌建议
        content += "### 4.4 宜忌建议\n\n"
        content += "**宜**：\n"
        content += self._extract_recommendations(responses, 'dos') + "\n\n"
        content += "**忌**：\n"
        content += self._extract_recommendations(responses, 'donts') + "\n"

        return content

    def _generate_section_5(self, context: DebateContext) -> str:
        """生成第五部分：备注（简化版）"""
        consensus_level = self._calculate_overall_consensus(context)

        return f"""## 五、备注

**报告说明**：
- 本报告基于传统正宗派、象数派、盲派三流派的综合分析
- 共经历 {context.current_round} 轮辩论迭代
- 整体共识度：{consensus_level}
- 收敛分数：{context.convergence_score:.2f}

**特别说明**：
本报告仅供参考，提供的是趋势分析。具体结果还需看个人努力与实际行动。建议结合自身实际情况，理性参考，勿过度依赖。
"""

    # ==================== 辅助方法 ====================

    def _extract_mainstream_judgment(self, responses: List[AgentResponse]) -> str:
        """提取主流吉凶判断（综合各流派观点）"""
        # 提取所有流派的判断
        judgments = []
        for resp in responses:
            judgment = self._extract_fortune_judgment(resp.content)
            school_name = self._get_school_chinese_name(resp.school)
            judgments.append(f"- **{school_name}**：{judgment}（置信度 {resp.confidence}/10）")

        # 尝试生成综合判断
        avg_confidence = sum(r.confidence for r in responses) / len(responses)
        if avg_confidence > 7.0:
            overall = "**总体判断**：吉\n\n"
        elif avg_confidence > 5.0:
            overall = "**总体判断**：中平\n\n"
        else:
            overall = "**总体判断**：需谨慎\n\n"

        return overall + "各流派观点：\n" + '\n'.join(judgments)

    def _extract_mainstream_timing(self, responses: List[AgentResponse]) -> str:
        """提取主流应期判断"""
        timings = []
        for resp in responses:
            timing = self._extract_timing(resp.content)
            school_name = self._get_school_chinese_name(resp.school)
            timings.append(f"- **{school_name}**：{timing}")

        # 尝试找到共同时间点
        return '\n'.join(timings)

    def _extract_mainstream_rationale(self, responses: List[AgentResponse]) -> str:
        """提取主流判断依据"""
        rationales = []
        for resp in responses:
            key_points = self._extract_key_points(resp.content)
            if key_points:
                rationales.append(f"- {key_points}")

        if rationales:
            # 合并相似的论点
            unique_points = list(set(rationales))
            return '\n'.join(unique_points[:5])  # 最多5个要点
        return "- 各流派观点较为一致，均认为卦象显示出明确的趋势"

    def _extract_key_suggestions(self, responses: List[AgentResponse]) -> str:
        """提取关键建议（优先展示共识建议）"""
        # 提取共同建议
        common = self._extract_common_suggestions(responses)

        # 提取流派特色建议
        school_specific = []
        for resp in responses:
            suggestion = self._extract_suggestion(resp.content)
            school_name = self._get_school_chinese_name(resp.school)
            if suggestion and suggestion != "根据实际情况灵活应对":
                school_specific.append(f"- **{school_name}**：{suggestion}")

        result = common
        if school_specific:
            result += "\n\n**流派特色建议**：\n" + '\n'.join(school_specific[:2])  # 最多2个

        return result

    def _extract_integrated_yongshen_analysis(self, responses: List[AgentResponse]) -> str:
        """提取综合用神分析"""
        analyses = []
        for resp in responses:
            analysis = self._extract_yongshen_analysis(resp.content)
            school_name = self._get_school_chinese_name(resp.school)
            if analysis and analysis != "（详见完整分析）":
                analyses.append(f"{analysis}")

        if analyses:
            # 合并用神分析
            unique_analyses = list(set(analyses))
            return '\n\n'.join(unique_analyses)
        return "各流派对用神选取有不同侧重，综合来看应关注核心要素的生克制化关系。"

    def _extract_integrated_dongyao_analysis(self, responses: List[AgentResponse], line) -> str:
        """提取综合动爻分析"""
        analyses = []
        for resp in responses:
            # 尝试从内容中提取对该动爻的分析
            if str(line.position) in resp.content or line.wuxing in resp.content:
                # 提取相关段落
                lines_list = resp.content.split('\n')
                for i, l in enumerate(lines_list):
                    if str(line.position) in l or line.wuxing in l:
                        # 提取前后几行
                        segment = '\n'.join(lines_list[max(0, i-1):min(len(lines_list), i+3)])
                        analyses.append(f"- {segment.strip()}")
                        break

        if analyses:
            return '\n'.join(analyses[:3])  # 最多3个要点
        return f"- 关注该爻的五行生克关系\n- 结合世应位置判断影响\n- 考虑其在整体卦象中的作用"

    def _extract_integrated_structure_analysis(self, responses: List[AgentResponse], hexagram) -> str:
        """提取综合卦象结构分析"""
        # 提取各流派的结构分析
        structure_points = []

        # 从各流派响应中提取结构相关信息
        for resp in responses:
            content = resp.content
            # 查找关键词
            keywords = ['世应', '六神', '卦宫', '五行']
            for keyword in keywords:
                if keyword in content:
                    lines_list = content.split('\n')
                    for i, line in enumerate(lines_list):
                        if keyword in line:
                            structure_points.append(f"- {line.strip()}")
                            break

        if structure_points:
            unique_points = list(set(structure_points))
            return '\n'.join(unique_points[:5])  # 最多5个要点
        return f"""- **世应关系**：{hexagram.ben_gua_name}中世应位置显示出特定的关系模式
- **卦宫属性**：本卦属于{hexagram.ben_gua_gong}宫，具有该宫的五行特性
- **整体格局**：结合动爻变化，整体卦象呈现出动态平衡"""

    def _analyze_consensus(self, context: DebateContext) -> Dict[str, Any]:
        """分析共识情况"""
        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)

        confidences = [r.confidence for r in responses]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences) if confidences else 0.0

        return {
            'avg_confidence': avg_confidence,
            'variance': variance,
            'consensus_points': [],
            'mainstream_views': [],
            'disagreements': []
        }

    def _calculate_consensus_level(self, responses: List[AgentResponse]) -> str:
        """计算共识度等级"""
        confidences = [r.confidence for r in responses]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences) if confidences else 0.0

        if avg_confidence > 7.5 and variance < 1.0:
            return "高 ⭐⭐⭐⭐⭐"
        elif avg_confidence > 6.0 and variance < 2.0:
            return "中 ⭐⭐⭐"
        else:
            return "低 ⭐⭐"

    def _calculate_timing_consensus(self, responses: List[AgentResponse]) -> str:
        """计算应期判断的共识度"""
        # 简化版本：检查应期是否相似
        return "中等"  # 实际应解析应期并比较

    def _extract_fortune_judgment(self, content: str) -> str:
        """从内容中提取吉凶判断"""
        # 尝试多种模式匹配
        patterns = [
            r'吉凶判断[：:]\s*([^\n]+)',
            r'结论[：:]\s*([^\n]+)',
            r'判断[：:]\s*([^\n]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                judgment = match.group(1).strip()
                # 限制长度
                if len(judgment) > 50:
                    return judgment[:50] + "..."
                return judgment

        return "详见分析"

    def _extract_consensus_reasons(self, responses: List[AgentResponse]) -> str:
        """提取共识依据"""
        reasons = []
        for resp in responses:
            # 提取关键论点
            key_points = self._extract_key_points(resp.content)
            if key_points:
                school_name = self._get_school_chinese_name(resp.school)
                reasons.append(f"- {school_name}: {key_points}")

        return '\n'.join(reasons) if reasons else "- 各流派观点较为一致"

    def _generate_timing_table(self, responses: List[AgentResponse]) -> str:
        """生成应期判断表格"""
        table_rows = []
        for resp in responses:
            timing = self._extract_timing(resp.content)
            school_name = self._get_school_chinese_name(resp.school)
            table_rows.append(f"| {school_name} | {timing} | {resp.confidence}/10 |")
        return '\n'.join(table_rows)

    def _extract_common_suggestions(self, responses: List[AgentResponse]) -> str:
        """提取共同建议"""
        # 简化版本：从各流派建议中提取共同点
        return "- 主动把握机会\n- 注意时机选择"

    def _extract_school_specific_suggestions(self, responses: List[AgentResponse]) -> str:
        """提取流派特色建议"""
        suggestions = []
        for resp in responses:
            school_name = self._get_school_chinese_name(resp.school)
            suggestion = self._extract_suggestion(resp.content)
            suggestions.append(f"- **{school_name}**：{suggestion}")
        return '\n'.join(suggestions)

    def _extract_yongshen_analysis(self, content: str) -> str:
        """提取用神分析"""
        if '用神' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '用神' in line:
                    # 提取用神相关段落
                    return '\n'.join(lines[max(0, i-1):min(len(lines), i+5)])
        return "（详见完整分析）"

    def _track_confidence_history(self, context: DebateContext) -> Dict[SchoolType, List[float]]:
        """追踪置信度历史"""
        history = {SchoolType.TRADITIONAL: [], SchoolType.XIANGSHU: [], SchoolType.MANGPAI: []}

        for round_data in context.history:
            for resp in round_data.get('responses', []):
                # 获取school
                school_str = resp.get('school', resp.get('agent_name', ''))
                if isinstance(school_str, str):
                    if 'traditional' in school_str.lower():
                        history[SchoolType.TRADITIONAL].append(resp.get('confidence', 0.0))
                    elif 'xiangshu' in school_str.lower():
                        history[SchoolType.XIANGSHU].append(resp.get('confidence', 0.0))
                    elif 'mangpai' in school_str.lower():
                        history[SchoolType.MANGPAI].append(resp.get('confidence', 0.0))

        return history

    def _extract_short_term_suggestions(self, responses: List[AgentResponse]) -> str:
        """提取短期建议"""
        suggestions = []
        for resp in responses:
            if '建议' in resp.content:
                # 提取建议部分
                lines = resp.content.split('\n')
                for i, line in enumerate(lines):
                    if '建议' in line:
                        return '\n'.join(lines[i:min(i+5, len(lines))])
        return "- 积极准备\n- 把握时机"

    def _extract_mid_term_plans(self, responses: List[AgentResponse]) -> str:
        """提取中期规划"""
        return "- 根据应期判断，在关键时间窗口重点行动\n- 持续关注机会"

    def _extract_risk_warnings(self, responses: List[AgentResponse]) -> str:
        """提取风险提示"""
        warnings = []
        for resp in responses:
            if '风险' in resp.content or '注意' in resp.content:
                lines = resp.content.split('\n')
                for line in lines:
                    if '风险' in line or '注意' in line:
                        warnings.append(f"- {line.strip()}")
        return '\n'.join(warnings) if warnings else "- 注意细节，谨慎决策"

    def _extract_recommendations(self, responses: List[AgentResponse], rec_type: str) -> str:
        """提取建议（宜/忌）"""
        if rec_type == 'dos':
            return "- 主动出击\n- 把握时机\n- 仔细准备"
        else:  # donts
            return "- 犹豫拖延\n- 过度焦虑\n- 盲目行动"

    def _extract_timing(self, content: str) -> str:
        """提取应期"""
        patterns = [
            r'应期[：:]\s*([^\n]+)',
            r'时间[：:]\s*([^\n]+)',
            r'月|季|年'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                timing = match.group(1).strip() if match.lastindex else match.group(0)
                return timing[:30]  # 限制长度
        return "详见分析"

    def _extract_key_points(self, content: str) -> str:
        """提取关键论点"""
        lines = content.split('\n')
        key_lines = [line.strip() for line in lines if line.strip().startswith(('-', '•', '*'))]
        return ' '.join(key_lines[:3]) if key_lines else ""

    def _extract_suggestion(self, content: str) -> str:
        """提取建议"""
        if '建议' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '建议' in line:
                    return ' '.join(lines[i:min(i+3, len(lines))])
        return "根据实际情况灵活应对"

    def _calculate_overall_consensus(self, context: DebateContext) -> str:
        """计算整体共识度"""
        if context.convergence_score > 0.8:
            return "高"
        elif context.convergence_score > 0.5:
            return "中"
        else:
            return "低"

    def _get_school_chinese_name(self, school) -> str:
        """获取流派中文名称"""
        # 如果是字符串，直接映射
        if isinstance(school, str):
            name_map = {
                "traditional": "传统正宗派",
                "xiangshu": "象数派",
                "mangpai": "盲派"
            }
            return name_map.get(school, school)

        # 如果是枚举，使用枚举映射
        name_map = {
            SchoolType.TRADITIONAL: "传统正宗派",
            SchoolType.XIANGSHU: "象数派",
            SchoolType.MANGPAI: "盲派"
        }
        return name_map.get(school, school.value if hasattr(school, 'value') else str(school))

    def _extract_responses_from_round(self, round_data: Dict[str, Any]) -> List[AgentResponse]:
        """从轮次数据中提取响应列表"""
        responses_data = round_data.get('responses', [])
        responses = []

        for resp_data in responses_data:
            if isinstance(resp_data, dict):
                responses.append(AgentResponse(**resp_data))
            elif isinstance(resp_data, AgentResponse):
                responses.append(resp_data)

        return responses


# ==================== Module-level Helper Functions ====================

def extract_fortune_from_report(report_text: str) -> str:
    """从最终报告中提取吉凶程度

    Args:
        report_text: 最终报告文本

    Returns:
        str: 吉凶程度描述（截取到8字符以内）
    """
    patterns = [
        r'吉凶判断[：:]\s*([^\n]+)',
        r'综合判断[：:]\s*([^\n]+)',
        r'吉凶[：:]\s*([^\n]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, report_text)
        if match:
            judgment = match.group(1).strip()
            # Return short form: 吉, 凶, 中吉, etc.
            if len(judgment) > 8:
                return judgment[:8] + ".."
            return judgment
    return "未知"


def compute_consensus_from_history(debate_history_json: str) -> str:
    """从辩论历史JSON计算共识度

    Args:
        debate_history_json: 辩论历史JSON字符串

    Returns:
        str: 共识度等级 (高/中/低/-)
    """
    try:
        history_data = json.loads(debate_history_json)
        # Extract confidences from last round responses
        if "rounds" in history_data and history_data["rounds"]:
            last_round = history_data["rounds"][-1]
            responses = last_round.get("responses", [])
            confidences = [r.get("confidence", 0) for r in responses]

            if not confidences:
                return "-"

            avg_conf = sum(confidences) / len(confidences)
            variance = sum((c - avg_conf) ** 2 for c in confidences) / len(confidences)

            # Return concise form
            if avg_conf > 7.5 and variance < 1.0:
                return "高"
            elif avg_conf > 6.0 and variance < 2.0:
                return "中"
            else:
                return "低"
    except Exception:
        pass
    return "-"
