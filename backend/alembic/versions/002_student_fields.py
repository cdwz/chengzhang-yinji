"""add student fields and fix column names

Revision ID: 002_student_fields
Revises: 001_initial
Create Date: 2026-05-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_student_fields'
down_revision = 'initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 重命名 student_no 为 student_number
    op.alter_column('students', 'student_no', new_column_name='student_number')
    
    # 修改 student_number 为可空
    op.alter_column('students', 'student_number', nullable=True)
    
    # 添加 gender 字段
    op.add_column('students', sa.Column('gender', sa.String(10), server_default='male'))
    
    # 添加 birth_date 字段
    op.add_column('students', sa.Column('birth_date', sa.Date(), nullable=True))
    
    # 添加 study_group_id 字段
    op.add_column('students', sa.Column('study_group_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # 添加外键约束
    op.create_foreign_key('fk_students_study_group', 'students', 'study_groups', ['study_group_id'], ['id'])


def downgrade() -> None:
    # 删除外键约束
    op.drop_constraint('fk_students_study_group', 'students', type_='foreignkey')
    
    # 删除字段
    op.drop_column('students', 'study_group_id')
    op.drop_column('students', 'birth_date')
    op.drop_column('students', 'gender')
    
    # 重命名回 student_no
    op.alter_column('students', 'student_number', new_column_name='student_no')
    
    # 恢复非空约束
    op.alter_column('students', 'student_no', nullable=False)
