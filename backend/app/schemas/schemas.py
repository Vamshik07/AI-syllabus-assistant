from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    pass

class UserRegister(BaseModel):
    email: str
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Subject Schemas
class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    syllabus_text: Optional[str] = None
    pyq_data: Optional[Dict[str, Any]] = None

class SubjectCreate(SubjectBase):
    user_id: Optional[str] = None

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    syllabus_text: Optional[str] = None

class SubjectResponse(SubjectBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Unit Schemas
class UnitBase(BaseModel):
    title: str
    order_index: int = 1
    description: Optional[str] = None
    syllabus_text: Optional[str] = None

class UnitCreate(UnitBase):
    pass

class UnitUpdate(BaseModel):
    title: Optional[str] = None
    order_index: Optional[int] = None
    description: Optional[str] = None
    syllabus_text: Optional[str] = None

class UnitResponse(UnitBase):
    id: str
    subject_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    unit_id: str
    file_name: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    slide_count: Optional[int] = None
    processing_status: str
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentStatusResponse(BaseModel):
    id: str
    processing_status: str
    processing_error: Optional[str] = None
    page_count: Optional[int] = None
    slide_count: Optional[int] = None
    topics_count: int = 0


# Source Region Schemas
class SourceRegionResponse(BaseModel):
    id: str
    document_id: str
    topic_id: str
    subtopic_id: Optional[str] = None
    page_number: Optional[int] = None
    slide_number: Optional[int] = None
    region_type: str
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    element_order: int
    source_reference: Optional[str] = None
    content_text: Optional[str] = None
    content_html: Optional[str] = None
    media_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Subtopic Schemas
class SubtopicResponse(BaseModel):
    id: str
    topic_id: str
    name: str
    order_index: int
    source_start: Optional[str] = None
    source_end: Optional[str] = None
    confidence: float
    status: str

    model_config = ConfigDict(from_attributes=True)


# Topic Schemas
class TopicResponse(BaseModel):
    id: str
    document_id: str
    name: str
    order_index: int
    source_start: Optional[str] = None
    source_end: Optional[str] = None
    confidence: float
    status: str
    subtopics: List[SubtopicResponse] = []
    is_unlocked: bool = True
    progress_status: Optional[str] = "UNLOCKED"
    learning_data: Optional[Dict[str, Any]] = None
    pyq_frequency: int = 0
    pyq_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TopicContentView(BaseModel):
    topic_id: str
    topic_name: str
    order_index: int
    document_id: str
    file_type: str
    file_name: str
    source_start: Optional[str] = None
    source_end: Optional[str] = None
    subtopics: List[SubtopicResponse] = []
    regions: List[SourceRegionResponse] = []
    unit_id: Optional[str] = None
    unit_title: Optional[str] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    learning_data: Optional[Dict[str, Any]] = None
    pyq_frequency: int = 0
    pyq_notes: Optional[str] = None

class TopicLearningView(BaseModel):
    topic_id: str
    topic_name: str
    order_index: int
    learning_data: Dict[str, Any]
    source_reference: Optional[str] = None


# Quiz Schemas
class QuizQuestionBase(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    source_reference: str
    explanation: Optional[str] = None
    concept_area: Optional[str] = "Core Concepts"
    question_type: Optional[str] = "concept_understanding"
    difficulty: Optional[str] = "medium"
    order_index: int = 0

class QuizQuestionResponse(BaseModel):
    id: str
    question: str
    options: List[str]
    # In student-facing quiz taking, correct_answer is hidden until submitted
    order_index: int
    source_reference: Optional[str] = None
    explanation: Optional[str] = None
    concept_area: Optional[str] = "Core Concepts"
    question_type: Optional[str] = "concept_understanding"
    difficulty: Optional[str] = "medium"

    model_config = ConfigDict(from_attributes=True)

class QuizResponse(BaseModel):
    id: str
    topic_id: Optional[str] = None
    unit_id: str
    quiz_type: str
    passing_percentage: float = 75.0
    questions: List[QuizQuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class QuizAttemptRequest(BaseModel):
    answers: Dict[str, str]  # {question_id: selected_option}
    user_id: Optional[str] = None

class QuestionResult(BaseModel):
    question_id: str
    question: str
    options: List[str]
    selected_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    source_reference: str
    explanation: Optional[str] = None
    concept_area: Optional[str] = "Core Concepts"
    question_type: Optional[str] = "concept_understanding"
    difficulty: Optional[str] = "medium"

class QuizAttemptResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: int
    total_questions: int
    percentage: float
    passed: bool
    passing_percentage: float = 75.0
    results: List[QuestionResult]
    concept_breakdown: Optional[Dict[str, Any]] = None
    weak_concepts: Optional[List[str]] = None
    recommended_revision: Optional[List[str]] = None
    unlocked_next_topic_id: Optional[str] = None
    master_quiz_unlocked: Optional[bool] = False
    unit_completed: Optional[bool] = False



# Progress Schemas
class TopicProgressResponse(BaseModel):
    topic_id: str
    topic_name: str
    order_index: int
    status: str  # LOCKED, UNLOCKED, IN_PROGRESS, PASSED, COMPLETED
    best_score: Optional[int] = None
    attempt_count: int = 0
    completed_at: Optional[datetime] = None

class UnitProgressResponse(BaseModel):
    unit_id: str
    unit_title: str
    topics_completed: int
    total_topics: int
    completion_percentage: float
    master_quiz_unlocked: bool
    master_quiz_score: Optional[int] = None
    status: str  # NOT_STARTED, IN_PROGRESS, COMPLETED
    completed_at: Optional[datetime] = None
    topic_progress: List[TopicProgressResponse] = []

class SubjectProgressResponse(BaseModel):
    subject_id: str
    subject_name: str
    units_completed: int
    total_units: int
    completion_percentage: float
    status: str
    unit_progress: List[UnitProgressResponse] = []


# Detail Responses
class UnitDetailResponse(UnitResponse):
    subject_name: Optional[str] = None
    document: Optional[DocumentResponse] = None
    topics: List[TopicResponse] = []
    progress: Optional[UnitProgressResponse] = None

class SubjectDetailResponse(SubjectResponse):
    units: List[UnitDetailResponse] = []
    progress: Optional[SubjectProgressResponse] = None


# Companion Schemas
class CompanionChatRequest(BaseModel):
    message: str
    mode: str = "study"  # "study" or "general"
    topic_id: Optional[str] = None
    topic_name: Optional[str] = None
    unit_id: Optional[str] = None
    unit_name: Optional[str] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    current_page: Optional[str] = None
    current_slide: Optional[int] = None
    current_resource_id: Optional[str] = None
    current_question: Optional[str] = None
    history: List[Dict[str, str]] = []

class CompanionChatResponse(BaseModel):
    response: str
    mode: str
    cat_state: str = "EXPLAINING"
    speech_bubble: Optional[str] = None
    requires_general_prompt: bool = False
    outside_concept: Optional[str] = None
    source_reference: Optional[str] = None
    quick_actions: List[str] = []
