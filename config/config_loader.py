"""配置加载模块"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from dotenv import load_dotenv
from loguru import logger


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径，默认为 "config/config.yaml"
        """
        # 加载环境变量
        load_dotenv()

        # 项目根目录（以 config 目录上级作为基准）
        self.base_dir = Path(__file__).resolve().parent.parent

        # 使用默认路径如果未提供
        if config_path is None:
            config_path = self.base_dir / "config" / "config.yaml"

        # 加载 YAML 配置
        config_path = Path(config_path).expanduser()
        if not config_path.is_absolute():
            cwd_candidate = (Path.cwd() / config_path).resolve()
            config_path = cwd_candidate if cwd_candidate.exists() else (self.base_dir / config_path).resolve()

        self.config_path = config_path
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"配置加载成功: {config_path}")

    def _resolve_env_value(self, value: Any) -> Any:
        """解析 ${ENV_VAR} 形式的字符串"""
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            env_val = os.getenv(env_var)
            if env_val is None or env_val == "":
                raise ValueError(f"环境变量未设置: {env_var}")
            return env_val
        return value

    def resolve_path(self, path: str) -> str:
        """将相对路径解析为项目根目录下的绝对路径"""
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = (self.base_dir / p)
        return str(p.resolve())

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

        client_config = {
            k: self._resolve_env_value(v) for k, v in clients[client_name].items()
        }

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
        storage_config = {
            k: self._resolve_env_value(v) for k, v in storage_config.items()
        }

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
        config = self.config.get('literature_search', {
            'enabled': True,
            'method': 'keyword',
            'knowledge_base_path': 'knowledge_base',
            'top_k': 3
        })
        if 'knowledge_base_path' in config:
            config = config.copy()
            config['knowledge_base_path'] = self.resolve_path(config['knowledge_base_path'])
        return config

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

        return self.resolve_path(prompt_file)
