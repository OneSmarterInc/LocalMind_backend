# LocalMind — API Reference

**Base URL**: `http://127.0.0.1:8000/api`

All `POST` and `PATCH` requests must include the header:
```
Content-Type: application/json
```

No authentication is required in the current build.

---

## Table of Contents

1. [System](#1-system)
2. [Documents](#2-documents)
3. [Learning — Chapters & Modules](#3-learning--chapters--modules)
4. [Learning — Assessments](#4-learning--assessments)
5. [Learning — Remediation](#5-learning--remediation)
6. [Tutor — Teaching & Q&A](#6-tutor--teaching--qa)
7. [Data Models Reference](#7-data-models-reference)
8. [Status Codes Reference](#8-status-codes-reference)

---

## 1. System

### `GET /api/health/`

Health check — verify the backend is running.

**Response `200 OK`**
```json
{ "status": "healthy" }
```

---

## 2. Documents

### `POST /api/documents/upload/`

Upload a PDF, DOCX, or DOC file.

**Request**: `multipart/form-data`

| Field | Type   | Required | Description              |
|-------|--------|----------|--------------------------|
| file  | File   | ✅       | `.pdf`, `.docx`, or `.doc` |

**Response `201 Created`**
```json
{
  "id": "uuid",
  "title": "Chapter_06_Case_Studies",
  "original_name": "Chapter_06_Case_Studies.docx",
  "file_type": "docx",
  "status": "uploaded",
  "outline_source": "",
  "error_message": "",
  "created_at": "2026-08-22T09:00:00Z",
  "updated_at": "2026-08-22T09:00:00Z",
  "outline_confirmed_at": null,
  "chapters": []
}
```

> **Note**: Copy the returned `id` — it is used in all subsequent document endpoints.

---

### `POST /api/documents/{document_id}/process/`

Parse the uploaded document and extract real source text into SQLite chapters and modules. This is the core ingestion step.

**Request Body**: None

**Response `200 OK`** — Returns the document with fully populated chapters.

```json
{
  "id": "uuid",
  "title": "Chapter 6: Case Studies in Cybersecurity",
  "status": "awaiting_review",
  "outline_source": "source_hierarchy",
  "chapters": [
    {
      "id": "chapter-uuid",
      "title": "Chapter 6: Case Studies in Cybersecurity",
      "order": 1,
      "source_text": "...",
      "start_page": 1,
      "end_page": 58,
      "status": "not_started",
      "modules": [
        {
          "id": "module-uuid",
          "title": "Chapter Objectives",
          "order": 1,
          "source_text": "...",
          "start_page": 1,
          "end_page": 2,
          "status": "not_started"
        },
        {
          "id": "module-uuid",
          "title": "Section 1: Notable Cybersecurity Case Studies",
          "order": 2,
          "source_text": "...",
          "start_page": 3,
          "end_page": 40
        }
      ]
    }
  ]
}
```

**Error Responses**

| Status | Meaning |
|--------|---------|
| `409 Conflict` | Document is already processing or confirmed |
| `422 Unprocessable Entity` | Parsing failed (e.g. corrupted file) |

---

### `GET /api/documents/{document_id}/`

Get document detail including all chapters and nested modules.

**Response `200 OK`** — Same shape as process response above.

---

### `GET /api/documents/{document_id}/chapters/`

**Real Chapter API** — Returns all chapters with their complete extracted source text, used by the AI Tutor, Assessment Engine, and Remediation Engine.

**Response `200 OK`**
```json
{
  "document_id": "uuid",
  "title": "Chapter 6: Case Studies in Cybersecurity",
  "status": "awaiting_review",
  "chapters": [
    {
      "id": "chapter-uuid",
      "title": "Chapter 6: Case Studies in Cybersecurity",
      "order": 1,
      "document_id": "uuid",
      "source_text": "Full extracted text...",
      "start_page": 1,
      "end_page": 58,
      "is_user_edited": false,
      "status": "not_started",
      "started_at": null,
      "completed_at": null,
      "modules": [ ... ]
    }
  ]
}
```

---

### `GET /api/documents/{document_id}/structure/`

**Lightweight Navigation Tree** — Returns only IDs, titles, and order — no large `source_text` fields. Ideal for rendering sidebar/navigation UI.

**Response `200 OK`**
```json
{
  "document_id": "uuid",
  "title": "Chapter 6: Case Studies in Cybersecurity",
  "status": "awaiting_review",
  "chapters": [
    {
      "id": "chapter-uuid",
      "title": "Chapter 6: Case Studies in Cybersecurity",
      "order": 1,
      "modules": [
        { "id": "module-uuid", "title": "Chapter Objectives", "order": 1 },
        { "id": "module-uuid", "title": "Section 1: Notable Case Studies", "order": 2 }
      ]
    }
  ]
}
```

---

### `POST /api/documents/{document_id}/outline/confirm/`

Confirms the document outline. After confirmation the document cannot be reprocessed.

**Request Body**: None

**Response `200 OK`** — Returns the document with `status: "confirmed"`.

---

## 3. Learning — Chapters & Modules

### `GET /api/learning/chapters/{chapter_id}/`

Get a single chapter with its complete source text and all child modules.

**Response `200 OK`**
```json
{
  "id": "uuid",
  "document_id": "uuid",
  "title": "Chapter 6: Case Studies in Cybersecurity",
  "order": 1,
  "source_text": "...",
  "start_page": 1,
  "end_page": 58,
  "is_user_edited": false,
  "status": "not_started",
  "started_at": null,
  "completed_at": null,
  "modules": [ ... ]
}
```

---

### `GET /api/learning/modules/{module_id}/`

Get a single learning module with its source text.

**Response `200 OK`**
```json
{
  "id": "uuid",
  "chapter_id": "uuid",
  "title": "Section 1: Notable Cybersecurity Case Studies",
  "order": 2,
  "source_text": "...",
  "start_page": 3,
  "end_page": 40,
  "is_user_edited": false,
  "status": "not_started",
  "started_at": null,
  "completed_at": null
}
```

---

### `GET /api/learning/micro-modules/`

List all micro-modules across all documents.

**Response `200 OK`** — Array of micro-module objects.

---

### `PATCH /api/learning/micro-modules/{micro_module_id}/status/`

Update a micro-module's progress status. Call this when a student starts or completes a topic.

**Request Body**
```json
{ "status": "in_progress" }
```

**Allowed `status` values**

| Value | Meaning |
|-------|---------|
| `not_started` | Default — student hasn't opened this module |
| `in_progress` | Student has started reading / learning |
| `completed` | Student passed the assessment |
| `needs_review` | Student failed the assessment |

**Response `200 OK`** — Updated micro-module object.

---

## 4. Learning — Assessments

### `POST /api/learning/assessment/generate/`

Generate a **Hybrid Assessment** (5 MCQs + 2 Subjective questions). On a retest, previously asked questions are automatically excluded.

**Request Body — Option A**: Pass `micro_module_id` to load from the database.
```json
{
  "micro_module_id": "uuid",
  "num_mcqs": 5,
  "num_subjective": 2,
  "pass_percentage": 70
}
```

**Request Body — Option B**: Pass `source_text` directly in the payload.
```json
{
  "micro_module": {
    "id": "any-string-id",
    "title": "WannaCry Ransomware Attack (2017)",
    "source_text": "WannaCry was a global ransomware attack...",
    "start_page": 1,
    "end_page": 2
  },
  "num_mcqs": 5,
  "num_subjective": 2,
  "pass_percentage": 70
}
```

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `micro_module_id` | UUID | ❌ (or use `micro_module`) | — |
| `micro_module` | Object | ❌ (or use `micro_module_id`) | — |
| `num_mcqs` | Integer | ❌ | `5` |
| `num_subjective` | Integer | ❌ | `2` |
| `pass_percentage` | Integer | ❌ | `70` |

**Response `201 Created`**
```json
{
  "id": "assessment-uuid",
  "title": "WannaCry Ransomware Attack (2017)",
  "pass_percentage": 70,
  "questions_for_student": [
    {
      "id": "q1",
      "type": "mcq",
      "question": "Which exploit did WannaCry use to spread?",
      "options": [
        { "key": "A", "text": "Heartbleed" },
        { "key": "B", "text": "EternalBlue" },
        { "key": "C", "text": "Stuxnet" },
        { "key": "D", "text": "Melissa" }
      ]
    },
    {
      "id": "s1",
      "type": "subjective",
      "question": "Explain the impact of WannaCry on the UK NHS based on the provided text."
    }
  ],
  "created_at": "2026-08-22T09:30:00Z"
}
```

> **Important for Frontend**: `correct_answer`, `explanation`, and `expected_rubric` fields are **never included** in `questions_for_student`. They are redacted on the server side.

> Copy the returned `id` — it is used to fetch and submit the assessment.

---

### `GET /api/learning/assessment/{assessment_id}/`

Fetch the assessment question paper by ID. Same response shape as generate.

**Response `200 OK`** — Assessment object with `questions_for_student`.

---

### `POST /api/learning/assessment/{assessment_id}/submit/`

Submit student answers for grading. MCQs are graded deterministically. Subjective answers are evaluated by the AI against the source text.

**Request Body**
```json
{
  "submitted_answers": {
    "q1": "B",
    "q2": "A",
    "q3": "C",
    "q4": "B",
    "q5": "D",
    "s1": "WannaCry disrupted the NHS, canceling appointments and diverting ambulances.",
    "s2": "Marcus Hutchins stopped the spread by registering a kill switch domain."
  }
}
```

- MCQ keys (`q1`–`q5`): value is the answer key (`"A"`, `"B"`, `"C"`, or `"D"`).
- Subjective keys (`s1`, `s2`): value is the student's written answer as a string.

**Response `200 OK`**
```json
{
  "id": "attempt-uuid",
  "assessment": "assessment-uuid",
  "score": 6,
  "total_questions": 7,
  "percentage": 85.7,
  "passed": true,
  "micro_module_status": "completed",
  "detailed_results": [
    {
      "question_id": "q1",
      "type": "mcq",
      "submitted_answer": "B",
      "correct_answer": "B",
      "is_correct": true,
      "score_awarded": 1.0
    },
    {
      "question_id": "s1",
      "type": "subjective",
      "submitted_answer": "WannaCry disrupted the NHS...",
      "is_correct": true,
      "score_awarded": 1.0,
      "feedback": "Correctly identifies NHS disruption and ambulance diversion.",
      "missing_points": []
    }
  ],
  "created_at": "2026-08-22T09:45:00Z"
}
```

**Key Fields**

| Field | Type | Description |
|-------|------|-------------|
| `passed` | boolean | `true` if `percentage >= pass_percentage` (70%) |
| `micro_module_status` | string | `"completed"` if passed, `"needs_review"` if failed |

> Copy the returned `id` (attempt ID) if `passed: false` — used in the Remediation API.

---

## 5. Learning — Remediation

### `POST /api/learning/remediation/generate/`

Analyzes a failed assessment attempt and generates a targeted review lesson explaining **only the concepts the student missed**, grounded in the source text.

**Request Body — Option A**: By attempt ID (recommended after a failed submit)
```json
{
  "assessment_attempt_id": "attempt-uuid"
}
```

**Request Body — Option B**: By micro-module ID
```json
{
  "micro_module_id": "uuid"
}
```

**Response `200 OK`**
```json
{
  "title": "WannaCry Ransomware Attack (2017)",
  "attempt_score": "0/7 (0.0%)",
  "missed_concepts_summary": [
    "EternalBlue exploit and SMB protocol vulnerability",
    "Impact on UK National Health Service",
    "Discovery of kill switch domain by Marcus Hutchins"
  ],
  "remediation_explanation": [
    {
      "heading": "Review: EternalBlue and Propagation",
      "content": "According to the source text, WannaCry spread using EternalBlue..."
    },
    {
      "heading": "Review: How WannaCry Was Stopped",
      "content": "The text states that Marcus Hutchins registered a kill switch domain..."
    }
  ],
  "key_takeaways_to_remember": [
    "WannaCry exploited the SMB protocol via EternalBlue.",
    "A kill switch domain registered by Marcus Hutchins halted the spread."
  ]
}
```

**Error Responses**

| Status | Meaning |
|--------|---------|
| `400 Bad Request` | Neither `assessment_attempt_id` nor `micro_module_id` provided, or no failed attempts found |

---

## 6. Tutor — Teaching & Q&A

### `POST /api/tutor/teach/`

Generate a structured lesson explanation for a given topic. The AI strictly uses only the provided `source_text` — no outside information is ever added.

**Request Body**
```json
{
  "micro_module": {
    "title": "Stuxnet (2010)",
    "source_text": "Stuxnet is widely regarded as one of the most sophisticated cyber-attacks ever discovered. It was a computer worm specifically designed to target Iran's nuclear enrichment facilities...",
    "start_page": 1,
    "end_page": 2
  }
}
```

**Response `200 OK`**
```json
{
  "title": "Stuxnet (2010)",
  "simplified_explanation": "Stuxnet was a highly complex computer worm built to target Iran's Natanz nuclear enrichment plant by manipulating Siemens PLCs that controlled centrifuges...",
  "key_takeaways": [
    "Stuxnet targeted Iran's Natanz uranium enrichment plant.",
    "It targeted Siemens Programmable Logic Controllers (PLCs).",
    "Centrifuges were physically damaged while false normal readings were sent."
  ]
}
```

---

### `POST /api/tutor/ask/`

Ask a question about a topic. Supports two modes:

**Option A — New Question** (creates a new conversation):
```json
{
  "micro_module": {
    "id": "any-string-id",
    "title": "Stuxnet (2010)",
    "source_text": "Stuxnet was a computer worm targeting Iran's Natanz uranium enrichment plant...",
    "start_page": 1,
    "end_page": 2
  },
  "question": "What specific hardware did Stuxnet target?"
}
```

**Option B — Follow-up Question** (continues an existing conversation — no `source_text` needed):
```json
{
  "conversation_id": "uuid",
  "question": "Which facility in Iran was targeted?"
}
```

**Response `200 OK`**
```json
{
  "answer_status": "answered",
  "answer": "According to the provided text, Stuxnet targeted Siemens Programmable Logic Controllers (PLCs).",
  "key_points": [
    "Siemens PLCs were the target.",
    "PLCs controlled centrifuges in the facility."
  ],
  "conversation_id": "uuid",
  "message_id": "uuid"
}
```

**`answer_status` values**

| Value | Meaning |
|-------|---------|
| `answered` | Question answered from source text |
| `not_in_source` | Question is outside the source material — AI refuses to invent an answer |

---

### `GET /api/tutor/conversations/{conversation_id}/`

Fetch complete message history for a conversation.

**Response `200 OK`**
```json
{
  "id": "uuid",
  "micro_module_id": "any-string-id",
  "micro_module_title": "Stuxnet (2010)",
  "messages": [
    {
      "id": "uuid",
      "role": "student",
      "content": "What specific hardware did Stuxnet target?",
      "created_at": "2026-08-22T09:05:00Z"
    },
    {
      "id": "uuid",
      "role": "tutor",
      "content": "According to the provided text, Stuxnet targeted Siemens PLCs...",
      "created_at": "2026-08-22T09:05:02Z"
    }
  ]
}
```

---

## 7. Data Models Reference

### Document Statuses

| Value | Meaning |
|-------|---------|
| `uploaded` | File uploaded, not yet processed |
| `processing` | Document is currently being parsed |
| `awaiting_review` | Parsing complete, chapters created |
| `confirmed` | Outline confirmed — locked for use |
| `error` | Parsing failed (check `error_message` field) |

### Module/Chapter/MicroModule Statuses

| Value | Meaning |
|-------|---------|
| `not_started` | Default — student hasn't interacted |
| `in_progress` | Student has started |
| `completed` | Student passed assessment (≥ 70%) |
| `needs_review` | Student failed assessment (< 70%) |

### Question Types in Assessment

| Type | Description |
|------|-------------|
| `mcq` | Multiple Choice — 4 options (A, B, C, D) |
| `subjective` | Open-ended written answer, evaluated by AI |

---

## 8. Status Codes Reference

| HTTP Status | Meaning |
|-------------|---------|
| `200 OK` | Successful GET / PATCH / POST (non-create) |
| `201 Created` | Successful resource creation (upload, assessment generate) |
| `400 Bad Request` | Missing or invalid request parameters |
| `404 Not Found` | Resource with the given ID does not exist |
| `409 Conflict` | Operation not allowed in current state (e.g., reprocessing a confirmed document) |
| `422 Unprocessable Entity` | File processing failed (parsing error) |
| `500 Internal Server Error` | Unexpected server error (check server logs) |
