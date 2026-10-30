import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
    JSON,
    func,
)
from sqlalchemy.orm import relationship
from app.database.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    topic_progress = relationship("TopicProgress", back_populates="user", cascade="all, delete-orphan")
    unit_progress = relationship("UnitProgress", back_populates="user", cascade="all, delete-orphan")
    subject_progress = relationship("SubjectProgress", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    syllabus_text = Column(Text, nullable=True)
    pyq_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="subjects")
    units = relationship("Unit", back_populates="subject", cascade="all, delete-orphan", order_by="Unit.order_index")
    progress = relationship("SubjectProgress", back_populates="subject", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)
    syllabus_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    subject = relationship("Subject", back_populates="units")
    document = relationship("Document", back_populates="unit", uselist=False, cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="unit", cascade="all, delete-orphan")
    progress = relationship("UnitProgress", back_populates="unit", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    unit_id = Column(String(36), ForeignKey("units.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # PDF, PPTX, DOCX, TXT, IMAGE
    file_size = Column(Integer, nullable=False)  # in bytes
    file_path = Column(String(500), nullable=False)
    page_count = Column(Integer, nullable=True)
    slide_count = Column(Integer, nullable=True)
    resource_type = Column(String(50), nullable=False, default="STUDY_RESOURCE")  # SYLLABUS, STUDY_RESOURCE, PYQ
    processing_status = Column(String(50), nullable=False, default="UPLOADED")  # UPLOADED, PROCESSING, PROCESSED, FAILED, REVIEW_REQUIRED
    processing_error = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    unit = relationship("Unit", back_populates="document")
    topics = relationship("Topic", back_populates="document", cascade="all, delete-orphan", order_by="Topic.order_index")
    source_regions = relationship("SourceRegion", back_populates="document", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Grounded in source
    order_index = Column(Integer, nullable=False, index=True)  # Mandatory: matches source order
    source_start = Column(String(100), nullable=True)  # Page/slide or offset
    source_end = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    status = Column(String(50), nullable=False, default="EXTRACTED")  # EXTRACTED, VERIFIED, REVIEW_REQUIRED
    learning_data = Column(JSON, nullable=True)  # Structured learning content: definitions, mind map, flowchart, keywords
    pyq_frequency = Column(Integer, nullable=False, default=0)
    pyq_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    document = relationship("Document", back_populates="topics")
    subtopics = relationship("Subtopic", back_populates="topic", cascade="all, delete-orphan", order_by="Subtopic.order_index")
    source_regions = relationship("SourceRegion", back_populates="topic", cascade="all, delete-orphan", order_by="SourceRegion.element_order")
    quizzes = relationship("Quiz", back_populates="topic", cascade="all, delete-orphan")
    progress = relationship("TopicProgress", back_populates="topic", cascade="all, delete-orphan")


class Subtopic(Base):
    __tablename__ = "subtopics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Grounded in source
    order_index = Column(Integer, nullable=False)  # Matches source order
    source_start = Column(String(100), nullable=True)
    source_end = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    status = Column(String(50), nullable=False, default="EXTRACTED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    topic = relationship("Topic", back_populates="subtopics")
    source_regions = relationship("SourceRegion", back_populates="subtopic")


class SourceRegion(Base):
    __tablename__ = "source_regions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    subtopic_id = Column(String(36), ForeignKey("subtopics.id", ondelete="SET NULL"), nullable=True, index=True)
    page_number = Column(Integer, nullable=True)  # 1-indexed for PDF
    slide_number = Column(Integer, nullable=True)  # 1-indexed for PPTX
    region_type = Column(String(50), nullable=False)  # TEXT, IMAGE, TABLE, DIAGRAM, EQUATION, FLOWCHART, FULL_PAGE, SLIDE
    x1 = Column(Float, nullable=True)
    y1 = Column(Float, nullable=True)
    x2 = Column(Float, nullable=True)
    y2 = Column(Float, nullable=True)
    element_order = Column(Integer, nullable=False, default=0)
    source_reference = Column(String(255), nullable=True)
    content_text = Column(Text, nullable=True)
    content_html = Column(Text, nullable=True)
    media_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="source_regions")
    topic = relationship("Topic", back_populates="source_regions")
    subtopic = relationship("Subtopic", back_populates="source_regions")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)
    unit_id = Column(String(36), ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_type = Column(String(50), nullable=False, default="TOPIC")  # TOPIC, MASTER_UNIT
    passing_percentage = Column(Float, nullable=False, default=75.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    topic = relationship("Topic", back_populates="quizzes")
    unit = relationship("Unit", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizAttempt.created_at.desc()")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_area = Column(String(100), nullable=True, default="Core Concepts")
    question_type = Column(String(50), nullable=True, default="concept_understanding")
    difficulty = Column(String(20), nullable=True, default="medium")
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # List of strings [A, B, C, D]
    correct_answer = Column(Text, nullable=False)
    source_reference = Column(Text, nullable=False)  # Verifiable source text citation
    explanation = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    passed = Column(Boolean, nullable=False)
    answers = Column(JSON, nullable=True)  # {question_id: selected_answer}
    concept_breakdown = Column(JSON, nullable=True)  # {concept_area: {total, correct, percentage}}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")



class TopicProgress(Base):
    __tablename__ = "topic_progress"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(String(36), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="UNLOCKED")  # UNLOCKED, IN_PROGRESS, PASSED, COMPLETED
    best_score = Column(Integer, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="topic_progress")
    topic = relationship("Topic", back_populates="progress")

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),
    )


class UnitProgress(Base):
    __tablename__ = "unit_progress"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_id = Column(String(36), ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    topics_completed = Column(Integer, nullable=False, default=0)
    total_topics = Column(Integer, nullable=False, default=0)
    master_quiz_unlocked = Column(Boolean, nullable=False, default=False)
    master_quiz_score = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="NOT_STARTED")  # NOT_STARTED, IN_PROGRESS, COMPLETED
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="unit_progress")
    unit = relationship("Unit", back_populates="progress")

    __table_args__ = (
        UniqueConstraint("user_id", "unit_id", name="uq_user_unit"),
    )


class SubjectProgress(Base):
    __tablename__ = "subject_progress"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    units_completed = Column(Integer, nullable=False, default=0)
    total_units = Column(Integer, nullable=False, default=0)
    completion_percentage = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="NOT_STARTED")  # NOT_STARTED, IN_PROGRESS, COMPLETED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="subject_progress")
    subject = relationship("Subject", back_populates="progress")

    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_user_subject"),
    )


class StudyRoadmap(Base):
    __tablename__ = "study_roadmaps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Integer, nullable=False)
    daily_hours = Column(Float, nullable=False)
    total_available_hours = Column(Float, nullable=False)
    total_scheduled_hours = Column(Float, nullable=False)
    buffer_hours = Column(Float, nullable=False, default=0.0)
    shortfall_hours = Column(Float, nullable=False, default=0.0)
    has_shortfall = Column(Boolean, nullable=False, default=False)
    shortfall_message = Column(Text, nullable=True)
    topics_count = Column(Integer, nullable=False, default=0)
    revision_hours = Column(Float, nullable=False, default=0.0)
    assessment_hours = Column(Float, nullable=False, default=0.0)
    plan_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User")
    subject = relationship("Subject")

    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_user_subject_roadmap"),
    )
