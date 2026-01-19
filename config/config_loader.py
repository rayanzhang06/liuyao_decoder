"""配置加载模块"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from dotenv import load_dotenv
from loguru import logger


class Config:
    """配置管理类"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化配置

        Args:
            config_path: 配置文件路径
        """
        # 加载环境变量
        load_dotenv()

        # 加载 YAML 配置
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"配置加载成功: {config_path}")

    def get_llm_config(self, client_name: str) -> Dict[str, Any]:
        """
        获取 LLM 客户端配置

        Args:
            client_name: 客户端名称（"openai" 或 "anthropic"）

        Returns:
            Dict: 客户端配置
        """
        clients = self.config.get('llm', {}).get('clients', {})

        if client_name not in clients:
            raise ValueError(f"未找到 LLM 客户端配置: {client_name}")

        client_config = clients[client_name].copy()

        # 替换环境变量
        if 'api_key' in client_config:
            api_key = client_config['api_key']
            if api_key.startswith('${') and api_key.endswith('}'):
                env_var = api_key[2:-1]
                client_config['api_key'] = os.getenv(env_var)
                if not client_config['api_key']:
                    raise ValueError(f"环境变量未设置: {env_var}")

        return client_config

    def get_default_llm_client(self) -> str:
        """
        获取默认的 LLM 客户端名称

        Returns:
            str: 客户端名称
        """
        return self.config.get('llm', {}).get('default_client', 'anthropic')

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        获取 Agent 配置

        Args:
            agent_name: Agent 名称（"traditional", "xiangshu", "mangpai"）

        Returns:
            Dict: Agent 配置
        """
        agents = self.config.get('agents', {})

        if agent_name not in agents:
            raise ValueError(f"未找到 Agent 配置: {agent_name}")

        return agents[agent_name]

    def get_all_agents_config(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有 Agent 配置

        Returns:
            Dict: 所有 Agent 配置
        """
        return self.config.get('agents', {})

    def get_debate_config(self) -> Dict[str, Any]:
        """
        获取辩论配置

        Returns:
            Dict: 辩论配置
        """
        return self.config.get('debate', {
            'max_rounds': 10,
            'convergence_threshold': 0.9,
            'confidence_stability_threshold': 0.5,
            'min_rounds_for_convergence': 3
        })

    def get_storage_config(self) -> Dict[str, Any]:
        """
        获取存储配置

        Returns:
            Dict: 存储配置
        """
        storage_config = self.config.get('storage', {'type': 'sqlite'})

        # 如果未指定 URL，使用默认值
        if 'url' not in storage_config:
            if storage_config['type'] == 'sqlite':
                storage_config['url'] = 'sqlite:///liuyao_decoder.db'
            elif storage_config['type'] == 'postgresql':
                storage_config['url'] = 'postgresql://localhost/liuyao_decoder'

        return storage_config

    def get_literature_search_config(self) -> Dict[str, Any]:
        """
        获取文献搜索配置

        Returns:
            Dict: 文献搜索配置
        """
        return self.config.get('literature_search', {
            'enabled': True,
            'method': 'keyword',
            'knowledge_base_path': 'knowledge_base',
            'top_k': 3
        })

    def get_logging_config(self) -> Dict[str, Any]:
        """
        获取日志配置

        Returns:
            Dict: 日志配置
        """
        return self.config.get('logging', {
            'level': 'INFO',
            'file': 'logs/liuyao_decoder.log',
            'rotation': '100 MB',
            'retention': '30 days'
        })

    def get_prompt_file_path(self, agent_name: str) -> str:
        """
        获取 Prompt 文件路径

        Args:
            agent_name: Agent 名称

        Returns:
            str: Prompt 文件路径
        """
        agent_config = self.get_agent_config(agent_name)
        prompt_file = agent_config.get('prompt_file')

        if not prompt_file:
            raise ValueError(f"Agent {agent_name} 未配置 prompt_file")

        return prompt_file
