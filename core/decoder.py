"""六爻解码核心业务逻辑"""
import asyncio
from pathlib import Path
from typing import Optional, Callable
from loguru import logger

from config.config_loader import Config
from utils.parser import HexagramParser
from agents.orchestrator import DebateOrchestrator
from utils.report_generator import ReportGenerator
from storage.models import HexagramInput
from storage.database import DatabaseManager


class LiuyaoDecoder:
    """六爻解码器 - 核心业务逻辑（无UI依赖）"""

    def __init__(self, config: Optional[Config] = None):
        """
        初始化解码器

        Args:
            config: 配置对象，如果为None则创建默认配置
        """
        self.config = config or Config()
        self.parser = HexagramParser()
        self.report_generator = ReportGenerator()
        self.database = DatabaseManager(self.config)
        self._orchestrator = None

    def _get_orchestrator(self) -> DebateOrchestrator:
        """获取或创建 DebateOrchestrator（延迟初始化）"""
        if self._orchestrator is None:
            self._orchestrator = DebateOrchestrator(self.config)
        return self._orchestrator

    async def decode(self,
                     text: str,
                     save_to_db: bool = False,
                     output_file: Optional[str] = None,
                     progress_callback: Optional[Callable] = None) -> dict:
        """
        解码卦象文本

        Args:
            text: 卦象文本（遵循prompt_v2.md格式）
            save_to_db: 是否保存到数据库
            output_file: 可选的输出报告文件路径
            progress_callback: 可选的进度回调函数

        Returns:
            dict: 包含以下键的字典:
                - report: markdown格式的报告
                - hexagram: 解析后的卦象对象
                - context: 辩论上下文
                - output_path: 输出文件路径（如果指定）
        """
        try:
            # Stage 1: 解析卦象
            hexagram = self.parser.parse_text(text)
            logger.info(f"卦象解析成功: {hexagram.ben_gua_name} → {hexagram.bian_gua_name}")

            # 触发回调：解析完成
            if progress_callback:
                progress_callback("parsed", {"hexagram": hexagram})

            # Stage 2: 运行辩论
            max_rounds = self.config.get_debate_config()['max_rounds']

            # 运行辩论
            context = await self._get_orchestrator().run_debate(
                hexagram,
                progress_callback=progress_callback
            )

            logger.info(f"辩论完成，总轮次: {context.current_round}, 收敛分数: {context.convergence_score:.2f}")

            # Stage 3: 生成报告
            report = self.report_generator.generate_report(context)
            logger.info("报告生成成功")

            # Stage 4: 保存到文件（如果指定）
            output_path = None
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(report, encoding='utf-8')
                logger.info(f"报告已保存: {output_path}")

            # Stage 5: 保存到数据库（如果启用）
            if save_to_db:
                record = self.database.save_debate(context, report)
                logger.info(f"已保存到数据库 (ID: {record.id})")

            return {
                "report": report,
                "hexagram": hexagram,
                "context": context,
                "output_path": output_path
            }

        except Exception as e:
            logger.exception("解码失败")
            raise

    def get_history(self, limit: int = 20, offset: int = 0):
        """获取历史记录"""
        return self.database.list_debates(limit=limit, offset=offset)

    def get_record(self, record_id: int):
        """获取单条记录"""
        return self.database.load_debate(record_id)

    def delete_record(self, record_id: int) -> bool:
        """删除记录"""
        return self.database.delete_debate(record_id)
