"""数据模型定义"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# SQLAlchemy ORM models
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SchoolType(str, Enum):
    """流派类型"""
    TRADITIONAL = "traditional"  # 传统正宗派
    XIANGSHU = "xiangshu"        # 象数派
    MANGPAI = "mangpai"          # 盲派


class LineInfo(BaseModel):
    """爻信息"""
    position: int                  # 爻位（1-6）
    shen: str                      # 六神
    liuqin: str                    # 六亲
    wuxing: str                    # 五行
    dizhi: str                     # 地支
    yin_yang: str                  # 阴阳
    shi_ying: Optional[str] = None # 世应标记
    change_info: Optional[str] = None  # 变卦信息（如有）


class HexagramInput(BaseModel):
    """卦象输入数据结构"""
    original_text: str              # 原始文本
    system_name: str                # 系统名称（如"灵光象吉"）
    datetime: str                   # 占卜时间
    question: str                   # 占问问题

    ganzhi: Dict[str, str]          # 年月日时干支
    kongwang: Dict[str, str]        # 空亡信息

    ben_gua: str                    # 本卦信息
    ben_gua_name: str               # 本卦名称
    ben_gua_gong: str               # 本卦所属宫
    ben_gua_index: int              # 本卦序号
    ben_gua_type: str               # 本卦类型（如"归魂"、"游魂"）

    bian_gua: str                   # 变卦信息
    bian_gua_name: str              # 变卦名称
    bian_gua_gong: str              # 变卦所属宫
    bian_gua_index: int             # 变卦序号

    lines: List[LineInfo]           # 六爻详情


class LiteratureRef(BaseModel):
    """文献引用"""
    book_title: str       # 书名
    volume: str           # 卷数
    chapter: str          # 章节
    original_text: str    # 原文引用
    keyword: str          # 关键词
    school: SchoolType    # 流派


class AgentResponse(BaseModel):
    """Agent 响应数据结构"""
    agent_name: str               # Agent 名称
    school: SchoolType            # 流派
    content: str                  # 响应内容
    confidence: float = Field(ge=0, le=10)  # 置信度（0-10）
    literature_refs: List[LiteratureRef] = Field(default_factory=list, alias="references")  # 引用的文献
    round_number: int             # 轮次
    metadata: Dict[str, Any] = Field(default_factory=dict)  # 元数据（model, usage等）
    timestamp: datetime = Field(default_factory=datetime.now)  # 时间戳


class DebateState(str, Enum):
    """辩论状态"""
    INIT = "init"                              # 初始化
    INITIAL_INTERPRETATION = "initial_interpretation"  # 初始解读
    DEBATING = "debating"                      # 辩论中
    CONVERGED = "converged"                    # 已收敛
    MAX_ROUNDS_REACHED = "max_rounds_reached"  # 达到最大轮数
    FINISHED = "finished"                      # 已完成


class DebateContext(BaseModel):
    """辩论上下文"""
    hexagram: HexagramInput              # 卦象输入
    agents: List[str]                    # Agent 名称列表
    history: List[Dict[str, Any]]        # 历史记录
    current_round: int                   # 当前轮次
    state: DebateState                   # 辩论状态
    convergence_score: float = Field(ge=0, le=1, default=0.0)  # 收敛分数（0-1）

    class Config:
        use_enum_values = True


class RoundRecord(BaseModel):
    """轮次记录"""
    round: int                          # 轮次
    stage: str                          # 阶段（"initial_interpretation" 或 "debate"）
    responses: List[AgentResponse]      # Agent 响应列表
    timestamp: datetime = Field(default_factory=datetime.now)  # 时间戳


class DebateRecord(BaseModel):
    """辩论记录表（用于数据库存储）"""
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    hexagram_input: str                 # JSON 字符串
    debate_history: str                # JSON 字符串
    final_report: str                  # Markdown 格式

    convergence_round: int             # 收敛轮次
    convergence_score: float           # 收敛分数
    total_tokens_used: int             # 总 token 使用量

    class Config:
        from_attributes = True


class AgentResponseRecord(BaseModel):
    """Agent 响应记录表（用于数据库存储）"""
    id: Optional[int] = None
    debate_id: int                     # 关联的辩论记录 ID
    round_number: int                  # 轮次
    agent_name: str                    # Agent 名称
    school: SchoolType                 # 流派
    content: str                       # 响应内容
    confidence: float                  # 置信度
    literature_refs: str               # JSON 字符串
    timestamp: datetime = Field(default_factory=datetime.now)  # 时间戳

    class Config:
        from_attributes = True


# ==================== SQLAlchemy ORM Models ====================

class DebateRecordORM(Base):
    """辩论记录表（SQLAlchemy ORM）"""
    __tablename__ = 'debate_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    hexagram_input = Column(Text, nullable=False)  # JSON字符串
    debate_history = Column(Text, nullable=False)  # JSON字符串
    final_report = Column(Text)  # Markdown格式

    convergence_round = Column(Integer)  # 收敛轮次
    convergence_score = Column(Float)  # 收敛分数
    total_tokens_used = Column(Integer, default=0)  # 总token使用量

    # 关系
    responses = relationship("AgentResponseRecordORM", back_populates="debate",
                           cascade="all, delete-orphan")

    def to_pydantic(self) -> 'DebateRecord':
        """转换为Pydantic模型"""
        return DebateRecord(
            id=self.id,
            timestamp=self.timestamp,
            hexagram_input=self.hexagram_input,
            debate_history=self.debate_history,
            final_report=self.final_report,
            convergence_round=self.convergence_round,
            convergence_score=self.convergence_score,
            total_tokens_used=self.total_tokens_used
        )


class AgentResponseRecordORM(Base):
    """Agent响应记录表（SQLAlchemy ORM）"""
    __tablename__ = 'agent_responses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    debate_id = Column(Integer, ForeignKey('debate_records.id'), nullable=False)
    round_number = Column(Integer, nullable=False)

    agent_name = Column(String(100), nullable=False)
    school = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    literature_refs = Column(Text)  # JSON字符串
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    debate = relationship("DebateRecordORM", back_populates="responses")

    def to_pydantic(self) -> 'AgentResponseRecord':
        """转换为Pydantic模型"""
        return AgentResponseRecord(
            id=self.id,
            debate_id=self.debate_id,
            round_number=self.round_number,
            agent_name=self.agent_name,
            school=SchoolType(self.school),
            content=self.content,
            confidence=self.confidence,
            literature_refs=self.literature_refs,
            timestamp=self.timestamp
        )
