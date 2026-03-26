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
from database import SessionLocal, User, Base
from users import get_password_hash, verify_password
from auth import create_access_token, verify_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

load_dotenv()
api_key=os.getenv("GROQ_API_KEY")
client=Groq(api_key=api_key)

model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client=chromadb.Client()

class QuestionInput(BaseModel):
    collection_id: str
    question: str

class UserInput(BaseModel):
    username: str
    password: str

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return{'Message':"api is running"}

@app.post("/register")
def register_user(reg:UserInput):
    db=SessionLocal()
    hashed = get_password_hash(reg.password)
    user_store = User(username=reg.username, hashed_password=hashed)
    db.add(user_store)
    db.commit()
    db.close()
    return{"Message":"Registered successfully"}

@app.post("/login")
def user_login(log: OAuth2PasswordRequestForm = Depends()):
    db=SessionLocal()
    user=db.query(User).filter(User.username == log.username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    verification=verify_password(log.password,user.hashed_password)
    if verification is False:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token=create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/upload")
async def upload(document: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    verify_token(token)    
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
def chat(doc:QuestionInput, token: str = Depends(oauth2_scheme)):
    verify_token(token)    
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