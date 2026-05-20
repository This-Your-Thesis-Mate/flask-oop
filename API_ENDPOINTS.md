# API Endpoints

## 1. Upload File

POST /uploads

```
Form Data:
- file: (binary PDF file)
- course_id: 1
- course_name: "Algoritma dan Struktur Data"
- module_id: 101
- tenant_id: 5
```

**cURL:**
```bash
curl -X POST http://localhost:5000/uploads \
  -F "file=@algoritma_dasar.pdf" \
  -F "course_id=1" \
  -F "course_name=Algoritma dan Struktur Data" \
  -F "module_id=101" \
  -F "tenant_id=5"
```

---

## 2. RAG Chat

POST /chat

```json
{
  "prompt": "Jelaskan tentang algoritma dasar",
  "course_id": 1,
  "tenant_id": 5,
  "threshold": 0.4,
  "limit": 5
}
```

**Minimal:**
```json
{
  "prompt": "Jelaskan tentang algoritma dasar",
  "course_id": 1,
  "tenant_id": 5
}
```

**With History:**
```json
{
  "prompt": "Jelaskan lebih detail",
  "course_id": 1,
  "tenant_id": 5,
  "messages": [
    {
      "role": "user",
      "content": "Jelaskan tentang algoritma dasar"
    },
    {
      "role": "assistant",
      "content": "Algoritma dasar adalah serangkaian instruksi..."
    }
  ]
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Jelaskan tentang algoritma dasar",
    "course_id": 1,
    "tenant_id": 5,
    "threshold": 0.4,
    "limit": 5
  }'
```

---

## 3. Generate Quiz

POST /quiz

```json
{
  "query": "Algoritma Dasar",
  "course_id": 1,
  "module_id": 101,
  "tenant_id": 5,
  "question_type": "multiple_choice",
  "number_of_question": "5"
}
```

**Multiple Types:**
```json
{
  "query": "Struktur Data",
  "course_id": 1,
  "module_id": 101,
  "tenant_id": 5,
  "question_type": "multiple_choice, short_answer, essay",
  "number_of_question": "5, 3, 2"
}
```

**Advanced:**
```json
{
  "query": "Algoritma Dasar",
  "course_id": 1,
  "module_id": 101,
  "tenant_id": 5,
  "question_type": "multiple_choice, true_false",
  "number_of_question": "5, 3",
  "threshold": 0.5,
  "limit": 10
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Algoritma Dasar",
    "course_id": 1,
    "module_id": 101,
    "tenant_id": 5,
    "question_type": "multiple_choice",
    "number_of_question": "5"
  }'
```

---

## 4. Generate Annotations

POST /generate-annotations

```json
{
  "course_id": 1,
  "module_id": 101,
  "tenant_id": 5
}
```

**Form Data (Alternative):**
```
course_id=1&module_id=101&tenant_id=5
```

**cURL (JSON):**
```bash
curl -X POST http://localhost:5000/generate-annotations \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "module_id": 101,
    "tenant_id": 5
  }'
```

**cURL (Form Data):**
```bash
curl -X POST http://localhost:5000/generate-annotations \
  -d "course_id=1&module_id=101&tenant_id=5"
```

---

## 5. Get Annotations

GET /get-annotations

```
Query Parameters:
- course_id: 1
- module_id: 101
- tenant_id: 5
```

**Full URL:**
```
http://localhost:5000/get-annotations?course_id=1&module_id=101&tenant_id=5
```

**cURL:**
```bash
curl -X GET "http://localhost:5000/get-annotations?course_id=1&module_id=101&tenant_id=5"
```

---

## 6. Get Annotations List

GET /get-annotations-list

```
Query Parameters:
- course_id: 1 (optional)
- tenant_id: 5 (required)
```

**Full URL (All):**
```
http://localhost:5000/get-annotations-list?tenant_id=5
```

**Full URL (By Course):**
```
http://localhost:5000/get-annotations-list?course_id=1&tenant_id=5
```

**cURL (All):**
```bash
curl -X GET "http://localhost:5000/get-annotations-list?tenant_id=5"
```

**cURL (By Course):**
```bash
curl -X GET "http://localhost:5000/get-annotations-list?course_id=1&tenant_id=5"
```

---

## Notes

- Base URL: `http://localhost:5000`
- Always include `tenant_id` in requests
- `course_id` is required for: uploads, chat, quiz, generate-annotations, get-annotations
- `module_id` required for: quiz, generate-annotations, get-annotations
- Optional params: `threshold`, `limit` (for chat & quiz)
- GET endpoints use query parameters, not JSON body
