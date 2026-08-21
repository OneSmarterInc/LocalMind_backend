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
- 📝 Hybrid Assessment Engine (5 MCQs + 2 Subjective Questions)
- 🔄 Dynamic fresh retest questions (excludes previously asked questions)
- ✅ Deterministic scoring (MCQs graded in Python, Subjective validated by LLM against source text)
- 🔁 Targeted Remediation Engine (explains only missed concepts from source text)
- 📊 Micro-Module Progress Tracking (`not_started` → `in_progress` → `completed` / `needs_review`)

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
| POST | `/api/learning/assessment/generate/` | Generate 5 MCQs + 2 Subjective questions |
| POST | `/api/learning/assessment/<id>/submit/` | Submit answers for grading |
| POST | `/api/learning/remediation/generate/` | Get targeted review lesson for missed concepts |
| GET  | `/api/learning/micro-modules/<id>/` | Get micro-module progress status |

## Running Tests

```bash
.\venv\Scripts\python.exe manage.py test core documents learning tutor
```
