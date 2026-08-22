# LocalMind — Intern QA & API Testing Manual

Welcome to the **LocalMind** testing guide! This document is designed for interns and QA testers to test all LocalMind backend APIs step-by-step using **Postman** (or any API client).

---

## 📌 1. Before You Start (Prerequisites)

Make sure the following 2 services are running on your machine:

1. **Ollama AI Service**:
   - Open a terminal and verify: `ollama run qwen3:1.7b`
   - Ollama should be accessible at: `http://127.0.0.1:11434`
2. **LocalMind Django Backend**:
   - Terminal command: `.\venv\Scripts\python.exe manage.py runserver`
   - Server runs at: `http://127.0.0.1:8000`
3. **Postman Header**:
   - For all `POST` / `PATCH` requests, ensure you set:
     - **Key**: `Content-Type`
     - **Value**: `application/json`

---

## 📋 Test Execution Checklist (16 Test Cases)

- [ ] **TC-01**: Backend Server Health Check
- [ ] **TC-02**: Document Upload & Chapter Extraction
- [ ] **TC-03**: AI Tutor Micro-Module Teaching (Zero-Hallucination)
- [ ] **TC-04**: Ask Question — Answerable Fact from Source Text
- [ ] **TC-05**: Ask Question — Out-of-Scope Fact Refusal
- [ ] **TC-06**: Follow-up Question — Multi-Turn Conversation (Option B)
- [ ] **TC-07**: Get Conversation Message History
- [ ] **TC-08**: Generate Hybrid Assessment (5 MCQs + 2 Subjective)
- [ ] **TC-09**: Retrieve Student Question Paper (Answers Redacted)
- [ ] **TC-10**: Submit Passing Assessment Attempt ($\ge 70\% \rightarrow$ Completed)
- [ ] **TC-11**: Submit Failing Assessment Attempt ($< 70\% \rightarrow$ Needs Review)
- [ ] **TC-12**: Generate Targeted Remediation Review Lesson
- [ ] **TC-13**: Retest Assessment — Fresh Non-Duplicate Questions
- [ ] **TC-14**: Chapter Progress & Assessment Readiness Tracking
- [ ] **TC-15**: Generate & Submit Chapter Assessment (Comprehensive)
- [ ] **TC-16**: Chapter-Level Remediation Review Lesson

---

# 🚀 Step-by-Step Test Cases

---

### Test Case 01: Backend Server Health Check
**Objective**: Verify that the Django backend server is up and responsive.

* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/health/`
* **Headers**: None required
* **Body**: None

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "status": "healthy"
}
```
* **Pass Criteria**: Status is 200 and response says `"status": "healthy"`.

---

### Test Case 02: Document Upload & Chapter Extraction
**Objective**: Test uploading a PDF document and extracting its outline and chapters.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/documents/upload/`
* **Body Type**: `form-data`
  * Key: `file` (Change key type from *Text* to *File*)
  * Value: Select any sample `.pdf` file from your computer

#### Expected Result:
* **Status Code**: `201 Created`
* **Response Body**:
```json
{
  "id": "uuid-here",
  "title": "sample.pdf",
  "total_pages": 5,
  "outline": [ ... ]
}
```
* **Pass Criteria**: Status is 201 and file is parsed with page count and outline.

---

### Test Case 03: AI Tutor Micro-Module Teaching
**Objective**: Test that the AI tutor explains a concept strictly using source text without adding external examples (like cars, rockets, or sports).

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/tutor/teach/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "title": "Newton's First Law of Motion",
    "source_text": "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced external force. This tendency is known as inertia.",
    "start_page": 1,
    "end_page": 2
  }
}
```

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "title": "Newton's First Law of Motion",
  "simplified_explanation": "...",
  "key_takeaways": [
    "An object at rest remains at rest unless an external force acts.",
    "An object in motion continues in motion with the same speed and direction unless acted upon.",
    "This tendency is called inertia."
  ]
}
```
* **Pass Criteria**:
  - Status is 200.
  - `simplified_explanation` simplifies the text without introducing outside trivia (no mention of vehicles, football, rocket ships).
  - `key_takeaways` has 2 to 4 clear bullet points.

---

### Test Case 04: Ask Question — Answerable Fact from Source Text
**Objective**: Verify the tutor answers factual questions directly present in the source text and starts a new conversation.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/tutor/ask/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "id": "mm-physics-101",
    "title": "Newton's First Law",
    "source_text": "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced external force. This tendency is known as inertia.",
    "start_page": 1,
    "end_page": 2
  },
  "question": "What is the tendency of an object to resist changes in motion called?"
}
```

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "answer_status": "answered",
  "answer": "According to the provided text, this tendency is known as inertia.",
  "conversation_id": "7b68e9f2-...",
  "message_id": "..."
}
```
* **Action**: **Copy the `conversation_id` value from the response** for Test Case 06 & 07!
* **Pass Criteria**: `answer_status` is `"answered"` and `answer` correctly states "inertia".

---

### Test Case 05: Ask Question — Out-of-Scope Fact Refusal
**Objective**: Verify the AI strictly refuses to answer questions about facts not mentioned in the source text.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/tutor/ask/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "id": "mm-physics-101",
    "title": "Newton's First Law",
    "source_text": "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced external force. This tendency is known as inertia.",
    "start_page": 1,
    "end_page": 2
  },
  "question": "In what year was Isaac Newton born?"
}
```

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "answer_status": "not_in_source",
  "answer": "I cannot answer this question because the provided text does not mention Isaac Newton's birth year or historical details.",
  "conversation_id": "..."
}
```
* **Pass Criteria**: `answer_status` is `"not_in_source"` and the model does NOT invent the year 1643.

---

### Test Case 06: Follow-up Question — Multi-Turn Conversation (Option B)
**Objective**: Verify that follow-up questions work by passing ONLY the `conversation_id` and `question` (without re-sending `source_text`).

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/tutor/ask/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "conversation_id": "<PASTE_CONVERSATION_ID_FROM_TC_04>",
  "question": "What is required to change the speed or direction of an object?"
}
```

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "answer_status": "answered",
  "answer": "An unbalanced external force is required to change the speed or direction of an object.",
  "conversation_id": "<SAME_CONVERSATION_ID>"
}
```
* **Pass Criteria**: Status is 200, uses the existing conversation, and correctly answers "unbalanced external force".

---

### Test Case 07: Get Full Conversation Message History
**Objective**: Verify that all messages in a conversation are stored in SQLite and can be retrieved.

* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/tutor/conversations/<PASTE_CONVERSATION_ID_FROM_TC_04>/`
* **Headers**: None required
* **Body**: None

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "id": "7b68e9f2-...",
  "micro_module_id": "mm-physics-101",
  "micro_module_title": "Newton's First Law",
  "messages": [
    { "role": "student", "content": "What is the tendency..." },
    { "role": "tutor", "content": "According to the provided text..." },
    { "role": "student", "content": "What is required to change..." },
    { "role": "tutor", "content": "An unbalanced external force..." }
  ]
}
```
* **Pass Criteria**: Returns the full list of student and tutor messages in chronological order.

---

### Test Case 08: Generate Hybrid Assessment (5 MCQs + 2 Subjective)
**Objective**: Verify that generating an assessment produces exactly **5 Multiple Choice Questions** (4 options each) and **2 Subjective Questions** with redacted student answers.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/generate/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "id": "mm-physics-assessment-01",
    "title": "Newton's First Law",
    "source_text": "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced external force. This tendency is known as inertia.",
    "start_page": 1,
    "end_page": 2
  },
  "num_mcqs": 5,
  "num_subjective": 2,
  "pass_percentage": 70
}
```

#### Expected Result:
* **Status Code**: `201 Created`
* **Response Body**:
```json
{
  "id": "276cfb7c-...",
  "title": "Newton's First Law",
  "pass_percentage": 70,
  "questions_for_student": [
    { "id": "q1", "type": "mcq", "question": "...", "options": [ ... ] },
    { "id": "q2", "type": "mcq", "question": "...", "options": [ ... ] },
    { "id": "q3", "type": "mcq", "question": "...", "options": [ ... ] },
    { "id": "q4", "type": "mcq", "question": "...", "options": [ ... ] },
    { "id": "q5", "type": "mcq", "question": "...", "options": [ ... ] },
    { "id": "s1", "type": "subjective", "question": "..." },
    { "id": "s2", "type": "subjective", "question": "..." }
  ]
}
```
* **Action**: **Copy the `id` from the response** (this is your `assessment_id`)!
* **Pass Criteria**:
  - Returns `pass_percentage: 70`.
  - Exactly 5 MCQs (`q1` to `q5`) and 2 Subjectives (`s1`, `s2`).
  - `correct_answer`, `explanation`, and `expected_rubric` are NOT leaked to the student.

---

### Test Case 09: Retrieve Student Question Paper
**Objective**: Verify a student can fetch their question paper by assessment ID.

* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/<PASTE_ASSESSMENT_ID_FROM_TC_08>/`
* **Expected Status**: `200 OK`
* **Pass Criteria**: Returns the assessment details and the 7 redacted questions.

---

### Test Case 10: Submit Passing Assessment ($\ge 70\%$)
**Objective**: Submit correct answers for all 7 questions and verify score calculation and module completion.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/<PASTE_ASSESSMENT_ID_FROM_TC_08>/submit/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
*(Note: Match MCQ keys A/B/C/D to your generated questions)*
```json
{
  "submitted_answers": {
    "q1": "B",
    "q2": "A",
    "q3": "B",
    "q4": "B",
    "q5": "A",
    "s1": "Inertia is the natural tendency of an object to remain at rest or keep moving with uniform speed unless acted on by an unbalanced external force.",
    "s2": "An unbalanced external force is required to change an object's speed or direction of motion."
  }
}
```

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "score": 7,
  "total_questions": 7,
  "percentage": 100.0,
  "passed": true,
  "detailed_results": [ ... ],
  "micro_module_status": "completed"
}
```
* **Pass Criteria**:
  - `percentage`: $\ge 70.0\%$
  - `passed`: `true`
  - `micro_module_status`: `"completed"`

---

### Test Case 11: Submit Failing Assessment ($< 70\%$)
**Objective**: Submit incorrect answers to trigger a failed attempt and verify status changes to `needs_review`.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/<PASTE_ASSESSMENT_ID_FROM_TC_08>/submit/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "submitted_answers": {
    "q1": "D",
    "q2": "D",
    "q3": "D",
    "q4": "D",
    "q5": "D",
    "s1": "I don't know the answer.",
    "s2": "Nothing happens."
  }
}
```

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "id": "attempt-uuid-here",
  "score": 0,
  "total_questions": 7,
  "percentage": 0.0,
  "passed": false,
  "micro_module_status": "needs_review"
}
```
* **Action**: **Copy the `id` from the response** (this is your `assessment_attempt_id` for TC-12)!
* **Pass Criteria**:
  - `percentage`: $< 70.0\%$
  - `passed`: `false`
  - `micro_module_status`: `"needs_review"`

---

### Test Case 12: Generate Targeted Remediation Review Lesson
**Objective**: Verify that when a student fails an assessment, the backend analyzes their missed questions and generates a focused review lesson explaining ONLY the missed concepts.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/remediation/generate/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "assessment_attempt_id": "<PASTE_ATTEMPT_ID_FROM_TC_11>"
}
```

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "title": "Newton's First Law",
  "attempt_score": "0/7 (0.0%)",
  "missed_concepts_summary": [
    "Concept of inertia was missed",
    "Role of unbalanced external force was not understood"
  ],
  "remediation_explanation": [
    {
      "heading": "Review: What is Inertia?",
      "content": "Inertia is the tendency of an object to remain in its state of rest or uniform motion..."
    },
    {
      "heading": "Review: Unbalanced External Force",
      "content": "An object will only change its motion when an unbalanced external force acts upon it..."
    }
  ],
  "key_takeaways_to_remember": [
    "An object at rest stays at rest unless acted upon by an external force.",
    "Inertia is the resistance to change in motion."
  ]
}
```
* **Pass Criteria**: Status is 200 and returns targeted review headings and takeaways for the missed concepts.

---

### Test Case 13: Retest Assessment — Dynamic Fresh Questions
**Objective**: Verify that when a student takes a retest on the same micro-module, the backend automatically excludes previous questions and generates a **brand new unique question set**.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/generate/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "id": "mm-physics-assessment-01",
    "title": "Newton's First Law",
    "source_text": "An object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced external force. This tendency is known as inertia.",
    "start_page": 1,
    "end_page": 2
  },
  "num_mcqs": 5,
  "num_subjective": 2,
  "pass_percentage": 70
}
```

#### Expected Result:
* **Status Code**: `201 Created`
* **Validation**:
  - Generates a new `assessment_id`.
  - Compare the 5 MCQs and 2 Subjective questions to Test Case 08 — **the question wordings and angles must be fresh and not identical repeats**.

---

### Test Case 14: Chapter Progress & Assessment Readiness Tracking
**Objective**: Verify that a student can inspect Chapter progress and determine whether all child micro-modules are completed and ready for Chapter Assessment.

* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/learning/chapters/<CHAPTER_ID>/`
* **Headers**: None required

#### Expected Result:
* **Status Code**: `200 OK`
* **Response Body**:
```json
{
  "id": "chapter-uuid",
  "title": "Laws of Motion",
  "status": "in_progress",
  "micro_modules_count": 2,
  "completed_micro_modules_count": 2,
  "all_micro_modules_completed": true,
  "ready_for_assessment": true,
  "micro_modules": [ ... ]
}
```
* **Pass Criteria**: `ready_for_assessment` is `true` when all micro-modules have status `completed`.

---

### Test Case 15: Generate & Submit Chapter Assessment (Comprehensive)
**Objective**: Verify generating a comprehensive chapter-level assessment aggregating source text across all child micro-modules, and submitting it to complete the Chapter.

#### Step 15A: Generate Chapter Assessment
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/generate/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "chapter_id": "<CHAPTER_ID>",
  "num_mcqs": 5,
  "num_subjective": 2,
  "pass_percentage": 70
}
```

* **Expected Status**: `201 Created`
* **Validation**: Returns `assessment_type: "chapter"`, `chapter: "<CHAPTER_ID>"`, and 7 redacted questions testing concepts across the chapter.

#### Step 15B: Submit Passing Chapter Assessment
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/<ASSESSMENT_ID>/submit/`
* **Headers**: `Content-Type: application/json`
* **Body**:
```json
{
  "submitted_answers": {
    "q1": "A",
    "q2": "B",
    "q3": "A",
    "q4": "C",
    "q5": "A",
    "s1": "Inertia is the tendency of an object to resist change in its state of motion.",
    "s2": "An unbalanced force is required to accelerate an object."
  }
}
```

* **Expected Status**: `200 OK`
* **Validation**: Returns `"passed": true`, `"chapter_status": "completed"`.

---

### Test Case 16: Chapter-Level Targeted Remediation
**Objective**: Verify that if a chapter assessment is failed, the backend generates a targeted remediation review for missed concepts in the chapter.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/remediation/generate/`
* **Headers**: `Content-Type: application/json`
* **Body**:
```json
{
  "chapter_id": "<CHAPTER_ID>"
}
```

* **Expected Status**: `200 OK`
* **Validation**:
  - `chapter_id` matches the chapter ID.
  - `missed_concepts_summary` lists the missed chapter concepts.
  - `remediation_explanation` provides grounded explanations for missed topics.

---

## 🎯 Summary of Pass Criteria for Interns:
1. All 16 test cases return status code `200` or `201`.
2. AI explanations never invent unmentioned trivia.
3. Multi-turn chat remembers context without re-sending `source_text`.
4. Micro-Module and Chapter assessments pass at $\ge 70\%$ threshold.
5. Failed tests trigger `needs_review` and generate targeted remediation review notes.
6. Chapter assessment combines chapter knowledge and updates chapter status upon passing.
