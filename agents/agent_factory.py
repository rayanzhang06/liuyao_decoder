"""Agent 工厂 - 通过配置创建不同流派的Agent"""
from typing import Optional
from loguru import logger

from llm.base import BaseLLMClient
from storage.models import SchoolType
from agents.base_agent import BaseAgent


class AgentFactory:
    """Agent 工厂类"""

    # Agent 配置字典
    AGENT_CONFIG = {
        'traditional': {
            'name': 'TraditionalAgent',
            'school': SchoolType.TRADITIONAL,
            'display_name': '传统正宗派'
        },
        'xiangshu': {
            'name': 'XiangshuAgent',
            'school': SchoolType.XIANGSHU,
            'display_name': '象数派'
        },
        'mangpai': {
            'name': 'MangpaiAgent',
            'school': SchoolType.MANGPAI,
            'display_name': '盲派'
        }
    }

    @classmethod
    def create(cls,
               agent_type: str,
               llm_client: BaseLLMClient,
               prompt_path: str,
               literature_search: Optional['LiteratureSearch'] = None) -> BaseAgent:
        """
        创建指定类型的Agent

        Args:
            agent_type: Agent类型 ('traditional', 'xiangshu', 'mangpai')
            llm_client: LLM客户端
            prompt_path: Prompt文件路径
            literature_search: 可选的文献搜索实例

        Returns:
            BaseAgent: Agent实例

        Raises:
            ValueError: 如果agent_type不支持
        """
        if agent_type not in cls.AGENT_CONFIG:
            raise ValueError(f"不支持的Agent类型: {agent_type}。支持的类型: {list(cls.AGENT_CONFIG.keys())}")

        config = cls.AGENT_CONFIG[agent_type]

        agent = BaseAgent(
            name=config['name'],
            school=config['school'],
            llm_client=llm_client,
            prompt_path=prompt_path,
            literature_search=literature_search
        )

        logger.info(f"创建{config['display_name']} Agent，使用 LLM: {llm_client.__class__.__name__}")

        return agent

    @classmethod
    def get_supported_types(cls) -> list:
        """
        获取支持的Agent类型列表

        Returns:
            list: 支持的Agent类型列表
        """
        return list(cls.AGENT_CONFIG.keys())

    @classmethod
    def get_config(cls, agent_type: str) -> dict:
        """
        获取指定Agent类型的配置

        Args:
            agent_type: Agent类型

        Returns:
            dict: Agent配置字典

        Raises:
            ValueError: 如果agent_type不支持
        """
        if agent_type not in cls.AGENT_CONFIG:
            raise ValueError(f"不支持的Agent类型: {agent_type}")
        return cls.AGENT_CONFIG[agent_type].copy()
