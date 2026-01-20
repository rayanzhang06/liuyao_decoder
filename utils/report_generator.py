"""报告生成器 - 生成符合prompt_v2.md规范的最终解读报告"""
import re
from typing import Dict, List, Any, Optional
from loguru import logger

from storage.models import DebateContext, SchoolType, AgentResponse


class ReportGenerator:
    """报告生成器 - 将辩论结果转换为结构化的markdown报告"""

    def __init__(self):
        """初始化报告生成器"""
        logger.info("ReportGenerator 初始化完成")

    def generate_report(self, context: DebateContext) -> str:
        """
        生成最终markdown报告

        遵循prompt_v2.md 4.3节的格式规范

        Args:
            context: 辩论上下文

        Returns:
            str: Markdown格式的报告
        """
        logger.info("开始生成最终报告")

        sections = []

        # 一、卦象基本信息
        sections.append(self._generate_section_1(context))

        # 二、核心结论
        consensus_analysis = self._analyze_consensus(context)
        sections.append(self._generate_section_2(context, consensus_analysis))

        # 三、详细分析
        sections.append(self._generate_section_3(context))

        # 四、流派视角
        sections.append(self._generate_section_4(context))

        # 五、辩论摘要
        sections.append(self._generate_section_5(context))

        # 六、综合建议
        sections.append(self._generate_section_6(context))

        # 七、备注
        sections.append(self._generate_section_7(context))

        report = '\n\n'.join(sections)

        logger.info("报告生成完成")
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

    def _generate_section_2(self, context: DebateContext, consensus: Dict[str, Any]) -> str:
        """生成第二部分：核心结论"""
        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)

        # 构建结论表格
        conclusion_table = "| 流派 | 吉凶判断 | 置信度 |\n|------|---------|--------|\n"
        for resp in responses:
            conclusion = self._extract_fortune_judgment(resp.content)
            # 处理 school 字段（可能是枚举或字符串）
            school_str = self._get_school_chinese_name(resp.school)
            conclusion_table += f"| {school_str} | {conclusion} | {resp.confidence}/10 |\n"

        # 计算共识度
        consensus_level = self._calculate_consensus_level(responses)

        return f"""## 二、核心结论

### 2.1 吉凶判断
**【共识度：{consensus_level}】**

{conclusion_table}

**共识依据**：
{self._extract_consensus_reasons(responses)}

### 2.2 应期推断
**【共识度：{self._calculate_timing_consensus(responses)}】**

| 流派 | 应期判断 | 置信度 |
|------|---------|--------|
{self._generate_timing_table(responses)}

### 2.3 关键建议

**【共识】**
{self._extract_common_suggestions(responses)}

**【流派特色建议】**
{self._extract_school_specific_suggestions(responses)}
"""

    def _generate_section_3(self, context: DebateContext) -> str:
        """生成第三部分：详细分析"""
        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)

        content = "## 三、详细分析\n\n"

        # 3.1 用神分析
        content += "### 3.1 用神分析\n\n"
        content += "**用神选取**：分析各流派用神选取\n\n"

        for resp in responses:
            school_name = self._get_school_chinese_name(resp.school)
            content += f"**{school_name}观点**：\n"
            content += f"{self._extract_yongshen_analysis(resp.content)}\n\n"

        # 3.2 动爻解析
        content += "### 3.2 动爻解析\n\n"
        hexagram = context.hexagram
        dong_yao_lines = [line for line in hexagram.lines if line.change_info]

        for line in dong_yao_lines:
            content += f"**{line.position}爻 {line.liuqin} {line.wuxing}**：\n\n"
            # 这里可以从各流派的分析中提取对该动爻的解读
            content += f"- {self._get_school_chinese_name(SchoolType.TRADITIONAL)}：关注其五行生克制化\n"
            content += f"- {self._get_school_chinese_name(SchoolType.XIANGSHU)}：关注其意象变化\n"
            content += f"- {self._get_school_chinese_name(SchoolType.MANGPAI)}：关注口诀验证\n\n"

        # 3.3 六神与世应分析
        content += "### 3.3 六神与世应分析\n\n"
        content += "（根据各流派分析提取）\n"

        return content

    def _generate_section_4(self, context: DebateContext) -> str:
        """生成第四部分：流派视角"""
        content = "## 四、流派视角\n\n"

        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)

        for resp in responses:
            school_name = self._get_school_chinese_name(resp.school)
            content += f"### 4.1 {school_name}视角\n\n"
            content += f"{self._extract_full_analysis(resp.content)}\n\n"

        return content

    def _generate_section_5(self, context: DebateContext) -> str:
        """生成第五部分：辩论摘要"""
        content = "## 五、辩论摘要\n\n"

        # 5.1 达成共识的过程
        content += "### 5.1 达成共识的过程\n\n"

        turning_points = self._find_turning_points(context)
        for tp in turning_points:
            content += f"- **第{tp['round']}轮**：{tp['description']}\n"
        content += "\n"

        # 5.2 主要分歧点
        content += "### 5.2 主要分歧点\n\n"
        disagreements = self._find_disagreements(context)
        if disagreements:
            for i, disc in enumerate(disagreements, 1):
                content += f"**分歧{i}**：{disc['description']}\n\n"
        else:
            content += "（各流派观点基本一致）\n\n"

        # 5.3 最终置信度
        content += "### 5.3 最终置信度\n\n"
        content += "| 流派 | 吉凶判断置信度 | 应期判断置信度 |\n"
        content += "|------|---------------|---------------|\n"

        confidence_history = self._track_confidence_history(context)
        for school, confs in confidence_history.items():
            school_name = self._get_school_chinese_name(school)
            final_conf = confs[-1] if confs else 0.0
            content += f"| {school_name} | {final_conf}/10 | {final_conf}/10 |\n"

        return content

    def _generate_section_6(self, context: DebateContext) -> str:
        """生成第六部分：综合建议"""
        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)

        content = "## 六、综合建议\n\n"

        # 6.1 短期行动
        content += "### 6.1 短期行动（1-3个月）\n\n"
        content += self._extract_short_term_suggestions(responses) + "\n\n"

        # 6.2 中期规划
        content += "### 6.2 中期规划（3-6个月）\n\n"
        content += self._extract_mid_term_plans(responses) + "\n\n"

        # 6.3 风险提示
        content += "### 6.3 风险提示\n\n"
        content += self._extract_risk_warnings(responses) + "\n\n"

        # 6.4 辅助建议
        content += "### 6.4 辅助建议\n\n"
        content += "**宜**：\n"
        content += self._extract_recommendations(responses, 'dos') + "\n\n"
        content += "**忌**：\n"
        content += self._extract_recommendations(responses, 'donts') + "\n"

        return content

    def _generate_section_7(self, context: DebateContext) -> str:
        """生成第七部分：备注"""
        return f"""## 七、备注

- **本报告由三流派辩论生成**，共经历 {context.current_round} 轮迭代
- **共识度**：{self._calculate_overall_consensus(context)}
- **收敛分数**：{context.convergence_score:.2f}
- **报告生成时间**：{context.hexagram.datetime}

**特别说明**：
本报告仅供参考，现实仍需努力。六爻解读提供的是趋势分析，具体结果还需看个人努力与实际行动。
"""

    # ==================== 辅助方法 ====================

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

    def _extract_full_analysis(self, content: str) -> str:
        """提取完整分析"""
        # 清理和格式化内容
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines[:20])  # 限制长度

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

    def _find_turning_points(self, context: DebateContext) -> List[Dict[str, Any]]:
        """寻找辩论的关键转折点"""
        turning_points = []

        # 找出置信度变化最大的轮次
        confidence_history = self._track_confidence_history(context)

        for round_num in range(1, len(context.history)):
            prev_confs = {}
            curr_confs = {}

            for school, confs in confidence_history.items():
                if round_num - 1 < len(confs) and round_num < len(confs):
                    prev_confs[school] = confs[round_num - 1]
                    curr_confs[school] = confs[round_num]

            if prev_confs and curr_confs:
                # 计算平均变化
                avg_change = sum(
                    abs(curr_confs[s] - prev_confs[s])
                    for s in prev_confs.keys()
                ) / len(prev_confs)

                if avg_change > 1.0:  # 显著变化
                    turning_points.append({
                        'round': round_num,
                        'description': f'观点显著调整 (平均变化 {avg_change:.2f})'
                    })

        return turning_points

    def _find_disagreements(self, context: DebateContext) -> List[Dict[str, Any]]:
        """寻找主要分歧点"""
        # 简化版本：基于置信度差异判断
        disagreements = []

        last_round = context.history[-1]
        responses = self._extract_responses_from_round(last_round)

        confidences = [r.confidence for r in responses]
        if max(confidences) - min(confidences) > 3.0:
            disagreements.append({
                'description': '各流派对吉凶判断存在较大分歧'
            })

        return disagreements

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
