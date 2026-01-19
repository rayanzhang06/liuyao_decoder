"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-01-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建辩论记录表
    op.create_table(
        'debate_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('hexagram_input', sa.Text(), nullable=False),
        sa.Column('debate_history', sa.Text(), nullable=False),
        sa.Column('final_report', sa.Text(), nullable=True),
        sa.Column('convergence_round', sa.Integer(), nullable=True),
        sa.Column('convergence_score', sa.Float(), nullable=True),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_debate_records_timestamp', 'debate_records', ['timestamp'])

    # 创建Agent响应记录表
    op.create_table(
        'agent_responses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('debate_id', sa.Integer(), nullable=False),
        sa.Column('round_number', sa.Integer(), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('school', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('literature_refs', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['debate_id'], ['debate_records.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_responses_debate_id', 'agent_responses', ['debate_id'])
    op.create_index('ix_agent_responses_round_number', 'agent_responses', ['round_number'])


def downgrade() -> None:
    op.drop_index('ix_agent_responses_round_number', table_name='agent_responses')
    op.drop_index('ix_agent_responses_debate_id', table_name='agent_responses')
    op.drop_table('agent_responses')

    op.drop_index('ix_debate_records_timestamp', table_name='debate_records')
    op.drop_table('debate_records')
