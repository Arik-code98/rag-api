# RAG API — Retrieval-Augmented Generation with FastAPI

A RESTful API that brings RAG (Retrieval-Augmented Generation) capabilities to any text document. Upload a `.txt` file via the API, then ask questions against it — the system retrieves the most relevant passages using semantic search and generates a grounded answer using LLaMA 3.3 70B via the Groq API.

Each uploaded document gets its own isolated ChromaDB collection, identified by a unique collection ID, allowing multiple independent documents to coexist simultaneously. All endpoints are protected with JWT-based authentication.

---

## How It Works

```
POST /register + POST /login
      |
      returns JWT token
      |
      v
POST /upload (.txt file + token)
      |
      v
  Read & Decode file contents (UTF-8)
      |
      v
  Text Chunking  (split on \n\n)
      |
      v
Sentence Embeddings  <-- SentenceTransformer (all-MiniLM-L6-v2)
      |
      v
ChromaDB Collection  (keyed by UUID)
      |
      returns collection_id
      |
      v
POST /ask (collection_id + question + token)
      |
      v
Question Embedding  -->  Semantic Search  -->  Top-2 Chunks
                                                      |
                                                      v
                                          Prompt = Context + Question
                                                      |
                                                      v
                                       LLaMA 3.3 70B (Groq API)
                                                      |
                                                      v
                                            Grounded Answer
```

---

## Tech Stack

- **FastAPI** - Web framework for building the API
- **SentenceTransformers** - Local semantic embedding model (`all-MiniLM-L6-v2`)
- **ChromaDB** - In-memory vector database for storing and querying embeddings
- **Groq API** - LLM inference backend
- **LLaMA 3.3 70B Versatile** - The underlying large language model
- **Pydantic** - Request body validation
- **python-dotenv** - Secure API key management
- **SQLAlchemy** - ORM for user database management
- **JWT (JSON Web Tokens)** - Token-based authentication via `create_access_token`
- **Passlib / bcrypt** - Password hashing and verification
- **FastAPI Security** - OAuth2 password flow (`OAuth2PasswordBearer`)

---

## Project Structure

```
project/
├── main.py          # Main application file
├── auth.py          # JWT token creation and verification
├── database.py      # SQLAlchemy setup, User model, DB session
├── users.py         # Password hashing and verification helpers
├── users.db         # SQLite database (auto-created on first run)
├── .env             # Environment variables (not committed)
└── requirements.txt # Project dependencies
```

---

## Setup and Installation

**1. Clone the repository**

```bash
git clone https://github.com/Arik-code98/rag-api.git
cd rag-api
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment variables**

Create a `.env` file in the root directory:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key from [https://console.groq.com](https://console.groq.com).

**4. Run the server**

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

---

## API Endpoints

### GET /
Health check to confirm the API is running.

**Response**
```json
{
  "Message": "api is running"
}
```

---

### POST /register
Register a new user. Hashes the password and stores credentials in the SQLite database.

**Request Body**
```json
{
  "username": "john",
  "password": "secret123"
}
```

**Response**
```json
{
  "Message": "Registered successfully"
}
```

---

### POST /login
Authenticate and receive a JWT access token.

**Request Body** — `form-data` (OAuth2 standard)

| Field    | Type   |
|----------|--------|
| username | string |
| password | string |

**Response**
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

**Error (401)**
```json
{
  "detail": "Invalid credentials"
}
```

---

### POST /upload
Upload a `.txt` file. The contents are read, chunked, embedded, and stored in an isolated ChromaDB collection. Returns a `collection_id` for querying.

**Auth**: Requires a valid Bearer token in the `Authorization` header.

**Request** — `multipart/form-data`

| Field    | Type | Description                    |
|----------|------|--------------------------------|
| document | file | A `.txt` file encoded in UTF-8 |

**Response**
```json
{
  "collection_id": "a3f2c91e4b6d4e8f9c1d2a3b4c5d6e7f"
}
```

---

### POST /ask
Ask a question against a previously uploaded document. The system retrieves the 2 most relevant chunks and generates a grounded answer.

**Auth**: Requires a valid Bearer token in the `Authorization` header.

**Request Body**
```json
{
  "collection_id": "a3f2c91e4b6d4e8f9c1d2a3b4c5d6e7f",
  "question": "How is AI used in healthcare?"
}
```

**Response**
```json
{
  "answer": "Based on the document, AI is used in healthcare to..."
}
```

**Error (404)**
```json
{
  "detail": "doc not found"
}
```

---

## Example Workflow

**Step 1 — Register**
```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "secret123"}'
```

**Step 2 — Login and get token**
```bash
curl -X POST http://127.0.0.1:8000/login \
  -F "username=john" \
  -F "password=secret123"
```

**Step 3 — Upload a `.txt` file**
```bash
curl -X POST http://127.0.0.1:8000/upload \
  -H "Authorization: Bearer <your_token>" \
  -F "document=@my_document.txt"
```

**Step 4 — Ask a question**
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "<your_collection_id>", "question": "What is this document about?"}'
```

You can also test all endpoints interactively via Swagger UI at `http://127.0.0.1:8000/docs`.

---

## Key Concepts Explored

- REST API design with FastAPI and Pydantic
- JWT-based authentication with token creation and verification
- OAuth2 password flow using FastAPI Security
- Password hashing with bcrypt
- Protecting routes using FastAPI's `Depends` injection
- User registration and login with SQLAlchemy and SQLite
- Async file handling in FastAPI using `UploadFile` and `await`
- `multipart/form-data` file uploads
- Dynamic document ingestion and chunking via API
- Per-document vector collection management with ChromaDB
- Semantic search using sentence embeddings
- Context-aware prompt construction for grounded LLM responses
- UUID-based multi-document isolation
- HTTP exception handling with proper status codes

---

## Limitations and Improvements

- **In-memory storage**: ChromaDB runs in memory — all collections are lost on server restart. For persistence, use a file-based or hosted ChromaDB instance.
- **SQLite only**: User data is stored in a local SQLite file. For production, migrate to PostgreSQL or another production-grade database.
- **No token expiry handling on client**: Tokens expire server-side but the client receives no explicit warning — adding refresh token support would improve UX.
- **UTF-8 only**: The uploaded file is decoded assuming UTF-8 encoding. Adding encoding detection (e.g. `chardet`) would make this more robust.
- **No file validation**: There is no check on file type or size before processing. Adding MIME type validation and a size limit is recommended before deploying.
- **Plain text only**: Only `.txt` files are supported. Extending to PDF or DOCX would significantly broaden usability.
- **Fixed retrieval count**: The top-2 chunks are always retrieved. Making `n_results` configurable would allow better tuning per document size.
- **Basic chunking**: Splitting on `\n\n` works well for structured text but may miss context at chunk boundaries. A sliding window or token-based chunker would improve retrieval quality.