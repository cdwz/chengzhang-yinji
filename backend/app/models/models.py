"""
成长印记 - 数据模型
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Integer, 
    Text, Date, Numeric, SmallInteger, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone = Column(String(11), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)  # super_admin, school_admin, teacher, parent
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    school_admins = relationship("SchoolAdmin", back_populates="user")
    teaching_assignments = relationship("TeachingAssignment", back_populates="teacher")
    parent_students = relationship("ParentStudent", back_populates="parent")


class Region(Base):
    """行政区划表"""
    __tablename__ = "regions"
    
    code = Column(String(6), primary_key=True)
    name = Column(String(50), nullable=False)
    parent_code = Column(String(6), ForeignKey("regions.code"), nullable=True)
    level = Column(SmallInteger)  # 1:省, 2:市, 3:区
    
    # 关系
    children = relationship("Region", backref="parent", remote_side=[code])


class School(Base):
    """学校表"""
    __tablename__ = "schools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    province_code = Column(String(6))
    city_code = Column(String(6))
    district_code = Column(String(6))
    address = Column(String(200))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    grades = relationship("Grade", back_populates="school", cascade="all, delete-orphan")
    admins = relationship("SchoolAdmin", back_populates="school")


class SchoolAdmin(Base):
    """学校管理员表"""
    __tablename__ = "school_admins"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # 是否主管理员
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    school = relationship("School", back_populates="admins")
    user = relationship("User", back_populates="school_admins")


class Grade(Base):
    """年级表"""
    __tablename__ = "grades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    name = Column(String(20), nullable=False)  # 如"一年级"
    year = Column(Integer, nullable=False)  # 学年
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    school = relationship("School", back_populates="grades")
    classes = relationship("Class", back_populates="grade", cascade="all, delete-orphan")


class Class(Base):
    """班级表"""
    __tablename__ = "classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False)
    name = Column(String(50), nullable=False)  # 如"一年级1班"
    homeroom_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    invite_code = Column(String(10), unique=True, nullable=False)  # 家长绑定用
    subjects = Column(JSONB, default=list)  # 班级启用科目列表，默认["语文","数学","英语"]
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    grade = relationship("Grade", back_populates="classes")
    students = relationship("Student", back_populates="class_", cascade="all, delete-orphan")
    study_groups = relationship("StudyGroup", back_populates="class_", cascade="all, delete-orphan")
    tasks = relationship("LearningTask", back_populates="class_", cascade="all, delete-orphan")
    evaluation_dimensions = relationship("EvaluationDimension", back_populates="class_", cascade="all, delete-orphan")


class Student(Base):
    """学生表"""
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    student_number = Column(String(20), nullable=True)  # 学号
    name = Column(String(50), nullable=False)
    gender = Column(String(10), default="male")  # 性别: male/female
    birth_date = Column(Date, nullable=True)  # 出生日期
    display_name = Column(String(60))  # 重名时附加标识
    study_group_id = Column(UUID(as_uuid=True), ForeignKey("study_groups.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("class_id", "student_number", name="uq_student_class_no"),
    )
    
    # 关系
    class_ = relationship("Class", back_populates="students")
    study_group = relationship("StudyGroup", back_populates="students")
    parent_students = relationship("ParentStudent", back_populates="student", cascade="all, delete-orphan")
    student_groups = relationship("StudentGroup", back_populates="student", cascade="all, delete-orphan")


class ParentStudent(Base):
    """家长学生绑定表"""
    __tablename__ = "parent_students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    relation_type = Column(String(20), default="家长")  # 父亲、母亲、其他
    
    __table_args__ = (
        UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),
    )
    
    # 关系
    parent = relationship("User", back_populates="parent_students")
    student = relationship("Student", back_populates="parent_students")


class StudyGroup(Base):
    """学习小组表"""
    __tablename__ = "study_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    
    # 关系
    class_ = relationship("Class", back_populates="study_groups")
    students = relationship("Student", back_populates="study_group")
    student_groups = relationship("StudentGroup", back_populates="group", cascade="all, delete-orphan")
    tasks = relationship("LearningTask", back_populates="group")


class StudentGroup(Base):
    """学生小组关联表"""
    __tablename__ = "student_groups"
    
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), primary_key=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("study_groups.id"), primary_key=True)
    
    # 关系
    student = relationship("Student", back_populates="student_groups")
    group = relationship("StudyGroup", back_populates="student_groups")


class TeachingAssignment(Base):
    """任教关系表"""
    __tablename__ = "teaching_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    subject = Column(String(50), nullable=False)  # 科目
    is_homeroom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("teacher_id", "class_id", "subject", name="uq_teaching"),
    )
    
    # 关系
    teacher = relationship("User", back_populates="teaching_assignments")


class LearningTask(Base):
    """自主学习任务表"""
    __tablename__ = "learning_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    subject = Column(String(50), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("study_groups.id"))  # NULL表示全班
    target_type = Column(String(20), default='all')  # all/groups/students
    target_ids = Column(JSONB, default=list)  # 目标小组或学生ID列表
    title = Column(String(200), nullable=False)
    content = Column(Text)
    suggested_duration = Column(Integer)  # 建议时长（分钟）
    task_date = Column(Date, nullable=False)
    task_period = Column(String(10), default='day')  # day/week/month - 任务周期类型
    weekend_required = Column(Boolean, default=True)  # 周末是否需要完成
    holiday_required = Column(Boolean, default=False)  # 节假日是否需要完成
    is_optional = Column(Boolean, default=True)  # 必须为TRUE（合规）
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    class_ = relationship("Class", back_populates="tasks")
    group = relationship("StudyGroup", back_populates="tasks")
    submissions = relationship("TaskSubmission", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")


class TaskAttachment(Base):
    """任务附件表"""
    __tablename__ = "task_attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("learning_tasks.id"), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    task = relationship("LearningTask", back_populates="attachments")


class TaskSubmission(Base):
    """任务提交记录表"""
    __tablename__ = "task_submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("learning_tasks.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    feedback = Column(Text)  # 家长选填反馈
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("task_id", "student_id", name="uq_submission_task_student"),
    )
    
    # 关系
    task = relationship("LearningTask", back_populates="submissions")
    images = relationship("SubmissionImage", back_populates="submission", cascade="all, delete-orphan")


class SubmissionImage(Base):
    """提交图片表"""
    __tablename__ = "submission_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("task_submissions.id"), nullable=False)
    original_url = Column(String(500), nullable=False)
    processed_url = Column(String(500))  # 处理后图片
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    submission = relationship("TaskSubmission", back_populates="images")
    annotations = relationship("TeacherAnnotation", back_populates="image", cascade="all, delete-orphan")


class TeacherAnnotation(Base):
    """教师批注表"""
    __tablename__ = "teacher_annotations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("submission_images.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    annotation_data = Column(JSONB)  # 存储圈画数据
    is_viewed = Column(Boolean, default=False)
    is_example = Column(Boolean, default=False)  # 典范例
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    image = relationship("SubmissionImage", back_populates="annotations")


class EvaluationDimension(Base):
    """评价维度表"""
    __tablename__ = "evaluation_dimensions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    name = Column(String(100), nullable=False)
    subject = Column(String(50))
    type = Column(String(20), nullable=False)  # star, grade, boolean, score, ab_score, text
    config = Column(JSONB, default=dict)  # 类型配置：score -> {score_type, max_score}, ab_score -> {total, a_score, b_score}
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    class_ = relationship("Class", back_populates="evaluation_dimensions")
    records = relationship("EvaluationRecord", back_populates="dimension", cascade="all, delete-orphan")


class EvaluationRecord(Base):
    """评价记录表"""
    __tablename__ = "evaluation_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dimension_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_dimensions.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    record_date = Column(Date, nullable=False)
    value = Column(Text)  # 根据type存储不同格式
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("dimension_id", "student_id", "record_date", name="uq_eval_record"),
    )
    
    # 关系
    dimension = relationship("EvaluationDimension", back_populates="records")


class Achievement(Base):
    """成长成就表"""
    __tablename__ = "achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    achievement_type = Column(String(50), nullable=False)
    achievement_data = Column(JSONB)
    earned_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    """站内消息表"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String(200))
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AccessLog(Base):
    """数据访问日志表"""
    __tablename__ = "access_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    viewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    target_student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"))
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
