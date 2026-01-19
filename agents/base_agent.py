"""Agent 基类"""
import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from loguru import logger

from llm.base import BaseLLMClient, Message, LLMResponse
from llm.factory import LLMClientFactory
from storage.models import HexagramInput, AgentResponse, SchoolType


class BaseAgent(ABC):
    """Agent 抽象基类"""

    def __init__(self,
                 name: str,
                 school: SchoolType,
                 llm_client: BaseLLMClient,
                 prompt_path: str,
                 literature_search: Optional['LiteratureSearch'] = None):
        """
        初始化 Agent

        Args:
            name: Agent 名称
            school: 流派类型
            llm_client: LLM 客户端
            prompt_path: Prompt 文件路径
            literature_search: 可选的文献搜索实例
        """
        self.name = name
        self.school = school
        self.llm_client = llm_client
        self.prompt_path = prompt_path
        self.literature_search = literature_search

        # 加载 system prompt
        self.system_prompt = self._load_system_prompt()

        logger.info(f"初始化 {self.school.value} Agent: {self.name}")

    @abstractmethod
    def interpret(self, hexagram: HexagramInput) -> AgentResponse:
        """
        独立解读卦象

        Args:
            hexagram: 卦象输入

        Returns:
            AgentResponse: Agent 响应
        """
        pass

    @abstractmethod
    def debate(self,
              hexagram: HexagramInput,
              debate_history: List[Dict[str, Any]],
              round_number: int) -> AgentResponse:
        """
        参与辩论

        Args:
            hexagram: 卦象输入
            debate_history: 辩论历史
            round_number: 当前轮次

        Returns:
            AgentResponse: Agent 响应
        """
        pass

    def _load_system_prompt(self) -> str:
        """
        加载 system prompt

        Returns:
            str: System prompt 内容
        """
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            logger.info(f"加载 prompt 文件成功: {self.prompt_path}")
            return prompt
        except FileNotFoundError:
            logger.error(f"Prompt 文件不存在: {self.prompt_path}")
            return f"你是{self.school.value}的六爻解读专家。"
        except Exception as e:
            logger.error(f"加载 prompt 文件失败: {e}")
            return f"你是{self.school.value}的六爻解读专家。"

    def _build_initial_prompt(self, hexagram: HexagramInput) -> str:
        """
        构建初始解读的 prompt

        Args:
            hexagram: 卦象输入

        Returns:
            str: 完整的 user prompt
        """
        prompt = f"""请对以下卦象进行独立解读：

## 问题
{hexagram.question}

## 卦象信息
**卦名变换**：{hexagram.ben_gua_name} → {hexagram.bian_gua_name}

**占卜时间**：{hexagram.datetime}

**干支时间**：
- 年：{hexagram.ganzhi.get('year', '未知')}
- 月：{hexagram.ganzhi.get('month', '未知')}
- 日：{hexagram.ganzhi.get('day', '未知')}
- 时：{hexagram.ganzhi.get('hour', '未知')}

**空亡**：{hexagram.kongwang}

**本卦**：{hexagram.ben_gua}（{hexagram.ben_gua_gong}宫·第{hexagram.ben_gua_index}卦 - {hexagram.ben_gua_type}）

**变卦**：{hexagram.bian_gua}（{hexagram.bian_gua_gong}宫·第{hexagram.bian_gua_index}卦）

**六爻详情**：
"""
        # 添加六爻详情
        for line in hexagram.lines:
            line_info = f"- {line.position}爻：{line.shen} {line.liuqin} {line.wuxing} {line.yin_yang}"
            if line.shi_ying:
                line_info += f" [{line.shi_ying}]"
            if line.change_info:
                line_info += f" → {line.change_info}"
            prompt += line_info + "\n"

        prompt += """
请按照以下格式输出：

## [流派名称] 初始解读

### 1. 用神选取
- 选取依据：[具体理由]
- 用神：[爻位]

### 2. 核心分析
- [逐条列出分析要点]

### 3. 初步结论
- 吉凶判断：[0-10分，并说明]
- 应期推断：[具体时间]
- 关键建议：[行动建议]

### 4. 置信度
- 自评：[0-10分]
- 理由：[为什么给出这个评分]
"""
        return prompt

    def _build_debate_prompt(self,
                           hexagram: HexagramInput,
                           debate_history: List[Dict[str, Any]],
                           round_number: int) -> str:
        """
        构建辩论的 prompt

        Args:
            hexagram: 卦象输入
            debate_history: 辩论历史
            round_number: 当前轮次

        Returns:
            str: 完整的 user prompt
        """
        prompt = f"""这是第 {round_number} 轮辩论。请回顾之前的讨论，并给出你的观点。

## 原始卦象信息
**问题**：{hexagram.question}
**卦名**：{hexagram.ben_gua_name} → {hexagram.bian_gua_name}

## 之前的讨论摘要

"""
        # 添加历史记录摘要
        for round_data in debate_history:
            prompt += f"\n### 第{round_data['round']}轮\n"
            for response in round_data.get('responses', []):
                prompt += f"**{response['agent_name']}（{response['school']}）**：\n"
                # 只显示关键结论部分
                if '核心结论' in response['content']:
                    lines = response['content'].split('\n')
                    for line in lines:
                        if line.startswith('- ') or line.startswith('*'):
                            prompt += line + "\n"
                prompt += "\n"

        prompt += f"""
## 你在第{round_number}轮的任务

请按照以下格式输出：

## [流派名称] 第{round_number}轮发言

### 1. 观点总结（保留不变的部分）
- [上一轮中仍然坚持的核心观点]

### 2. 观点修正（本轮调整的部分）
- 原观点：[之前的观点]
- 修正为：[新观点]
- 修正理由：[为什么修正，参考了谁的观点]
- **理论框架一致性**：[说明新观点如何在本流派理论框架内成立]

### 3. 对其他 Agent 的回应
#### 对 [流派A] 的回应
- 我同意的部分：[具体内容]
- 我质疑的部分：[具体内容 + 质疑理由]
- 证据：[支持质疑的证据]
- 文献依据：[引用本流派经典文献的具体章节或原文，如有]

#### 对 [流派B] 的回应
- [同上结构]

### 4. 本轮文献检索（可选）
- 检索关键词：[本轮查阅文献时使用的关键词]
- 查阅文献：[查阅的经典文献名称及章节]
- 文献要点：[从文献中提取的关键观点或原文引用]
- 应用说明：[如何将文献内容应用到当前卦象解读]

### 5. 本轮核心论点
- [本轮最想强调的观点]

### 6. 当前置信度
- 自评：[0-10分]
- 调整理由：[为什么提高或降低置信度]
"""
        return prompt

    def _call_llm(self, prompt: str) -> LLMResponse:
        """
        调用 LLM

        Args:
            prompt: 用户 prompt

        Returns:
            LLMResponse: LLM 响应
        """
        messages = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=prompt)
        ]

        return self.llm_client.chat(messages)

    def _extract_confidence(self, content: str) -> float:
        """
        从响应中提取置信度

        Args:
            content: 响应内容

        Returns:
            float: 置信度（0-10）
        """
        # 尝试多种模式匹配置信度
        patterns = [
            r'置信度[：:]\s*([0-9.]+)',
            r'自评[：:]\s*([0-9.]+)',
            r'吉凶判断[：:][^0-9]*([0-9.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    confidence = float(match.group(1))
                    return max(0, min(10, confidence))  # 限制在 0-10 范围
                except ValueError:
                    pass

        # 如果没有找到明确的置信度，返回默认值
        return 5.0

    def validate_response(self, response: AgentResponse) -> bool:
        """
        验证响应是否有效

        Args:
            response: Agent 响应

        Returns:
            bool: 是否有效
        """
        if not response.content:
            logger.error(f"{self.name} 响应内容为空")
            return False

        if response.confidence < 0 or response.confidence > 10:
            logger.warning(f"{self.name} 置信度超出范围: {response.confidence}")
            response.confidence = max(0, min(10, response.confidence))

        return True

    def _search_literature(self, debate_history: List[Dict[str, Any]], round_number: int) -> List:
        """
        搜索文献引用

        Args:
            debate_history: 辩论历史
            round_number: 当前轮次

        Returns:
            List: 文献引用列表
        """
        if not self.literature_search:
            return []

        # 提取关键词
        keywords = self._extract_keywords(debate_history, round_number)

        if not keywords:
            return []

        # 搜索文献
        try:
            refs = self.literature_search.search(self.school, keywords, top_k=3)
            logger.debug(f"{self.name} 搜索到 {len(refs)} 条文献引用")
            return refs
        except Exception as e:
            logger.error(f"{self.name} 文献搜索失败: {e}")
            return []

    def _extract_keywords(self, debate_history: List[Dict[str, Any]], round_number: int) -> List[str]:
        """
        从辩论历史中提取关键词

        Args:
            debate_history: 辩论历史
            round_number: 当前轮次

        Returns:
            List[str]: 关键词列表
        """
        keywords = []

        # 从最近几轮中提取关键词
        recent_rounds = debate_history[-3:] if len(debate_history) >= 3 else debate_history

        for round_data in recent_rounds:
            for resp in round_data.get('responses', []):
                content = resp.get('content', '')

                # 提取关键概念（简单实现）
                # 查找"用神"、"官鬼"、"妻财"等六爻术语
                terms = re.findall(r'(用神|官鬼|妻财|兄弟|子孙|父母|世爻|应爻|动爻|空亡|月建|日辰)', content)
                keywords.extend(terms)

                # 提取问题关键词
                if round_number == 0:
                    # 初始轮，从问题中提取
                    question = content.split('问题')[-1].split('\n')[0] if '问题' in content else ''
                    if question:
                        keywords.extend(re.findall(r'[\u4e00-\u9fa5]{2,}', question))

        # 去重并返回前10个
        unique_keywords = list(set(keywords))[:10]
        return unique_keywords

    def _format_literature_refs(self, refs: List) -> str:
        """
        格式化文献引用用于prompt

        Args:
            refs: 文献引用列表

        Returns:
            str: 格式化后的文献引用文本
        """
        if not refs:
            return ""

        formatted = "\n\n## 本轮文献检索结果\n\n"

        for i, ref in enumerate(refs, 1):
            formatted += f"### 文献 {i}\n"
            formatted += f"- **书名**：《{ref.book_title}》\n"
            formatted += f"- **章节**：{ref.volume}·{ref.chapter}\n"
            formatted += f"- **原文**：{ref.original_text}\n"
            formatted += f"- **关键词**：{ref.keyword}\n\n"

        return formatted


import re  # 需要导入 re 模块
