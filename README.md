# 🎓 SourceLearn — Source-Grounded AI Learning Platform

> **Learn from authentic course sources, never rewritten by AI.**  
> SourceLearn is an educational learning platform built on **strict source fidelity**. It ingests authentic curriculum documents (PDF, PPTX, DOCX) and structures them into sequential topic pathways while ensuring that all educational content displayed to students comes **directly and un-paraphrased from the original source material**.

---

## 📑 Table of Contents

- [🌟 Core Philosophy: Absolute Source Fidelity](#-core-philosophy-absolute-source-fidelity)
- [✨ Key Features](#-key-features)
- [🏛️ System Architecture](#️-system-architecture)
- [📂 Project Structure](#-project-structure)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Quickstart & How to Run the Project](#-quickstart--how-to-run-the-project)
  - [Prerequisites](#prerequisites)
  - [1. Backend Setup (FastAPI & PostgreSQL)](#1-backend-setup-fastapi--postgresql)
  - [2. Frontend Setup (Next.js & Tailwind CSS)](#2-frontend-setup-nextjs--tailwind-css)
- [📖 User Guide (How to Use SourceLearn)](#-user-guide-how-to-use-sourcelearn)
- [🧪 Running Automated Tests](#-running-automated-tests)
- [🔒 Security & Multi-User Isolation](#-security--multi-user-isolation)
- [📄 License](#-license)

---

## 🌟 Core Philosophy: Absolute Source Fidelity

Traditional AI study tools summarize, rewrite, or hallucinate content. When preparing for university examinations or professional certifications, subtle details, exact formulas, and instructor-drawn diagrams are critical.

SourceLearn enforces a strict architectural boundary:
1. **Original Source is Authoritative**: When a student opens a topic, the platform displays the **original slide graphics, page layouts, tables, flowcharts, and text** extracted directly from the uploaded file.
2. **No LLM Paraphrasing**: The AI is **never** permitted to rewrite paragraphs, invent examples, summarize text, or alter instructor terminology.
3. **Targeted AI Responsibilities**: AI is used solely for:
   - Structural classification assistance (mapping document sections to topics).
   - Teacher-grade quiz generation (framing multiple-choice questions grounded in specific pages/slides with verbatim citations).

---

## ✨ Key Features

- **Multi-Format Ingestion**:
  - **PDF**: Preserves pages, text, embedded figures, and formatting via PyMuPDF (`fitz`). Automatic OCR fallback for scanned materials.
  - **PowerPoint (PPTX)**: Preserves slide order, slide titles, shapes, and bullet points via `python-pptx`.
  - **Word (DOCX)**: Preserves document structure, headings, tables, and images via `python-docx`.

- **Deterministic Topic Hierarchy**:
  - Analyzes the resource to form a clean pedagogical tree:
    $$\text{Subject} \longrightarrow \text{Unit} \longrightarrow \text{Ordered Topics} \longrightarrow \text{Subtopics}$$
  - Topics strictly maintain the sequence of the original document.

- **Teacher-Grade Assessments**:
  - Automatically synthesizes rigorous 5-question multiple-choice quizzes per topic.
  - Questions test real conceptual comprehension, diagram interpretation, and terminology rather than naive fill-in-the-blank text.
  - Every single question includes an **authentic source reference citation** indicating the exact page or slide.

- **Sequential Mastery Gating (75% Gate)**:
  - Passing score: **$\ge 75\%$** (4 out of 5 correct = 80% PASS; 3 out of 5 = 60% FAIL).
  - Passing a topic quiz unlocks the subsequent topic in the unit.
  - Passing all topics unlocks the comprehensive **Master Unit Quiz**.

- **Comprehensive Results Dashboard**:
  - After submitting an assessment, students receive an immediate audit:
    - Overall grade and passing status pill.
    - 4 metric cards: **Attempted**, **Correct**, **Incorrect**, and **Grade %**.
    - Detailed question review comparing the student's checked answer against the correct answer, complete with pedagogical explanations and source citations.
    - **Conditional Progression**: "Next Topic Unlocked →" button is only displayed upon passing; failed attempts present a "Retry Quiz" option to review and re-attempt.

- **Multi-User Authentication & Data Isolation**:
  - User registration and login powered by bcrypt password hashing and HS256 JWT tokens.
  - Complete data isolation: subjects, units, quiz attempts, and learning analytics are strictly scoped to the authenticated student account.

- **Real-Time Progress Tracking**:
  - Visual progress bars at Subject, Unit, and Topic levels reflecting completed topics, quiz scores, and mastery percentages.

- **Time-Aware Study Timetable**:
  - Choose a subject, preparation date range, and daily study hours from the Timetable page.
  - The planner distributes the subject's ordered topics across the available days.
  - Each topic includes source-grounded study material: concise main points when time is limited and more detailed material when more time is available.
  - The generated plan also includes study tasks and topic source ranges without paraphrasing the uploaded material.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User["Student Browser (Next.js 14)"]
    API["FastAPI Backend (Port 8000)"]
    DB[("PostgreSQL Database")]
    AI["Google Gemini Service (LLM)"]
    DocEng["Document Extraction Engine (PyMuPDF / python-pptx / python-docx)"]

    User -- "REST / JWT Bearer" --> API
    API -- "ORM Queries" --> DB
    API -- "Upload PDF/PPTX/DOCX" --> DocEng
    DocEng -- "Extracted Pages & Slides" --> API
    API -- "Topic Structure / Quiz Gen" --> AI
    AI -- "Validated Structured JSON" --> API
```

---

## 📂 Project Structure

```text
source-learn/
├── .gitignore                   # Git ignore for Python, Node, DBs, and secrets
├── README.md                    # Project documentation
│
├── frontend/                    # Next.js 14 Application
│   ├── app/
│   │   ├── page.tsx             # Public Product Landing Page
│   │   ├── layout.tsx           # Root layout & AuthProvider wrapper
│   │   ├── login/page.tsx       # User sign-in page
│   │   ├── register/page.tsx    # User registration page
│   │   ├── subjects/
│   │   │   ├── page.tsx         # User's enrolled subjects & subject creation
│   │   │   └── [id]/page.tsx    # Subject view & unit management
│   │   ├── units/
│   │   │   └── [unitId]/
│   │   │       ├── page.tsx     # Unit topic pathway & document upload
│   │   │       └── master-quiz/ # Master unit capstone quiz
│   │   ├── topics/
│   │   │   └── [topicId]/page.tsx # Authentic source viewer & topic quiz
│   │   └── progress/page.tsx    # Personal progress analytics
│   ├── components/
│   │   ├── Navbar.tsx           # Global navigation with auth state
│   │   ├── QuizCard.tsx         # Quiz player & detailed results dashboard
│   │   ├── SourceContentViewer.tsx # Authentic slide/page content renderer
│   │   ├── DocumentUploader.tsx # File drag-and-drop ingestion component
│   │   └── ProgressBar.tsx      # Animated progress bar
│   ├── context/
│   │   └── AuthContext.tsx      # React authentication state & token hydration
│   ├── lib/
│   │   └── api.ts               # Typed API client with Bearer auth injection
│   └── types/
│       └── index.ts             # TypeScript domain definitions
│
└── backend/                     # FastAPI Application
    ├── app/
    │   ├── main.py              # Application entrypoint & CORS
    │   ├── config.py            # Environment configuration settings
    │   ├── api/
    │   │   ├── auth.py          # User register, login, and profile endpoints
    │   │   ├── subjects.py      # Subject CRUD & isolation
    │   │   ├── units.py         # Unit management & document upload
    │   │   ├── topics.py        # Topic details, content view, and progress
    │   │   ├── quizzes.py       # Quiz generation, submissions & attempts
    │   │   ├── progress.py      # Analytics & mastery metrics
    │   │   ├── documents.py     # Document status & retrieval
    │   │   └── deps.py          # JWT authentication dependency
    │   ├── models/
    │   │   └── models.py        # SQLAlchemy models (User, Subject, Unit, Document, Topic, Quiz...)
    │   ├── schemas/
    │   │   └── schemas.py       # Pydantic request/response schemas
    │   ├── database/
    │   │   └── database.py      # Database engine & session management
    │   └── services/
    │       ├── auth_service.py  # Password hashing & JWT generation/verification
    │       ├── ai_service.py    # Gemini API client & prompt execution
    │       ├── pdf_service.py   # PyMuPDF parser & image extractor
    │       ├── pptx_service.py  # python-pptx slide parser
    │       ├── docx_service.py  # python-docx parser
    │       ├── ocr_service.py   # Tesseract OCR fallback
    │       ├── structure_service.py # Deterministic topic segmentation
    │       ├── quiz_service.py  # 5-question teacher-grade quiz generation
    │       ├── progress_service.py # 75% gate, sequential unlocks & analytics
    │       └── validation_service.py # Programmatic source grounding validation
    └── tests/                   # 15 automated integration tests
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic V2, Uvicorn |
| **Authentication** | Bcrypt password hashing (12 salt rounds), PyJWT (HS256) |
| **Database** | PostgreSQL (with automated SQLite fallback for local testing) |
| **Doc Processing** | PyMuPDF (`fitz`), `python-pptx`, `python-docx`, Tesseract OCR |
| **AI Integration** | Google Gemini API (`gemini-2.5-flash` / configurable via `.env`) |

---

## 🚀 Quickstart & How to Run the Project

### Prerequisites

Ensure you have the following installed on your machine:
- **Python**: Version 3.10+ (Python 3.12 recommended)
- **Node.js**: Version 18+ (Node 20+ recommended)
- **PostgreSQL**: Running on port `5432` or `5433` (or SQLite fallback)
- **Gemini API Key**: A valid Google AI Gemini API Key ([Get one free on Google AI Studio](https://aistudio.google.com/))

---

### 1. Backend Setup (FastAPI & PostgreSQL)

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create an environment configuration file:
   Create a file named `.env` in the `backend/` directory:
   ```env
   # PostgreSQL Connection URI (Adjust port/credentials as needed)
   DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/sourcelearn

   # Google Gemini API Key
   LLM_API_KEY=your_google_gemini_api_key_here

   # LLM Model Name (Default: gemini-2.5-flash)
   LLM_MODEL=gemini-2.5-flash

   # Secret Key for JWT Authentication
   SECRET_KEY=sourcelearn-super-secret-key-change-in-production

   # Local folder for document uploads
   UPLOAD_DIR=uploads
   ```

5. Run the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. Verify the Backend:
   - API Docs (Swagger UI): **`http://localhost:8000/docs`**
   - API Health: **`http://localhost:8000/api/health`**

---

### 2. Frontend Setup (Next.js & Tailwind CSS)

1. Open a second terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Configure Environment Variables:
   Create a `.env.local` file in the `frontend/` directory (or verify it exists):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

4. Start the Development Server:
   ```bash
   npm run dev
   ```

5. Access the Frontend Application:
   Open your browser to:
   👉 **`http://localhost:3001`** (or `http://localhost:3000`)

---

## 📖 User Guide (How to Use SourceLearn)

```mermaid
flowchart LR
    A["1. Register Account"] --> B["2. Create Subject"]
    B --> C["3. Add Unit & Upload File"]
    C --> D["4. Study Authentic Content"]
    D --> E["5. Pass Topic Quiz (≥75%)"]
    E --> F["6. Unlock Next Topic"]
    F --> G["7. Pass Master Unit Quiz"]
```

### Step 1: Create an Account & Sign In
- Navigate to **`http://localhost:3001/register`**.
- Enter your Full Name, Email, and Password (minimum 6 characters) and click **Create Free Account**.
- Your account session is automatically initialized.

### Step 2: Create a Subject
- Go to the **Subjects** tab or click **"Open My Subjects"**.
- Click **"+ New Subject"**.
- Enter a name (e.g. `Principles of Management` or `Operating Systems`) and an optional description, then click **Save Subject**.

### Step 3: Add Units & Upload Authentic Resources
- Click on your newly created subject to open its syllabus view.
- Click **"+ Add Unit"** to create a unit (e.g. `Unit 2: Planning and Decision Making`).
- Click into the unit, and use the **Upload Learning Resource** area to drop in your official course file:
  - Supports **PDF** (textbooks, lecture notes), **PPTX** (presentation slide decks), or **DOCX** (study guides).
- The system automatically extracts the document structure, generates topics in order, and extracts original diagrams and slide snapshots.

### Step 4: Study the Authentic Material
- Click on **Topic 1** in the pathway.
- In the **Source Learning Material** tab, review the authentic pages/slides exactly as authored by your instructor, including charts, formulas, and bullet points.

### Step 5: Take the Topic Assessment
- Click **"Take Topic Quiz"**.
- Answer the 5 multiple-choice questions synthesized from the source.
- Click **"Submit Quiz"**.

### Step 6: Review Results & Unlock Progress
- If you score **$\ge 75\%$** (4/5 or 5/5):
  - The assessment status turns green (**Passed**).
  - You see your checked answers vs. correct answers with source citations.
  - The **"Next Topic Unlocked →"** button appears, allowing you to proceed to Topic 2.
- If you score **$< 75\%$**:
  - The "Next Topic" button remains locked.
  - Review the source citations and explanations for the questions you missed.
  - Click **"Retry Quiz"** to attempt the assessment again.

### Step 7: Master the Unit
- Once all individual topics in the unit are passed, the **Master Unit Quiz** unlocks.
- Complete the capstone assessment to earn 100% unit completion.

---

## 🧪 Running Automated Tests

SourceLearn includes a suite of automated unit and end-to-end integration tests.

### Running Backend Tests
From the `backend/` directory with your virtual environment active:
```bash
pytest -v
```

**Test Coverage Summary (15/15 Passed)**:
- `test_auth_and_isolation.py`: Verifies user registration, bcrypt password hashing, JWT authentication, and ensures User A cannot access User B's subjects.
- `test_api_subjects_units.py`: Verifies Subject and Unit CRUD operations, cascade deletions, and error boundaries.
- `test_document_processing.py`: Tests PyMuPDF, python-pptx, and python-docx parsing, slide extraction, and invalid file rejection.
- `test_source_fidelity.py`: Validates exact heading fidelity, order preservation, and citation integrity.
- `test_quiz_and_progress.py`: Validates the 75% passing threshold, topic sequential unlocking, and progress calculations.
- `test_live_e2e_integration.py`: End-to-end HTTP pipeline test.

### Running Frontend Typechecks & Tests
From the `frontend/` directory:
```bash
# Typecheck validation
npx tsc --noEmit

# Build verification
npm run build
```

---

## 🔒 Security & Multi-User Isolation

- **Bcrypt Password Security**: Passwords are never stored in plaintext; salted hashes are generated using 12 rounds of bcrypt.
- **Stateless JWT Sessions**: Authenticated requests carry `Authorization: Bearer <token>` in the HTTP headers.
- **Row-Level User Scoping**: All database queries for subjects, units, quiz attempts, and learning progress explicitly filter on `user_id = current_user.id`.
- **Source Protection**: Uploaded files and media regions are served through verified path abstractions preventing unauthorized directory traversal.

---

## 📄 License

This project is built and distributed under the **MIT License**.

---

## ▶️ Run the Project on Windows

Open two PowerShell terminals.

### Terminal 1: Backend

```powershell
cd "C:\Users\VAMSHI\OneDrive\Desktop\AI syllabus assistant\backend"

.\venv\Scripts\Activate.ps1

$env:DATABASE_URL = "sqlite:///C:/Users/VAMSHI/OneDrive/Desktop/AI%20syllabus%20assistant/backend/sourcelearn.db"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend URLs:

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Swagger documentation: http://localhost:8000/docs

If PowerShell activation is unavailable, run the backend directly:

```powershell
cd "C:\Users\VAMSHI\OneDrive\Desktop\AI syllabus assistant\backend"

$env:DATABASE_URL = "sqlite:///C:/Users/VAMSHI/OneDrive/Desktop/AI%20syllabus%20assistant/backend/sourcelearn.db"

.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Frontend

```powershell
cd "C:\Users\VAMSHI\OneDrive\Desktop\AI syllabus assistant\frontend"

npm install
npm run dev
```

Frontend URL: http://localhost:3001

### Run backend tests

```powershell
cd "C:\Users\VAMSHI\OneDrive\Desktop\AI syllabus assistant\backend"

.\venv\Scripts\Activate.ps1
pytest -q
```
