from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException
import uuid
from fastapi import UploadFile, File

load_dotenv()
api_key=os.getenv("GROQ_API_KEY")
client=Groq(api_key=api_key)

model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client=chromadb.Client()

class QuestionInput(BaseModel):
    collection_id: str
    question: str

app=FastAPI()

@app.get("/")
def root():
    return{'Message':"api is running"}

@app.post("/upload")
async def upload(document: UploadFile = File(...)):
    contents = await document.read()
    text = contents.decode("utf-8")
    chunks=text.split("\n\n")
    c_id=uuid.uuid4().hex

    embeddings=model.encode(chunks)

    collection=chroma_client.create_collection(name=c_id)
    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        ids=[f"chunk{i}" for i in range(len(chunks))]
    )
    return {"collection_id": c_id}

@app.post("/ask")
def chat(doc:QuestionInput):
    collection_id=doc.collection_id
    try:
        collection = chroma_client.get_collection(name=collection_id)
    except:
        raise HTTPException(status_code=404, detail="doc not found")
    question=doc.question
    question_embedding = model.encode([question]).tolist()
    results = collection.query(
        query_embeddings=question_embedding,
        n_results=2
    )
    context = "\n\n".join(results["documents"][0])

    prompt = f"""Answer the question based on the context below.

    Context:
    {context}

    Question:
    {question}"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )

    return{"answer":response.choices[0].message.content}