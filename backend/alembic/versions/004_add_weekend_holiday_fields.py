"""添加周末和节假日字段到learning_tasks表

Revision ID: add_weekend_holiday_fields
Revises: 003_student_created_at
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_weekend_holiday_fields'
down_revision: Union[str, None] = '003_student_created_at'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 weekend_required 字段，默认值为 True
    op.add_column('learning_tasks', 
        sa.Column('weekend_required', sa.Boolean(), server_default='true', nullable=True)
    )
    
    # 添加 holiday_required 字段，默认值为 False
    op.add_column('learning_tasks', 
        sa.Column('holiday_required', sa.Boolean(), server_default='false', nullable=True)
    )
    
    # 添加 task_period 字段，默认值为 'day'
    op.add_column('learning_tasks',
        sa.Column('task_period', sa.String(10), server_default='day', nullable=True)
    )
    
    # 添加 target_type 字段
    op.add_column('learning_tasks',
        sa.Column('target_type', sa.String(20), server_default='all', nullable=True)
    )
    
    # 添加 target_ids 字段（JSONB）
    op.add_column('learning_tasks',
        sa.Column('target_ids', sa.JSON(), nullable=True)
    )
    
    # 更新现有记录的默认值
    op.execute("UPDATE learning_tasks SET weekend_required = true WHERE weekend_required IS NULL")
    op.execute("UPDATE learning_tasks SET holiday_required = false WHERE holiday_required IS NULL")
    op.execute("UPDATE learning_tasks SET task_period = 'day' WHERE task_period IS NULL")
    op.execute("UPDATE learning_tasks SET target_type = 'all' WHERE target_type IS NULL")
    
    # 将字段设置为 NOT NULL
    op.alter_column('learning_tasks', 'weekend_required', nullable=False)
    op.alter_column('learning_tasks', 'holiday_required', nullable=False)
    op.alter_column('learning_tasks', 'task_period', nullable=False)
    op.alter_column('learning_tasks', 'target_type', nullable=False)


def downgrade() -> None:
    # 删除添加的字段
    op.drop_column('learning_tasks', 'target_ids')
    op.drop_column('learning_tasks', 'target_type')
    op.drop_column('learning_tasks', 'task_period')
    op.drop_column('learning_tasks', 'holiday_required')
    op.drop_column('learning_tasks', 'weekend_required')