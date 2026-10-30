export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Subject {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  syllabus_text?: string;
  pyq_data?: any;
  created_at: string;
  updated_at: string;
  units?: UnitDetail[];
  progress?: SubjectProgress;
}

export interface Unit {
  id: string;
  subject_id: string;
  title: string;
  order_index: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentInfo {
  id: string;
  unit_id: string;
  file_name: string;
  file_type: 'PDF' | 'PPTX' | 'DOCX';
  file_size: number;
  page_count?: number;
  slide_count?: number;
  processing_status: 'UPLOADED' | 'PROCESSING' | 'PROCESSED' | 'FAILED' | 'REVIEW_REQUIRED';
  processing_error?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentStatus {
  id: string;
  processing_status: 'UPLOADED' | 'PROCESSING' | 'PROCESSED' | 'FAILED' | 'REVIEW_REQUIRED';
  processing_error?: string;
  page_count?: number;
  slide_count?: number;
  topics_count: number;
}

export interface Subtopic {
  id: string;
  topic_id: string;
  name: string;
  order_index: number;
  source_start?: string;
  source_end?: string;
  confidence: number;
  status: string;
}

export interface TopicLearningData {
  summary?: string;
  source_sections?: Array<{
    source_reference: string;
    page_number?: number;
    slide_number?: number;
    region_type?: string;
    text: string;
  }>;
  definitions?: Array<{ term: string; definition: string; source_reference?: string; source_ref?: string }>;
  core_concepts?: Array<{ concept?: string; title?: string; explanation?: string; description?: string; source_reference?: string; source_ref?: string }>;
  characteristics?: Array<string | { name: string; description?: string; source_reference?: string }>;
  types_and_classifications?: Array<{ category: string; items?: string[]; description?: string; source_reference?: string }>;
  classifications?: Array<{ category: string; items?: string[]; description?: string; source_reference?: string }>;
  processes?: Array<{
    process_name?: string;
    name?: string;
    source_reference?: string;
    steps: Array<string | { step_number?: number; title?: string; description?: string; source_reference?: string }>;
  }>;
  comparisons?: Array<{ aspect: string; item_a: string; item_b: string; source_reference?: string }>;
  advantages?: Array<string | { point: string; source_reference?: string }>;
  disadvantages?: Array<string | { point: string; source_reference?: string }>;
  examples?: Array<string | { example: string; source_reference?: string }>;
  important_points?: Array<string | { point: string; source_reference?: string }>;
  keywords?: Array<{ keyword?: string; term?: string; explanation?: string; definition?: string; context?: string; source_reference?: string }>;
  visuals?: Array<{
    id?: string;
    region_id?: string;
    type: string;
    caption: string;
    page_number?: number;
    slide_number?: number;
    media_path?: string;
    content_html?: string;
    source_reference?: string;
    ocr_text?: string;
  }>;
  practice_cards?: Array<{
    front: string;
    back: string;
    concept?: string;
    concept_area?: string;
    source_reference?: string;
  }>;
}

export interface Topic {
  id: string;
  document_id: string;
  name: string;
  order_index: number;
  source_start?: string;
  source_end?: string;
  confidence: number;
  status: string;
  subtopics: Subtopic[];
  is_unlocked: boolean;
  progress_status?: 'LOCKED' | 'UNLOCKED' | 'IN_PROGRESS' | 'PASSED' | 'COMPLETED';
  learning_data?: TopicLearningData;
  pyq_frequency?: number;
  pyq_notes?: string;
}

export interface SourceRegion {
  id: string;
  document_id: string;
  topic_id: string;
  subtopic_id?: string;
  page_number?: number;
  slide_number?: number;
  region_type: 'TEXT' | 'IMAGE' | 'TABLE' | 'DIAGRAM' | 'EQUATION' | 'FLOWCHART' | 'FULL_PAGE' | 'SLIDE';
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
  element_order: number;
  source_reference?: string;
  content_text?: string;
  content_html?: string;
  media_path?: string;
}

export interface TopicContentView {
  topic_id: string;
  topic_name: string;
  order_index: number;
  document_id: string;
  file_type: string;
  file_name: string;
  source_start?: string;
  source_end?: string;
  subtopics: Subtopic[];
  regions: SourceRegion[];
  unit_id?: string;
  unit_title?: string;
  subject_id?: string;
  subject_name?: string;
  learning_data?: TopicLearningData;
  pyq_frequency?: number;
  pyq_notes?: string;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  order_index: number;
  source_reference?: string;
  explanation?: string;
  concept_area?: string;
  question_type?: string;
  difficulty?: string;
}

export interface Quiz {
  id: string;
  topic_id?: string;
  unit_id: string;
  quiz_type: 'TOPIC' | 'MASTER_UNIT';
  passing_percentage: number;
  questions: QuizQuestion[];
}

export interface QuestionResult {
  question_id: string;
  question: string;
  options: string[];
  selected_answer?: string;
  correct_answer: string;
  is_correct: boolean;
  source_reference: string;
  explanation?: string;
  concept_area?: string;
  question_type?: string;
  difficulty?: string;
}

export interface QuizAttemptResponse {
  attempt_id: string;
  quiz_id: string;
  score: number;
  total_questions: number;
  percentage: number;
  passed: boolean;
  passing_percentage: number;
  results: QuestionResult[];
  concept_breakdown?: Record<string, { total: number; correct: number; percentage: number }>;
  weak_concepts?: string[];
  recommended_revision?: string[];
  unlocked_next_topic_id?: string;
  master_quiz_unlocked?: boolean;
  unit_completed?: boolean;
}


export interface TopicProgress {
  topic_id: string;
  topic_name: string;
  order_index: number;
  status: 'LOCKED' | 'UNLOCKED' | 'IN_PROGRESS' | 'PASSED' | 'COMPLETED';
  best_score?: number;
  attempt_count: number;
  completed_at?: string;
}

export interface UnitProgress {
  unit_id: string;
  unit_title: string;
  topics_completed: number;
  total_topics: number;
  completion_percentage: number;
  master_quiz_unlocked: boolean;
  master_quiz_score?: number;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  completed_at?: string;
  topic_progress: TopicProgress[];
}

export interface SubjectProgress {
  subject_id: string;
  subject_name: string;
  units_completed: number;
  total_units: number;
  completion_percentage: number;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  unit_progress: UnitProgress[];
}

export interface UnitDetail extends Unit {
  subject_name?: string;
  document?: DocumentInfo;
  topics: Topic[];
  progress?: UnitProgress;
}

export interface SubjectDetail extends Subject {
  units: UnitDetail[];
  progress?: SubjectProgress;
}

export interface RoadmapDay {
  day_number: number;
  date: string;
  available_hours: number;
  allocated_hours: number;
  allocated_minutes: number;
  remaining_minutes: number;
  items: StudyPlanItem[];
}

export interface StudyPlanItem {
  date?: string;
  day_number?: number;
  item_type?: 'NEW_TOPIC' | 'REVISION' | 'PRACTICE' | 'ASSESSMENT';
  unit_id: string;
  unit_title: string;
  topic_id: string;
  topic_name: string;
  allocated_minutes?: number;
  study_minutes: number;
  material_mode?: 'concise' | 'detailed';
  material?: string;
  short_points?: string;
  detailed_content?: string;
  key_points?: string[];
  priority?: 'HIGH' | 'MEDIUM' | 'LOWER' | 'high_weightage' | 'quick_win' | 'foundation';
  priority_tier?: string;
  rank?: number;
  is_important?: boolean;
  priority_label?: string;
  importance_label?: string;
  priority_reasons?: string[];
  strategy_tip?: string;
  source_start?: string;
  source_end?: string;
  source_reference?: string;
  status?: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'NEEDS_REVISION';
  best_score?: number | null;
  tasks: string[];
}

export interface TopicForPlan {
  topic_id: string;
  topic_name: string;
  unit_id: string;
  unit_title: string;
  unit_order?: number;
  order_index: number;
  source_start?: string;
  source_end?: string;
  source_reference?: string;
  workload_minutes?: number;
  priority?: 'HIGH' | 'MEDIUM' | 'LOWER' | 'high_weightage' | 'quick_win' | 'foundation';
  priority_tier?: string;
  rank?: number;
  is_important: boolean;
  importance_score: number;
  priority_label?: string;
  importance_label: string;
  strategy_tip?: string;
  reasons?: string[];
  status?: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'NEEDS_REVISION';
  best_score?: number | null;
}

export interface StudyPlan {
  subject_id: string;
  subject_name: string;
  start_date: string;
  end_date: string;
  days: number;
  daily_hours: number;
  total_available_hours?: number;
  total_scheduled_hours?: number;
  total_hours: number;
  buffer_hours?: number;
  has_shortfall?: boolean;
  shortfall_hours?: number;
  shortfall_message?: string | null;
  topics_count?: number;
  revision_hours?: number;
  assessment_hours?: number;
  minutes_per_topic?: number;
  material_mode?: 'concise' | 'detailed';
  material_preference?: string;
  total_topics_in_syllabus?: number;
  topics_scheduled?: number;
  high_weightage_count?: number;
  quick_win_count?: number;
  only_important?: boolean;
  daily_schedule?: RoadmapDay[];
  schedule: StudyPlanItem[];
}

// AI Study Cat Companion Types
export type CatState =
  | 'IDLE'
  | 'HAPPY'
  | 'THINKING'
  | 'EXPLAINING'
  | 'CURIOUS'
  | 'STUDYING'
  | 'QUIZ'
  | 'HINT'
  | 'SUCCESS'
  | 'SUPPORTIVE'
  | 'SLEEPY'
  | 'CELEBRATION'
  | 'ROADMAP'
  | 'GENERAL_KNOWLEDGE'
  | 'STUDY_MODE';

export interface CompanionChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  mode: 'study' | 'general';
  catState?: CatState;
  sourceReference?: string | null;
  requiresGeneralPrompt?: boolean;
  outsideConcept?: string | null;
  timestamp: string;
  quickActions?: string[];
}

export interface CompanionChatRequest {
  message: string;
  mode: 'study' | 'general';
  topic_id?: string | null;
  topic_name?: string | null;
  unit_id?: string | null;
  unit_name?: string | null;
  subject_id?: string | null;
  subject_name?: string | null;
  current_page?: string | null;
  current_slide?: number | null;
  current_resource_id?: string | null;
  current_question?: string | null;
  history?: Array<{ role: string; content: string }>;
}

export interface CompanionChatResponse {
  response: string;
  mode: 'study' | 'general';
  cat_state: CatState;
  speech_bubble?: string | null;
  requires_general_prompt: boolean;
  outside_concept?: string | null;
  source_reference?: string | null;
  quick_actions?: string[];
}

export interface CompanionContextData {
  topicId?: string;
  topicName?: string;
  unitId?: string;
  unitTitle?: string;
  subjectId?: string;
  subjectName?: string;
  currentQuestion?: string;
  pageType?: 'dashboard' | 'subjects' | 'units' | 'topic' | 'quiz' | 'timetable' | 'progress';
}
