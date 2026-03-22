# RAG API — Retrieval-Augmented Generation with FastAPI

A RESTful API that brings RAG (Retrieval-Augmented Generation) capabilities to any text document. Upload a document via the API, then ask questions against it — the system retrieves the most relevant passages using semantic search and generates a grounded answer using LLaMA 3.3 70B via the Groq API.

Each uploaded document gets its own isolated ChromaDB collection, identified by a unique collection ID, allowing multiple independent documents to coexist simultaneously.

---

## How It Works

```
POST /upload (.txt file)
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
POST /ask (collection_id + question)
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

---

## Project Structure

```
project/
├── main.py          # Main application file
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

### POST /upload
Upload a plain text document. The text is chunked, embedded, and stored in an isolated ChromaDB collection. Returns a `collection_id` to be used for querying.

**Request Body**
```json
{
  "text": "Artificial intelligence is transforming healthcare...\n\nMachine learning models can detect..."
}
```

**Response**
```json
{
  "collection_id": "a3f2c91e4b6d4e8f9c1d2a3b4c5d6e7f"
}
```

---

### POST /ask
Ask a question against a previously uploaded document. The system retrieves the 2 most relevant chunks and generates a grounded answer.

**Request** — `multipart/form-data`
```

| Field    | Type | Description                     |
|----------|------|---------------------------------|
| document | file | A `.txt` file encoded in UTF-8  |
```

**Response**
```json
{
  "answer": "Based on the document, AI is used in healthcare to..."
}
```

**Error (404) — collection not found**
```json
{
  "detail": "doc not found"
}
```

---

## Example Workflow

**Step 1 — Upload a document**
```bash
curl -X POST http://127.0.0.1:8000/upload \
  -F "document=@my_document.txt"
```

---

**3. Add one bullet under Key Concepts Explored:**
```
- Async file handling in FastAPI using `UploadFile` and `await`
- `multipart/form-data` file uploads vs JSON body requests
```

---

**4. Add one bullet under Limitations:**
```
- **UTF-8 only**: The file is decoded assuming UTF-8 encoding. Adding encoding detection (e.g. `chardet`) would make this more robust.
- **No file validation**: There is no check on file type or size. Adding MIME type validation and a size limit is recommended before deploying.
```

**Step 2 — Use the returned collection_id to ask a question**
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "<your_collection_id>", "question": "How does AI help doctors?"}'
```

---

## Key Concepts Explored

- REST API design with FastAPI and Pydantic
- Dynamic document ingestion and chunking via API
- Per-document vector collection management with ChromaDB
- Semantic search using sentence embeddings
- Context-aware prompt construction for grounded LLM responses
- UUID-based multi-document isolation
- HTTP exception handling with proper status codes

---

## Limitations and Improvements

- **In-memory storage**: ChromaDB runs in memory — all collections are lost on server restart. For persistence, use a file-based or hosted ChromaDB instance.
- **Plain text only**: The `/upload` endpoint currently accepts raw text. Extending it to accept PDF or DOCX uploads would make it more practical.
- **Fixed retrieval count**: The top-2 chunks are always retrieved. Making `n_results` a configurable parameter would allow better tuning per document size.
- **No authentication**: Endpoints are currently public. For production, add API key or JWT-based auth to protect both upload and query routes.
- **Basic chunking**: Splitting on `\n\n` works well for structured text but may miss context at chunk boundaries. A sliding window or token-based chunker would improve retrieval quality.