import {
  User,
  Subject,
  SubjectDetail,
  Unit,
  UnitDetail,
  DocumentInfo,
  DocumentStatus,
  Topic,
  TopicContentView,
  Quiz,
  QuizAttemptResponse,
  UnitProgress,
  SubjectProgress,
  TopicProgress,
  StudyPlan,
} from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as any),
    };

    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('sourcelearn_token');
      if (token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    const res = await fetch(url, {
      ...options,
      headers: options.body instanceof FormData ? { ...options.headers, ...(headers['Authorization'] ? { Authorization: headers['Authorization'] } : {}) } : headers,
    });

    if (!res.ok) {
      let errorMsg = `Error ${res.status}: ${res.statusText}`;
      try {
        const errData = await res.json();
        if (errData && errData.detail) {
          errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
        }
      } catch {
        // use default error message
      }
      throw new Error(errorMsg);
    }

    return res.json();
  }

  // Auth
  async register(data: { email: string; name: string; password: string }): Promise<{ access_token: string; token_type: string; user: User }> {
    const res = await this.request<{ access_token: string; token_type: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (typeof window !== 'undefined' && res.access_token) {
      localStorage.setItem('sourcelearn_token', res.access_token);
      localStorage.setItem('sourcelearn_user', JSON.stringify(res.user));
    }
    return res;
  }

  async login(data: { email: string; password: string }): Promise<{ access_token: string; token_type: string; user: User }> {
    const res = await this.request<{ access_token: string; token_type: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (typeof window !== 'undefined' && res.access_token) {
      localStorage.setItem('sourcelearn_token', res.access_token);
      localStorage.setItem('sourcelearn_user', JSON.stringify(res.user));
    }
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('sourcelearn_token');
      localStorage.removeItem('sourcelearn_user');
    }
  }

  getCurrentUser(): User | null {
    if (typeof window !== 'undefined') {
      const raw = localStorage.getItem('sourcelearn_user');
      if (raw) {
        try {
          return JSON.parse(raw);
        } catch {
          return null;
        }
      }
    }
    return null;
  }

  // Subjects
  async getSubjects(): Promise<Subject[]> {
    return this.request<Subject[]>('/subjects');
  }

  async getSubject(id: string): Promise<SubjectDetail> {
    return this.request<SubjectDetail>(`/subjects/${id}`);
  }

  async createSubject(data: { name: string; description?: string }): Promise<Subject> {
    return this.request<Subject>('/subjects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateSubject(id: string, data: { name?: string; description?: string }): Promise<Subject> {
    return this.request<Subject>(`/subjects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteSubject(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/subjects/${id}`, {
      method: 'DELETE',
    });
  }

  // Units
  async createUnit(subjectId: string, data: { title: string; order_index?: number; description?: string }): Promise<Unit> {
    return this.request<Unit>(`/subjects/${subjectId}/units`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getUnit(unitId: string): Promise<UnitDetail> {
    return this.request<UnitDetail>(`/units/${unitId}`);
  }

  async updateUnit(unitId: string, data: { title?: string; order_index?: number; description?: string }): Promise<Unit> {
    return this.request<Unit>(`/units/${unitId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteUnit(unitId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/units/${unitId}`, {
      method: 'DELETE',
    });
  }

  async getUnitTopics(unitId: string): Promise<Topic[]> {
    return this.request<Topic[]>(`/units/${unitId}/topics`);
  }

  // Documents
  async uploadDocument(unitId: string, file: File): Promise<DocumentInfo> {
    const formData = new FormData();
    formData.append('file', file);
    return this.request<DocumentInfo>(`/units/${unitId}/document`, {
      method: 'POST',
      body: formData,
    });
  }

  async getDocumentStatus(docId: string): Promise<DocumentStatus> {
    return this.request<DocumentStatus>(`/documents/${docId}/status`);
  }

  // Topics
  async getTopic(topicId: string): Promise<Topic> {
    return this.request<Topic>(`/topics/${topicId}`);
  }

  async getTopicContent(topicId: string): Promise<TopicContentView> {
    return this.request<TopicContentView>(`/topics/${topicId}/content`);
  }

  async getTopicProgress(topicId: string): Promise<TopicProgress> {
    return this.request<TopicProgress>(`/topics/${topicId}/progress`);
  }

  // Quizzes
  async generateTopicQuiz(topicId: string): Promise<Quiz> {
    return this.request<Quiz>(`/topics/${topicId}/quiz/generate`, {
      method: 'POST',
    });
  }

  async getTopicQuiz(topicId: string): Promise<Quiz> {
    return this.request<Quiz>(`/topics/${topicId}/quiz`);
  }

  async submitQuizAttempt(quizId: string, answers: Record<string, string>): Promise<QuizAttemptResponse> {
    return this.request<QuizAttemptResponse>(`/quizzes/${quizId}/attempt`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
  }

  async getLatestQuizAttempt(quizId: string): Promise<QuizAttemptResponse | null> {
    return this.request<QuizAttemptResponse | null>(`/quizzes/${quizId}/latest-attempt`);
  }

  // Master Quiz
  async generateMasterQuiz(unitId: string): Promise<Quiz> {
    return this.request<Quiz>(`/units/${unitId}/master-quiz/generate`, {
      method: 'POST',
    });
  }

  async submitMasterQuizAttempt(unitId: string, answers: Record<string, string>): Promise<QuizAttemptResponse> {
    return this.request<QuizAttemptResponse>(`/units/${unitId}/master-quiz/attempt`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
  }

  // Progress
  async getUnitProgress(unitId: string): Promise<UnitProgress> {
    return this.request<UnitProgress>(`/units/${unitId}/progress`);
  }

  async getSubjectProgress(subjectId: string): Promise<SubjectProgress> {
    return this.request<SubjectProgress>(`/subjects/${subjectId}/progress`);
  }

  async createStudyPlan(subjectId: string, data: {
    start_date: string;
    end_date: string;
    daily_hours: number;
  }): Promise<StudyPlan> {
    return this.request<StudyPlan>(`/subjects/${subjectId}/study-plan`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient();
