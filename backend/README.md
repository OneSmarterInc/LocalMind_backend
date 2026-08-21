# LocalMind Backend — Phase 1

## What this version does

This backend intentionally stops at the **outline verification stage**:

1. Accept PDF, DOCX, or legacy DOC.
2. Extract structured document content with Docling.
3. Detect headings.
4. Ask local Ollama (`qwen3:4b`) to group the detected structure into:
   - learning modules
   - chapters
5. If Ollama is unavailable, use a deterministic fallback outline.
6. Return the proposed outline through the REST API.
7. Let the student replace/edit the outline.
8. Let the student confirm the final outline.

It does **not** contain tutoring, embeddings, ChromaDB, RAG, quizzes, or frontend code.

---

## Manual setup

### 1. Create and activate a virtual environment

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Ollama

Make sure Ollama is installed and running locally.

Pull the outline model:

```powershell
ollama pull qwen3:4b
```

The backend uses:

```text
http://127.0.0.1:11434
```

If Ollama is unavailable, upload still works using the built-in fallback outline generator.

### 4. Legacy `.doc` note

PDF and DOCX are handled directly by Docling.

For old `.doc` files, Docling requires **LibreOffice** to be installed so the legacy Word format can be converted.

### 5. Create the SQLite database

```powershell
python manage.py migrate
```

### 6. Run tests

```powershell
python manage.py test
```

### 7. Start the backend

```powershell
python manage.py runserver
```

Health check:

```text
GET http://127.0.0.1:8000/api/health/
```

---

# API flow

## 1. Upload document

```text
POST /api/documents/upload/
Content-Type: multipart/form-data
field name: file
```

Example response:

```json
{
  "id": "document-uuid",
  "title": "Computer Networks",
  "original_name": "computer_networks.pdf",
  "file_type": "pdf",
  "status": "awaiting_review",
  "outline_source": "ollama",
  "modules": [
    {
      "id": "module-uuid",
      "title": "Networking Foundations",
      "order": 1,
      "is_user_edited": false,
      "chapters": [
        {
          "id": "chapter-uuid",
          "title": "Introduction to Networks",
          "order": 1,
          "is_user_edited": false
        }
      ]
    }
  ]
}
```

The student should now review this structure.

---

## 2. Read proposed outline

```text
GET /api/documents/{document_id}/outline/
```

---

## 3. Student changes the outline

```text
PUT /api/documents/{document_id}/outline/
Content-Type: application/json
```

Example:

```json
{
  "document_title": "Computer Networks",
  "modules": [
    {
      "title": "Module 1 - Basics",
      "chapters": [
        {"title": "Introduction"},
        {"title": "Network Models"}
      ]
    },
    {
      "title": "Module 2 - Networking",
      "chapters": [
        {"title": "IP Addressing"},
        {"title": "Routing"}
      ]
    }
  ]
}
```

The backend deletes the proposed outline and saves this student-approved structure.

---

## 4. Student confirms the outline

```text
POST /api/documents/{document_id}/outline/confirm/
```

After confirmation:

```json
{
  "status": "confirmed"
}
```

**This confirmed outline is the exact point where the next LocalMind phase — tutoring — should begin.**

---

## Current architecture

```text
PDF / DOCX / DOC
        |
        v
Django REST API
        |
        v
Docling
        |
        v
Detected headings
        |
        +--------------------+
        |                    |
        v                    v
     Ollama              Fallback
    qwen3:4b             heuristic
        |                    |
        +---------+----------+
                  |
                  v
          Proposed Outline
                  |
                  v
              SQLite
                  |
                  v
          Student Review
            /        \
         Edit       Confirm
          |            |
          +------------+
                  |
                  v
        Ready for Tutoring
```
