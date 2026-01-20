"""传统正宗派 Agent"""
from typing import List, Dict, Any, Optional
from loguru import logger

from llm.base import BaseLLMClient
from storage.models import HexagramInput, AgentResponse, SchoolType
from agents.base_agent import BaseAgent


class TraditionalAgent(BaseAgent):
    """传统正宗派 Agent"""

    def __init__(self, llm_client: BaseLLMClient, prompt_path: str,
                 literature_search: Optional['LiteratureSearch'] = None):
        """
        初始化传统正宗派 Agent

        Args:
            llm_client: LLM 客户端
            prompt_path: Prompt 文件路径
            literature_search: 可选的文献搜索实例
        """
        super().__init__(
            name="TraditionalAgent",
            school=SchoolType.TRADITIONAL,
            llm_client=llm_client,
            prompt_path=prompt_path,
            literature_search=literature_search
        )
        logger.info(f"初始化传统正宗派 Agent，使用 LLM: {llm_client.__class__.__name__}")

    def interpret(self, hexagram: HexagramInput) -> AgentResponse:
        """
        独立解读卦象

        Args:
            hexagram: 卦象输入

        Returns:
            AgentResponse: Agent 响应
        """
        logger.info(f"{self.name} 开始独立解读卦象")

        # 构建初始解读的 prompt
        user_prompt = self._build_initial_prompt(hexagram)

        # 调用 LLM
        llm_response = self._call_llm(user_prompt)

        # 提取置信度
        confidence = self._extract_confidence(llm_response.content)

        # 构建 Agent 响应
        response = AgentResponse(
            agent_name=self.name,
            school=self.school,
            content=llm_response.content,
            confidence=confidence,
            round_number=0,
            references=[],  # 初始解读暂无文献引用
            metadata={
                "model": llm_response.model,
                "usage": llm_response.usage,
                "interpretation_type": "initial"
            }
        )

        # 验证响应
        if not self.validate_response(response):
            logger.error(f"{self.name} 响应验证失败")
            return AgentResponse(
                agent_name=self.name,
                school=self.school,
                content="解读失败：响应验证未通过",
                confidence=0.0,
                round_number=0,
                metadata={"error": "validation_failed"}
            )

        logger.info(f"{self.name} 完成独立解读，置信度: {confidence}/10")
        return response

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
        logger.info(f"{self.name} 参与第 {round_number} 轮辩论")

        # 构建辩论的 prompt
        user_prompt = self._build_debate_prompt(hexagram, debate_history, round_number)

        # 调用 LLM
        llm_response = self._call_llm(user_prompt)

        # 提取置信度
        confidence = self._extract_confidence(llm_response.content)

        # 构建响应
        response = AgentResponse(
            agent_name=self.name,
            school=self.school,
            content=llm_response.content,
            confidence=confidence,
            round_number=round_number,
            references=[],  # TODO: 文献搜索功能后续实现
            metadata={
                "model": llm_response.model,
                "usage": llm_response.usage,
                "interpretation_type": "debate"
            }
        )

        # 验证响应
        if not self.validate_response(response):
            logger.error(f"{self.name} 辩论响应验证失败")
            return AgentResponse(
                agent_name=self.name,
                school=self.school,
                content="辩论发言失败：响应验证未通过",
                confidence=0.0,
                round_number=round_number,
                metadata={"error": "validation_failed"}
            )

        logger.info(f"{self.name} 完成第 {round_number} 轮辩论，置信度: {confidence}/10")
        return response
