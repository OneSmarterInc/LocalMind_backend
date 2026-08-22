# LocalMind

A local-first AI tutoring application. LocalMind processes your documents and acts as a personal AI tutor that strictly explains only what is in the source material — no hallucinations, no extra knowledge injected.

## Tech Stack
- **Backend**: Python 3.12, Django 5.2.x, Django REST Framework, SQLite
- **AI Model**: Ollama `qwen3:1.7b` (local, no cloud dependency)
- **Document Parsing**: Docling

## Features Implemented
- 📄 Document upload & outline/chapter extraction
- 🧑‍🏫 Source-grounded AI tutoring (strict zero-hallucination)
- 💬 Multi-turn conversation history (DB-backed)
- 📝 Hybrid Assessment Engine (5 MCQs + 2 Subjective Questions) for Micro-Modules and Chapters
- 🏆 Chapter-Level Assessment upon completion of chapter micro-modules
- 🔄 Dynamic fresh retest questions (excludes previously asked questions)
- ✅ Deterministic scoring (MCQs graded in Python, Subjective validated by LLM against source text)
- 🔁 Targeted Remediation Engine for Micro-Modules & Chapters (explains only missed concepts from source text)
- 📊 Micro-Module & Chapter Progress Tracking (`not_started` → `in_progress` → `completed` / `needs_review`)

## Getting Started

### Prerequisites
- Python 3.12+
- [Ollama](https://ollama.ai/) with `qwen3:1.7b` pulled

```bash
ollama pull qwen3:1.7b
```

### Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows
# or: source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

### API Base URL
`http://127.0.0.1:8000/api/`

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload/` | Upload a document |
| POST | `/api/tutor/teach/` | Get AI tutor explanation for a micro-module |
| POST | `/api/tutor/ask/` | Ask a follow-up question (with conversation history) |
| GET  | `/api/learning/chapters/` | List chapters with progress & micro-modules |
| GET  | `/api/learning/chapters/<id>/` | Get chapter details & readiness for chapter assessment |
| PATCH| `/api/learning/chapters/<id>/status/` | Update chapter status manually |
| GET  | `/api/learning/micro-modules/<id>/` | Get micro-module progress status |
| POST | `/api/learning/assessment/generate/` | Generate 5 MCQs + 2 Subjectives for Chapter or Micro-Module |
| GET  | `/api/learning/assessment/<id>/` | Get student question paper (answers redacted) |
| POST | `/api/learning/assessment/<id>/submit/` | Submit answers for grading (updates Chapter / Micro-Module status) |
| POST | `/api/learning/remediation/generate/` | Get targeted review lesson for missed concepts |

## Running Tests

```bash
.\venv\Scripts\python.exe manage.py test core documents learning tutor
```

