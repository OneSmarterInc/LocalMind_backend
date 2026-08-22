# Postman Testing Guide — Chapter 6 Case Studies in Cybersecurity

This guide provides the complete, step-by-step API testing workflow using your uploaded file: **`Chapter_06_Case_Studies.docx`**.

---

## ⚙️ Environment Setup

* **Base URL**: `http://127.0.0.1:8000/api`
* **Ollama Model**: `qwen3:1.7b` running locally on `http://127.0.0.1:11434`
* **File Under Test**: `d:\LocalMind\Chapter_06_Case_Studies.docx`

---

## 📌 Testing Flow at a Glance

```text
1. Upload DOCX ───────> POST /api/documents/upload/
                              │
2. Process Sections ──> POST /api/documents/<doc_id>/process/
                              │
3. View Real Text ────> GET  /api/documents/<doc_id>/chapters/
                              │
4. AI Tutor Teach ────> POST /api/tutor/teach/
                              │
5. Ask Question ──────> POST /api/tutor/ask/ (In-Scope & Out-of-Scope tests)
                              │
6. Follow-up Chat ────> POST /api/tutor/ask/ (Using conversation_id)
                              │
7. Generate Quiz ─────> POST /api/learning/assessment/generate/ (5 MCQs + 2 Subjective)
                              │
8. Submit & Grade ────> POST /api/learning/assessment/<id>/submit/ (70% Pass Rule)
                              │
9. Remediation ───────> POST /api/learning/remediation/generate/ (If failed)
```

---

# 🚀 Step-by-Step API Requests & Payloads

---

### Step 1: Upload Document (`POST /api/documents/upload/`)

Upload `Chapter_06_Case_Studies.docx` into LocalMind.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/documents/upload/`
* **Body Type**: `form-data`
  * Key: `file` (Select *File* from the dropdown)
  * Value: Browse and select `Chapter_06_Case_Studies.docx`

#### Expected Response (`201 Created`):
```json
{
  "id": "c6a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "title": "Chapter_06_Case_Studies",
  "original_name": "Chapter_06_Case_Studies.docx",
  "file_type": "docx",
  "status": "uploaded",
  "chapters": []
}
```
👉 **Copy the returned `"id"`** $\rightarrow$ This is your `DOCUMENT_ID`.

---

### Step 2: Process Document Sections & Chapters (`POST /api/documents/<DOCUMENT_ID>/process/`)

Parses the Word document styles and populates `Chapter` and `LearningModule` rows in SQLite with actual extracted text.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/documents/<PASTE_DOCUMENT_ID>/process/`
* **Headers**: None
* **Body**: None

#### Expected Response (`200 OK`):
```json
{
  "id": "<DOCUMENT_ID>",
  "title": "Chapter 6: Case Studies in Cybersecurity",
  "status": "awaiting_review",
  "outline_source": "source_hierarchy",
  "chapters": [
    {
      "id": "chapter-uuid-1",
      "title": "Chapter 6: Case Studies in Cybersecurity",
      "order": 1,
      "source_text": "...",
      "modules": [
        { "title": "Chapter Objectives" },
        { "title": "Introduction: The Value of Learning from Real Incidents" },
        { "title": "Section 1: Notable Cybersecurity Case Studies" },
        { "title": "Interactive Scenario Analysis: The Phishing Attack on Acme Corporation" },
        { "title": "Epilogue: Reflecting on the Lessons Learned" },
        { "title": "Exercise Questions" }
      ]
    }
  ]
}
```
👉 **Copy the `"id"` of the chapter or any module from the response.**

---

### Step 3: Fetch Real Chapter Source Text (`GET /api/documents/<DOCUMENT_ID>/chapters/`)

Returns the complete extracted source text for Chapter 6 directly from SQLite.

* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/documents/<PASTE_DOCUMENT_ID>/chapters/`
* **Expected Response (`200 OK`)**: Complete source text with zero summary alterations.

---

### Step 4: AI Tutor Grounded Teaching (`POST /api/tutor/teach/`)

Tests that the AI tutor explains the **Stuxnet Case Study** strictly using the facts in the text.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/tutor/teach/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "title": "Stuxnet (2010)",
    "source_text": "Stuxnet is widely regarded as one of the most sophisticated cyber-attacks ever discovered. It was a computer worm specifically designed to target Iran's nuclear enrichment facilities, particularly the Natanz uranium enrichment plant. Stuxnet targeted Programmable Logic Controllers (PLCs) manufactured by Siemens that were used to control centrifuges in the enrichment facility. The worm secretly altered the rotational speeds of the centrifuges, causing them to tear themselves apart, while sending false feedback signals to the control room.",
    "start_page": 1,
    "end_page": 2
  }
}
```

#### Expected Response (`200 OK`):
```json
{
  "title": "Stuxnet (2010)",
  "simplified_explanation": "Stuxnet was a highly complex computer worm created to target Iran's Natanz nuclear uranium enrichment facility. It focused on Siemens Programmable Logic Controllers (PLCs) regulating centrifuges, covertly altering centrifuge speeds to cause physical damage while displaying false normal status readings to operators.",
  "key_takeaways": [
    "Stuxnet targeted Iran's Natanz nuclear uranium enrichment plant.",
    "It altered Siemens PLC speeds to physically damage centrifuges.",
    "It reported false normal feedback signals to the control room."
  ]
}
```

---

### Step 5: Ask Question — In-Scope Fact (`POST /api/tutor/ask/`)

Ask a factual question directly covered in the Stuxnet text.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/tutor/ask/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "id": "mm-stuxnet-01",
    "title": "Stuxnet (2010)",
    "source_text": "Stuxnet was a computer worm specifically designed to target Iran's nuclear enrichment facilities, particularly the Natanz uranium enrichment plant. Stuxnet targeted Programmable Logic Controllers (PLCs) manufactured by Siemens that were used to control centrifuges.",
    "start_page": 1,
    "end_page": 2
  },
  "question": "Which specific hardware components and brand did Stuxnet target in the facility?"
}
```

#### Expected Response (`200 OK`):
```json
{
  "answer_status": "answered",
  "answer": "According to the provided text, Stuxnet targeted Programmable Logic Controllers (PLCs) manufactured by Siemens that were used to control centrifuges.",
  "key_points": [
    "Targeted Programmable Logic Controllers (PLCs).",
    "PLCs were manufactured by Siemens."
  ],
  "conversation_id": "8f3b2a1c-...",
  "message_id": "..."
}
```
👉 **Copy the returned `"conversation_id"`** for Step 7!

---

### Step 6: Ask Question — Out-of-Scope Fact Refusal (`POST /api/tutor/ask/`)

Ask about a detail NOT mentioned in the text (e.g. who wrote the code or what country developed it).

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/tutor/ask/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "id": "mm-stuxnet-01",
    "title": "Stuxnet (2010)",
    "source_text": "Stuxnet was a computer worm specifically designed to target Iran's nuclear enrichment facilities, particularly the Natanz uranium enrichment plant. Stuxnet targeted Programmable Logic Controllers (PLCs) manufactured by Siemens.",
    "start_page": 1,
    "end_page": 2
  },
  "question": "Which intelligence agency created Stuxnet and how much did it cost to develop?"
}
```

#### Expected Response (`200 OK`):
```json
{
  "answer_status": "not_in_source",
  "answer": "This detail is not covered in the current learning material.",
  "key_points": []
}
```
* **Pass Validation**: The AI refuses to speculate or guess outside information.

---

### Step 7: Follow-up Chat with Conversation History (`POST /api/tutor/ask/`)

Send a follow-up question using **ONLY** `conversation_id` (no duplicate `source_text`).

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/tutor/ask/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "conversation_id": "<PASTE_CONVERSATION_ID_FROM_STEP_5>",
  "question": "What facility in Iran was particularly targeted?"
}
```

#### Expected Response (`200 OK`):
```json
{
  "answer_status": "answered",
  "answer": "The text states that the Natanz uranium enrichment plant was particularly targeted.",
  "conversation_id": "<SAME_CONVERSATION_ID>"
}
```

---

### Step 8: Generate Hybrid Assessment on Chapter 6 Case Studies (`POST /api/learning/assessment/generate/`)

Generates **5 MCQs** (with 4 options A, B, C, D) + **2 Subjective Conceptual Questions**.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/generate/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "micro_module": {
    "id": "mm-case-studies-assessment",
    "title": "WannaCry Ransomware Attack (2017)",
    "source_text": "WannaCry was a global ransomware attack that affected hundreds of thousands of computers in over 150 countries. It spread using the EternalBlue exploit, which targeted a vulnerability in Microsoft's Server Message Block (SMB) protocol. The attack encrypted files on infected systems and demanded ransom payments in Bitcoin. The UK's National Health Service (NHS) was heavily disrupted, leading to canceled appointments and diverted ambulances. Marcus Hutchins discovered a kill switch domain that stopped the worm from spreading.",
    "start_page": 1,
    "end_page": 2
  },
  "num_mcqs": 5,
  "num_subjective": 2,
  "pass_percentage": 70
}
```

#### Expected Response (`201 Created`):
```json
{
  "id": "assessment-uuid-99",
  "title": "WannaCry Ransomware Attack (2017)",
  "pass_percentage": 70,
  "questions_for_student": [
    {
      "id": "q1",
      "type": "mcq",
      "question": "Which exploit did the WannaCry ransomware use to spread across networks?",
      "options": [
        { "key": "A", "text": "Heartbleed" },
        { "key": "B", "text": "EternalBlue" },
        { "key": "C", "text": "Stuxnet" },
        { "key": "D", "text": "Melissa" }
      ]
    },
    {
      "id": "q2",
      "type": "mcq",
      "question": "Which protocol vulnerability was targeted by EternalBlue in WannaCry?",
      "options": [
        { "key": "A", "text": "Server Message Block (SMB)" },
        { "key": "B", "text": "HTTP/HTTPS" },
        { "key": "C", "text": "FTP" },
        { "key": "D", "text": "DNS" }
      ]
    },
    {
      "id": "q3", "type": "mcq", "question": "...", "options": [ ... ]
    },
    {
      "id": "q4", "type": "mcq", "question": "...", "options": [ ... ]
    },
    {
      "id": "q5", "type": "mcq", "question": "...", "options": [ ... ]
    },
    {
      "id": "s1",
      "type": "subjective",
      "question": "Explain the impact of the WannaCry attack on the UK's National Health Service (NHS) based on the text."
    },
    {
      "id": "s2",
      "type": "subjective",
      "question": "How was the spread of WannaCry eventually halted according to the provided material?"
    }
  ]
}
```
👉 **Copy the returned `"id"`** $\rightarrow$ This is your `ASSESSMENT_ID`.

---

### Step 9: Submit Passing Answers ($\ge 70\% \rightarrow$ Completed)

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/<PASTE_ASSESSMENT_ID>/submit/`
* **Headers**: `Content-Type: application/json`
* **Body** (`raw` > `JSON`):
```json
{
  "submitted_answers": {
    "q1": "B",
    "q2": "A",
    "q3": "B",
    "q4": "A",
    "q5": "C",
    "s1": "The WannaCry attack heavily disrupted the UK NHS, resulting in canceled medical appointments and diverted ambulances because critical hospital computer systems were encrypted.",
    "s2": "The spread was halted when Marcus Hutchins registered a kill switch domain that prevented the malware from spreading further."
  }
}
```

#### Expected Response (`200 OK`):
```json
{
  "score": 7,
  "total_questions": 7,
  "percentage": 100.0,
  "passed": true,
  "micro_module_status": "completed",
  "detailed_results": [
    { "question_id": "q1", "type": "mcq", "is_correct": true, "score_awarded": 1.0 },
    { ... },
    {
      "question_id": "s1",
      "type": "subjective",
      "is_correct": true,
      "score_awarded": 1.0,
      "feedback": "The student correctly explained the cancellation of appointments and ambulance diversion according to the source text."
    }
  ]
}
```

---

### Step 10: Submit Failing Answers ($< 70\% \rightarrow$ Needs Review) & Request Remediation

#### A. Submit Wrong Answers:
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/<PASTE_ASSESSMENT_ID>/submit/`
* **Body**:
```json
{
  "submitted_answers": {
    "q1": "D",
    "q2": "D",
    "q3": "D",
    "q4": "D",
    "q5": "D",
    "s1": "I do not know.",
    "s2": "Nobody stopped it."
  }
}
```
* Response gives `passed: false`, `micro_module_status: "needs_review"`. Copy the returned `"id"` (your `ATTEMPT_ID`).

#### B. Request Remediation Review Lesson:
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/remediation/generate/`
* **Headers**: `Content-Type: application/json`
* **Body**:
```json
{
  "assessment_attempt_id": "<PASTE_ATTEMPT_ID>"
}
```

#### Expected Response (`200 OK`):
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
      "content": "WannaCry spread using EternalBlue, which attacked a flaw in Microsoft's Server Message Block (SMB) protocol..."
    },
    {
      "heading": "Review: How WannaCry Was Stopped",
      "content": "The spread of WannaCry was stopped when Marcus Hutchins discovered and registered a kill switch domain..."
    }
  ],
  "key_takeaways_to_remember": [
    "WannaCry exploited SMB via EternalBlue.",
    "A kill switch domain registered by Marcus Hutchins stopped the spread."
  ]
}
```

---

### Step 11: Retest Assessment (Dynamic Fresh Question Set)

Calling `POST /api/learning/assessment/generate/` on the same micro-module automatically instructs the AI to **exclude the previous questions** and generate a **fresh, distinct set of 5 MCQs + 2 Subjective questions**.

* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/learning/assessment/generate/`
* **Body**: Same as Step 8.
* **Validation**: Returns a fresh question paper with new question formulations.
