"""初始化数据库

Revision ID: initial
Create Date: 2026-05-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 用户表
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('phone', sa.String(11), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_users_phone', 'users', ['phone'])

    # 行政区划表
    op.create_table(
        'regions',
        sa.Column('code', sa.String(6), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('parent_code', sa.String(6), sa.ForeignKey('regions.code')),
        sa.Column('level', sa.SmallInteger),
    )

    # 学校表
    op.create_table(
        'schools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('province_code', sa.String(6)),
        sa.Column('city_code', sa.String(6)),
        sa.Column('district_code', sa.String(6)),
        sa.Column('address', sa.String(200)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 学校管理员表
    op.create_table(
        'school_admins',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 年级表
    op.create_table(
        'grades',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id'), nullable=False),
        sa.Column('name', sa.String(20), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 班级表
    op.create_table(
        'classes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('grade_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grades.id'), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('homeroom_teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('invite_code', sa.String(10), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 学生表
    op.create_table(
        'students',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id'), nullable=False),
        sa.Column('student_no', sa.String(20), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(60)),
    )
    op.create_unique_constraint('uq_student_class_no', 'students', ['class_id', 'student_no'])
    op.create_index('ix_students_class', 'students', ['class_id'])

    # 家长学生绑定表
    op.create_table(
        'parent_students',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('relationship', sa.String(20), default='家长'),
    )
    op.create_unique_constraint('uq_parent_student', 'parent_students', ['parent_id', 'student_id'])

    # 学习小组表
    op.create_table(
        'study_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id'), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0),
    )

    # 学生小组关联表
    op.create_table(
        'student_groups',
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id'), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study_groups.id'), primary_key=True),
    )

    # 任教关系表
    op.create_table(
        'teaching_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id'), nullable=False),
        sa.Column('subject', sa.String(50), nullable=False),
        sa.Column('is_homeroom', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_teaching', 'teaching_assignments', ['teacher_id', 'class_id', 'subject'])

    # 自主学习任务表
    op.create_table(
        'learning_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id'), nullable=False),
        sa.Column('subject', sa.String(50), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('study_groups.id')),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('suggested_duration', sa.Integer()),
        sa.Column('task_date', sa.Date(), nullable=False),
        sa.Column('is_optional', sa.Boolean(), default=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_tasks_class_date', 'learning_tasks', ['class_id', 'task_date'])

    # 任务附件表
    op.create_table(
        'task_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_tasks.id'), nullable=False),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 任务提交记录表
    op.create_table(
        'task_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_tasks.id'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('feedback', sa.Text()),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_submission_task_student', 'task_submissions', ['task_id', 'student_id'])
    op.create_index('ix_submissions_task', 'task_submissions', ['task_id'])

    # 提交图片表
    op.create_table(
        'submission_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_submissions.id'), nullable=False),
        sa.Column('original_url', sa.String(500), nullable=False),
        sa.Column('processed_url', sa.String(500)),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 教师批注表
    op.create_table(
        'teacher_annotations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('image_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submission_images.id'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('annotation_data', postgresql.JSONB()),
        sa.Column('is_viewed', sa.Boolean(), default=False),
        sa.Column('is_example', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 评价维度表
    op.create_table(
        'evaluation_dimensions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('subject', sa.String(50)),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 评价记录表
    op.create_table(
        'evaluation_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dimension_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evaluation_dimensions.id'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('record_date', sa.Date(), nullable=False),
        sa.Column('value', sa.Text()),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_eval_record', 'evaluation_records', ['dimension_id', 'student_id', 'record_date'])
    op.create_index('ix_evaluations_dimension_date', 'evaluation_records', ['dimension_id', 'record_date'])
    op.create_index('ix_evaluations_student', 'evaluation_records', ['student_id'])

    # 成长成就表
    op.create_table(
        'achievements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('achievement_type', sa.String(50), nullable=False),
        sa.Column('achievement_data', postgresql.JSONB()),
        sa.Column('earned_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 站内消息表
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('receiver_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('title', sa.String(200)),
        sa.Column('content', sa.Text()),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 数据访问日志表
    op.create_table(
        'access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('viewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('target_student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id')),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('access_logs')
    op.drop_table('messages')
    op.drop_table('achievements')
    op.drop_table('evaluation_records')
    op.drop_table('evaluation_dimensions')
    op.drop_table('teacher_annotations')
    op.drop_table('submission_images')
    op.drop_table('task_submissions')
    op.drop_table('task_attachments')
    op.drop_table('learning_tasks')
    op.drop_table('teaching_assignments')
    op.drop_table('student_groups')
    op.drop_table('study_groups')
    op.drop_table('parent_students')
    op.drop_table('students')
    op.drop_table('classes')
    op.drop_table('grades')
    op.drop_table('school_admins')
    op.drop_table('schools')
    op.drop_table('regions')
    op.drop_table('users')
