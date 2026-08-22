# LocalMind — Project Structure

**Tech Stack**: Django (Python) · SQLite · Ollama (LLM) · Docling (PDF/DOCX Parsing)

---

```
LocalMind/                                  ← Repository Root
│
├── backend/                                ← Django Backend (all server-side code lives here)
│   │
│   ├── manage.py                           ← Django CLI entrypoint (run server, migrate, test)
│   ├── requirements.txt                    ← Python dependencies (pip install -r requirements.txt)
│   ├── db.sqlite3                          ← Local SQLite database (auto-created on migrate)
│   │
│   ├── config/                             ← Django Project Configuration
│   │   ├── settings.py                     ← App settings (INSTALLED_APPS, DB, CORS, MEDIA_ROOT)
│   │   ├── urls.py                         ← Root URL router (wires all 4 apps)
│   │   ├── asgi.py                         ← ASGI entrypoint (for async deployments)
│   │   └── wsgi.py                         ← WSGI entrypoint (for production deployments)
│   │
│   ├── core/                               ← App: System health & shared utilities
│   │   ├── models.py                       ← (empty — no core models)
│   │   ├── views.py                        ← GET /api/health/ — health check endpoint
│   │   └── urls.py                         ← Routes: /api/health/
│   │
│   ├── documents/                          ← App: Document Upload & AI Parsing Engine
│   │   ├── models.py                       ← Document model (id, title, status, file_type, error_message)
│   │   ├── serializers.py                  ← DocumentSerializer (nested chapters + modules)
│   │   ├── views.py                        ← Upload, Process, Structure, Confirm outline views
│   │   ├── urls.py                         ← Routes: /api/documents/...
│   │   ├── tests.py                        ← Unit tests for parsing & structure APIs
│   │   ├── admin.py                        ← Django admin for Document management
│   │   └── services/
│   │       ├── parser.py                   ← ⭐ Core AI parser (Docling + Word XML hierarchy detection)
│   │       ├── outline.py                  ← Persists parsed Chapter/Module rows into SQLite
│   │       └── ollama.py                   ← Ollama HTTP client (shared by all AI features)
│   │
│   ├── learning/                           ← App: Chapters, Modules, Assessments & Remediation
│   │   ├── models.py                       ← Chapter, LearningModule, MicroModule,
│   │   │                                       Assessment, AssessmentAttempt models
│   │   ├── serializers.py                  ← Public + student-safe serializers
│   │   │                                       (AssessmentQuestionStudentSerializer redacts answers)
│   │   ├── views.py                        ← Chapter/Module detail, Assessment generate/submit,
│   │   │                                       Remediation generate views
│   │   ├── urls.py                         ← Routes: /api/learning/...
│   │   ├── tests.py                        ← Unit tests for assessment & remediation flows
│   │   ├── admin.py                        ← Django admin for all learning models
│   │   └── services/
│   │       ├── assessment_service.py       ← ⭐ Generates MCQ + Subjective questions via Ollama
│   │       ├── scoring_service.py          ← ⭐ Deterministic MCQ scoring + subjective AI grading
│   │       ├── subjective_evaluator.py     ← AI rubric evaluation for open-ended answers
│   │       └── remediation_service.py      ← ⭐ Builds targeted review lessons for missed concepts
│   │
│   └── tutor/                              ← App: AI Tutoring & Conversational Q&A
│       ├── models.py                       ← Conversation, Message models (multi-turn chat history)
│       ├── serializers.py                  ← ConversationSerializer, MessageSerializer
│       ├── views.py                        ← Teach, Ask (Q&A), Conversation detail views
│       ├── urls.py                         ← Routes: /api/tutor/...
│       ├── tests.py                        ← Unit tests for tutor sessions
│       ├── admin.py                        ← Django admin for conversations
│       └── services/
│           ├── tutor_service.py            ← ⭐ Lesson generation (structured explanation + takeaways)
│           └── question_answer_service.py  ← ⭐ Source-grounded Q&A (refuses to answer out-of-scope)
│
├── API_REFERENCE.md                        ← 📄 Complete API docs for Frontend team
├── POSTMAN_TESTING_CHAPTER_06.md           ← 📄 Step-by-step Postman guide for QA team
├── INTERN_TESTING_MANUAL.md               ← 📄 13-case generalized QA checklist for interns
├── README.md                               ← Project overview & setup instructions
├── .gitignore                              ← Ignores: venv/, db.sqlite3, media/, __pycache__
└── Chapter_06_Case_Studies.docx           ← 📄 Sample test file used in QA testing
```

---

## Django Apps at a Glance

| App | Prefix | Responsibility |
|-----|--------|---------------|
| `core` | `/api/` | System health check |
| `documents` | `/api/documents/` | File upload, AI parsing, outline management |
| `learning` | `/api/learning/` | Chapters, modules, assessments, remediation |
| `tutor` | `/api/tutor/` | AI teaching, conversational Q&A |

---

## Data Flow (How It All Connects)

```
                  ┌─────────────────────────────────────────────┐
                  │              documents/                      │
  DOCX/PDF ──────►│  parser.py  ──►  outline.py                 │
  (Upload)        │  (Docling + Word XML parsing)                │
                  └─────────────────┬───────────────────────────┘
                                    │ writes to SQLite
                                    ▼
                  ┌─────────────────────────────────────────────┐
                  │  SQLite DB                                   │
                  │  Document → Chapter → LearningModule         │
                  │                    → MicroModule             │
                  └────┬──────────────┬──────────────┬──────────┘
                       │              │              │
                       ▼              ▼              ▼
           ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐
           │   tutor/    │  │  learning/   │  │     learning/         │
           │             │  │  assessment  │  │     remediation       │
           │ TeachView   │  │  GenerateView│  │     GenerateView      │
           │ AskView     │  │  SubmitView  │  │                       │
           │             │  │              │  │                       │
           │ tutor_      │  │ assessment_  │  │ remediation_          │
           │ service.py  │  │ service.py   │  │ service.py            │
           │ qa_service  │  │ scoring_     │  │                       │
           │ .py         │  │ service.py   │  │                       │
           └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘
                  │                │                       │
                  └────────────────┴───────────────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   ollama.py          │
                        │  (HTTP client)       │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   Ollama (Local LLM) │
                        │   qwen3:1.7b         │
                        │   :11434             │
                        └─────────────────────┘
```

---

## Key Design Rules

| Rule | Where Enforced |
|------|----------------|
| AI never invents answers — only uses `source_text` | `tutor_service.py`, `question_answer_service.py` |
| `source_text` is **never overwritten** by AI output | `outline.py` |
| LLM temperature = `0.0` (deterministic, no hallucinations) | `ollama.py` |
| Pass threshold = **70%** strictly | `assessment_service.py`, `AssessmentAttempt` model |
| Student never sees correct answers / rubrics | `AssessmentQuestionStudentSerializer` |
| Retest excludes previously asked questions | `assessment_service.py` |

---

## Running the Project

```bash
# 1. Activate virtual environment
cd d:\LocalMind\backend
.\venv\Scripts\activate

# 2. Apply database migrations
python manage.py migrate

# 3. Start the development server
python manage.py runserver

# 4. Run all 35 unit tests
python manage.py test
```

**Server**: `http://127.0.0.1:8000`  
**Admin Panel**: `http://127.0.0.1:8000/admin`  
**Ollama must be running**: `ollama serve` (separate terminal)
