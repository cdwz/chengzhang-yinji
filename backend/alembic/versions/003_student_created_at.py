"""add student created_at

Revision ID: 003_student_created_at
Revises: 002_student_fields
Create Date: 2026-05-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_student_created_at'
down_revision = '002_student_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('students', sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')))


def downgrade() -> None:
    op.drop_column('students', 'created_at')
