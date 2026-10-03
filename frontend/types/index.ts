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
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  order_index: number;
  source_reference?: string;
  explanation?: string;
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
  document?: DocumentInfo;
  topics: Topic[];
  progress?: UnitProgress;
}

export interface SubjectDetail extends Subject {
  units: UnitDetail[];
  progress?: SubjectProgress;
}

export interface StudyPlanItem {
  date: string;
  unit_id: string;
  unit_title: string;
  topic_id: string;
  topic_name: string;
  study_minutes: number;
  material_mode: 'concise' | 'detailed';
  material: string;
  source_start?: string;
  source_end?: string;
  tasks: string[];
}

export interface StudyPlan {
  subject_id: string;
  subject_name: string;
  start_date: string;
  end_date: string;
  days: number;
  daily_hours: number;
  total_hours: number;
  material_mode: 'concise' | 'detailed';
  schedule: StudyPlanItem[];
}
