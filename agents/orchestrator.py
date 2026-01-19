"""辩论编排器 - 协调三个Agent进行多轮辩论"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from datetime import datetime

from config.config_loader import Config
from storage.models import (
    HexagramInput,
    DebateContext,
    DebateState,
    RoundRecord,
    AgentResponse,
    SchoolType
)
from agents.base_agent import BaseAgent
from agents.traditional_agent import TraditionalAgent
from agents.xiangshu_agent import XiangshuAgent
from agents.mangpai_agent import MangpaiAgent
from llm.factory import LLMClientFactory

# 导入文献搜索（Stage 3）
try:
    from utils.literature_search import LiteratureSearch
    LITERATURE_SEARCH_AVAILABLE = True
except ImportError:
    LITERATURE_SEARCH_AVAILABLE = False
    logger.warning("LiteratureSearch未导入，文献搜索功能将不可用")


class DebateOrchestrator:
    """辩论编排器 - 管理三个Agent的辩论流程"""

    def __init__(self, config: Config):
        """
        初始化编排器

        Args:
            config: 配置对象
        """
        self.config = config
        self.debate_config = config.get_debate_config()

        # 初始化文献搜索（如果启用）
        self.literature_search = None
        lit_config = config.get_literature_search_config()
        if lit_config.get('enabled', False) and LITERATURE_SEARCH_AVAILABLE:
            try:
                self.literature_search = LiteratureSearch(lit_config)
                logger.info("文献搜索功能已启用")
            except Exception as e:
                logger.warning(f"文献搜索初始化失败: {e}")

        # 初始化三个Agent
        self.agents: List[BaseAgent] = []
        self._initialize_agents()

        logger.info("DebateOrchestrator 初始化完成")

    def _initialize_agents(self):
        """初始化三个流派Agent"""
        agent_configs = {
            'traditional': self.config.get_agent_config('traditional'),
            'xiangshu': self.config.get_agent_config('xiangshu'),
            'mangpai': self.config.get_agent_config('mangpai')
        }

        # 创建传统正宗派Agent
        trad_config = agent_configs['traditional']
        trad_llm = LLMClientFactory.create(
            trad_config['llm_client'],
            self.config.get_llm_config(trad_config['llm_client'])['api_key'],
            trad_config['model']
        )
        self.agents.append(TraditionalAgent(
            name="TraditionalAgent",
            llm_client=trad_llm,
            prompt_path=trad_config['prompt_file'],
            literature_search=self.literature_search
        ))

        # 创建象数派Agent
        xiang_config = agent_configs['xiangshu']
        xiang_llm = LLMClientFactory.create(
            xiang_config['llm_client'],
            self.config.get_llm_config(xiang_config['llm_client'])['api_key'],
            xiang_config['model']
        )
        self.agents.append(XiangshuAgent(
            name="XiangshuAgent",
            llm_client=xiang_llm,
            prompt_path=xiang_config['prompt_file'],
            literature_search=self.literature_search
        ))

        # 创建盲派Agent
        mang_config = agent_configs['mangpai']
        mang_llm = LLMClientFactory.create(
            mang_config['llm_client'],
            self.config.get_llm_config(mang_config['llm_client'])['api_key'],
            mang_config['model']
        )
        self.agents.append(MangpaiAgent(
            name="MangpaiAgent",
            llm_client=mang_llm,
            prompt_path=mang_config['prompt_file'],
            literature_search=self.literature_search
        ))

        logger.info(f"已初始化 {len(self.agents)} 个Agent: {[a.name for a in self.agents]}")

    async def run_debate(self, hexagram: HexagramInput) -> DebateContext:
        """
        运行完整的辩论流程

        Args:
            hexagram: 卦象输入

        Returns:
            DebateContext: 包含完整辩论历史的上下文
        """
        logger.info(f"开始辩论: {hexagram.ben_gua_name} → {hexagram.bian_gua_name}")

        # 初始化辩论上下文
        context = DebateContext(
            hexagram=hexagram,
            agents=[a.name for a in self.agents],
            history=[],
            current_round=0,
            state=DebateState.INIT,
            convergence_score=0.0
        )

        # Stage 1: 初始解读（Round 0）
        logger.info("=== Stage 1: 初始解读 (Round 0) ===")
        context.state = DebateState.INITIAL_INTERPRETATION
        initial_round = await self._run_initial_interpretation(hexagram)
        context.history.append(self._round_record_to_dict(initial_round))
        context.current_round = 0

        # Stage 2: 辩论轮次（Round 1-10）
        logger.info("=== Stage 2: 辩论阶段 ===")
        max_rounds = self.debate_config['max_rounds']
        min_rounds = self.debate_config.get('min_rounds_for_convergence', 3)

        for round_num in range(1, max_rounds + 1):
            logger.info(f"--- 第 {round_num} 轮辩论 ---")
            context.state = DebateState.DEBATING
            context.current_round = round_num

            # 运行本轮辩论
            debate_round = await self._run_debate_round(hexagram, context.history, round_num)
            context.history.append(self._round_record_to_dict(debate_round))

            # 检查收敛
            if round_num >= min_rounds:
                should_stop, reason = self._check_convergence(context)
                if should_stop:
                    logger.info(f"辩论收敛: {reason} (第 {round_num} 轮)")
                    context.state = DebateState.CONVERGED
                    context.convergence_score = self._calculate_convergence_score(context)
                    break
            else:
                logger.debug(f"轮次 {round_num} < 最小收敛轮次 {min_rounds}，继续辩论")
        else:
            # 达到最大轮次
            logger.warning(f"达到最大轮次 {max_rounds}，停止辩论")
            context.state = DebateState.MAX_ROUNDS_REACHED
            context.convergence_score = self._calculate_convergence_score(context)

        context.state = DebateState.FINISHED
        logger.info(f"辩论完成: 共 {context.current_round} 轮，收敛分数: {context.convergence_score:.2f}")

        return context

    async def _run_initial_interpretation(self, hexagram: HexagramInput) -> RoundRecord:
        """
        运行初始解读（Round 0）- 并行调用三个Agent

        Args:
            hexagram: 卦象输入

        Returns:
            RoundRecord: 包含三个Agent响应的轮次记录
        """
        logger.info("并行调用三个Agent进行初始解读")

        # 并行调用三个Agent的interpret方法
        tasks = [agent.interpret(hexagram) for agent in self.agents]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常和响应
        processed_responses = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                logger.error(f"Agent {self.agents[i].name} 初始解读失败: {resp}")
                # 创建错误响应
                processed_responses.append(AgentResponse(
                    agent_name=self.agents[i].name,
                    school=self.agents[i].school,
                    content=f"分析失败：{str(resp)}",
                    confidence=0.0,
                    round_number=0,
                    metadata={"error": str(resp)}
                ))
            else:
                processed_responses.append(resp)
                logger.info(f"Agent {resp.agent_name} 初始解读完成，置信度: {resp.confidence}")

        return RoundRecord(
            round=0,
            stage="initial_interpretation",
            responses=processed_responses,
            timestamp=datetime.now()
        )

    async def _run_debate_round(self,
                               hexagram: HexagramInput,
                               history: List[Dict[str, Any]],
                               round_number: int) -> RoundRecord:
        """
        运行单轮辩论 - 顺序调用三个Agent（每个Agent需要看到其他Agent的响应）

        Args:
            hexagram: 卦象输入
            history: 辩论历史
            round_number: 当前轮次

        Returns:
            RoundRecord: 包含三个Agent响应的轮次记录
        """
        logger.info(f"运行第 {round_number} 轮辩论")

        # 顺序调用三个Agent的debate方法
        responses = []
        for agent in self.agents:
            try:
                logger.debug(f"调用 {agent.name} 的辩论方法")
                resp = await agent.debate(hexagram, history, round_number)
                responses.append(resp)
                logger.info(f"Agent {resp.agent_name} 第 {round_number} 轮完成，置信度: {resp.confidence}")
            except Exception as e:
                logger.error(f"Agent {agent.name} 第 {round_number} 轮失败: {e}")
                # 创建错误响应
                responses.append(AgentResponse(
                    agent_name=agent.name,
                    school=agent.school,
                    content=f"辩论失败：{str(e)}",
                    confidence=0.0,
                    round_number=round_number,
                    metadata={"error": str(e)}
                ))

        return RoundRecord(
            round=round_number,
            stage="debate",
            responses=responses,
            timestamp=datetime.now()
        )

    def _check_convergence(self, context: DebateContext) -> Tuple[bool, str]:
        """
        检查辩论是否收敛

        基于prompt_v2.md 3.4节的收敛规则：
        - 规则1: 连续3轮所有Agent的置信度波动 < 0.5
        - 规则2: 所有关键结论达成共识（差异度 < 10%）
        - 规则3: 出现压倒性证据

        Args:
            context: 辩论上下文

        Returns:
            Tuple[bool, str]: (是否应停止, 停止原因)
        """
        current_round = context.current_round
        history = context.history

        # 规则1: 置信度稳定性检查
        if current_round >= 3:
            recent_rounds = history[-3:]

            # 对每个Agent检查最近3轮的置信度变化
            confidence_stable = True
            for agent in context.agents:
                confidences = []
                for round_data in recent_rounds:
                    for resp in round_data.get('responses', []):
                        if resp.get('agent_name') == agent or resp.get('agent_name', '').endswith(agent):
                            confidences.append(resp.get('confidence', 0.0))

                if len(confidences) >= 3:
                    max_conf = max(confidences)
                    min_conf = min(confidences)
                    fluctuation = max_conf - min_conf

                    logger.debug(f"Agent {agent} 置信度波动: {fluctuation:.2f}")

                    if fluctuation >= self.debate_config.get('confidence_stability_threshold', 0.5):
                        confidence_stable = False
                        break

            if confidence_stable:
                return True, f"连续3轮置信度波动 < {self.debate_config.get('confidence_stability_threshold', 0.5)}"

        # 规则2: 高置信度共识检查
        # 简化版本：如果所有Agent置信度都 > 7.0，认为达成共识
        last_round = history[-1]
        confidences = [resp.get('confidence', 0.0) for resp in last_round.get('responses', [])]

        if all(conf > 7.0 for conf in confidences):
            avg_confidence = sum(confidences) / len(confidences)
            return True, f"所有Agent达成高置信度共识 (平均 {avg_confidence:.2f})"

        # 规则3: 压倒性证据（暂未实现，需要更复杂的逻辑）

        return False, ""

    def _calculate_convergence_score(self, context: DebateContext) -> float:
        """
        计算收敛分数（0-1）

        基于置信度的分布计算收敛度

        Args:
            context: 辩论上下文

        Returns:
            float: 收敛分数（0-1，越高表示收敛度越好）
        """
        last_round = context.history[-1]
        confidences = [resp.get('confidence', 0.0) for resp in last_round.get('responses', [])]

        if not confidences:
            return 0.0

        # 计算置信度的平均值
        avg_confidence = sum(confidences) / len(confidences)

        # 计算置信度的标准差
        variance = sum((c - avg_confidence) ** 2 for c in confidences) / len(confidences)
        std_dev = variance ** 0.5

        # 收敛分数 = 平均置信度 / 10 * (1 - 标准差/10)
        convergence_score = (avg_confidence / 10.0) * (1.0 - min(std_dev / 10.0, 1.0))

        return max(0.0, min(1.0, convergence_score))

    def _round_record_to_dict(self, record: RoundRecord) -> Dict[str, Any]:
        """
        将RoundRecord转换为字典（用于序列化）

        Args:
            record: 轮次记录

        Returns:
            Dict: 字典格式的轮次记录
        """
        return {
            'round': record.round,
            'stage': record.stage,
            'responses': [resp.dict() for resp in record.responses],
            'timestamp': record.timestamp.isoformat()
        }
