"""数据库管理器 - 处理所有数据库CRUD操作"""
import json
from contextlib import contextmanager
from typing import Optional, List
from datetime import datetime
from loguru import logger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from config.config_loader import Config
from storage.models import (
    DebateContext,
    DebateRecord,
    AgentResponseRecord,
    DebateRecordORM,
    AgentResponseRecordORM,
    Base
)


class DatabaseManager:
    """数据库会话和CRUD操作管理器"""

    def __init__(self, config: Config):
        """
        初始化数据库连接

        Args:
            config: 配置对象
        """
        self.storage_config = config.get_storage_config()
        db_url = self.storage_config['url']

        logger.info(f"初始化数据库连接: {db_url}")

        # 创建引擎
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
            poolclass=StaticPool if "sqlite" in db_url else None,
            echo=False  # 设置为True可查看SQL查询日志
        )

        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # 创建表
        self._create_tables()

        logger.info("数据库初始化完成")

    def _create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建完成")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise

    @contextmanager
    def get_session(self) -> Session:
        """
        获取数据库会话上下文管理器

        使用示例:
            with database.get_session() as session:
                # 数据库操作
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败，已回滚: {e}")
            raise
        finally:
            session.close()

    def save_debate(self, context: DebateContext, final_report: str) -> DebateRecord:
        """
        保存完整辩论到数据库

        Args:
            context: 辩论上下文
            final_report: 生成的markdown报告

        Returns:
            DebateRecord: 保存的记录（包含数据库ID）
        """
        logger.info("保存辩论到数据库")

        try:
            with self.get_session() as session:
                # 计算总token使用量
                total_tokens = 0
                for round_data in context.history:
                    for resp in round_data.get('responses', []):
                        metadata = resp.get('metadata', {})
                        usage = metadata.get('usage', {})
                        if isinstance(usage, dict):
                            total_tokens += usage.get('total_tokens', 0)

                # 创建辩论记录
                debate_record_orm = DebateRecordORM(
                    timestamp=datetime.utcnow(),
                    hexagram_input=context.hexagram.json(),
                    debate_history=json.dumps(
                        context.history,
                        ensure_ascii=False,
                        indent=2,
                        default=str
                    ),
                    final_report=final_report,
                    convergence_round=context.current_round,
                    convergence_score=context.convergence_score,
                    total_tokens_used=total_tokens
                )

                session.add(debate_record_orm)
                session.flush()  # 获取ID

                # 保存所有Agent响应
                for round_data in context.history:
                    for resp in round_data.get('responses', []):
                        # 处理响应数据
                        resp_dict = resp if isinstance(resp, dict) else resp.model_dump()

                        resp_record_orm = AgentResponseRecordORM(
                            debate_id=debate_record_orm.id,
                            round_number=resp_dict.get('round_number', 0),
                            agent_name=resp_dict.get('agent_name', ''),
                            school=resp_dict.get('school', ''),
                            content=resp_dict.get('content', ''),
                            confidence=resp_dict.get('confidence', 0.0),
                            literature_refs=json.dumps(
                                resp_dict.get('references', resp_dict.get('literature_refs', [])),
                                ensure_ascii=False,
                                default=str
                            ),
                            timestamp=resp_dict.get('timestamp', datetime.utcnow())
                        )
                        session.add(resp_record_orm)

                session.commit()
                logger.info(f"辩论已保存，ID: {debate_record_orm.id}")

                return debate_record_orm.to_pydantic()

        except Exception as e:
            logger.exception(f"保存辩论失败: {e}")
            raise

    def load_debate(self, debate_id: int) -> Optional[DebateRecord]:
        """
        加载辩论记录

        Args:
            debate_id: 数据库ID

        Returns:
            DebateRecord or None if not found
        """
        logger.info(f"加载辩论记录: {debate_id}")

        try:
            with self.get_session() as session:
                record = session.query(DebateRecordORM).filter(
                    DebateRecordORM.id == debate_id
                ).first()

                if record:
                    logger.info(f"辩论记录加载成功: {debate_id}")
                    return record.to_pydantic()
                else:
                    logger.warning(f"未找到辩论记录: {debate_id}")
                    return None

        except Exception as e:
            logger.exception(f"加载辩论失败: {e}")
            raise

    def list_debates(self, limit: int = 100, offset: int = 0) -> List[DebateRecord]:
        """
        列出辩论记录

        Args:
            limit: 最大返回数量
            offset: 偏移量

        Returns:
            List[DebateRecord]: 辩论记录列表
        """
        logger.info(f"列出辩论记录: limit={limit}, offset={offset}")

        try:
            with self.get_session() as session:
                records = session.query(DebateRecordORM).order_by(
                    DebateRecordORM.timestamp.desc()
                ).limit(limit).offset(offset).all()

                result = [r.to_pydantic() for r in records]
                logger.info(f"找到 {len(result)} 条辩论记录")

                return result

        except Exception as e:
            logger.exception(f"列出辩论记录失败: {e}")
            raise

    def delete_debate(self, debate_id: int) -> bool:
        """
        删除辩论记录

        Args:
            debate_id: 数据库ID

        Returns:
            bool: 是否删除成功
        """
        logger.info(f"删除辩论记录: {debate_id}")

        try:
            with self.get_session() as session:
                record = session.query(DebateRecordORM).filter(
                    DebateRecordORM.id == debate_id
                ).first()

                if record:
                    session.delete(record)
                    session.commit()
                    logger.info(f"辩论记录已删除: {debate_id}")
                    return True
                else:
                    logger.warning(f"未找到辩论记录: {debate_id}")
                    return False

        except Exception as e:
            logger.exception(f"删除辩论记录失败: {e}")
            raise

    def get_debate_count(self) -> int:
        """
        获取辩论记录总数

        Returns:
            int: 记录总数
        """
        try:
            with self.get_session() as session:
                count = session.query(DebateRecordORM).count()
                return count
        except Exception as e:
            logger.exception(f"获取辩论数量失败: {e}")
            raise

    def search_debates(self,
                     keyword: str,
                     limit: int = 100) -> List[DebateRecord]:
        """
        搜索辩论记录（简单关键词搜索）

        Args:
            keyword: 搜索关键词
            limit: 最大返回数量

        Returns:
            List[DebateRecord]: 匹配的辩论记录列表
        """
        logger.info(f"搜索辩论记录: keyword={keyword}, limit={limit}")

        try:
            with self.get_session() as session:
                # 在问题字段中搜索关键词
                records = session.query(DebateRecordORM).filter(
                    DebateRecordORM.hexagram_input.like(f'%{keyword}%')
                ).order_by(
                    DebateRecordORM.timestamp.desc()
                ).limit(limit).all()

                result = [r.to_pydantic() for r in records]
                logger.info(f"找到 {len(result)} 条匹配记录")

                return result

        except Exception as e:
            logger.exception(f"搜索辩论记录失败: {e}")
            raise

    def get_recent_debates(self, days: int = 7, limit: int = 100) -> List[DebateRecord]:
        """
        获取最近的辩论记录

        Args:
            days: 最近天数
            limit: 最大返回数量

        Returns:
            List[DebateRecord]: 最近的辩论记录列表
        """
        logger.info(f"获取最近 {days} 天的辩论记录")

        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            with self.get_session() as session:
                records = session.query(DebateRecordORM).filter(
                    DebateRecordORM.timestamp >= cutoff_date
                ).order_by(
                    DebateRecordORM.timestamp.desc()
                ).limit(limit).all()

                result = [r.to_pydantic() for r in records]
                logger.info(f"找到 {len(result)} 条最近的辩论记录")

                return result

        except Exception as e:
            logger.exception(f"获取最近辩论记录失败: {e}")
            raise
