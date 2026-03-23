from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password:str):
    if len(password) > 72:
        raise HTTPException(status_code=400, detail="Password too long, max 72 characters")
    hashed_password=pwd_context.hash(password)
    return hashed_password

def verify_password(password: str, hashed_password: str):
    confirmation=pwd_context.verify(password, hashed_password)
    return confirmation