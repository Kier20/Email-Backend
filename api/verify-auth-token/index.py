import time
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI()

token_store = {}
TOKEN_TTL = 5 * 60

class VerifySchema(BaseModel):
    email: EmailStr
    token: str

@app.post("/")
async def handler(req: Request):
    body = await req.json()
    data = VerifySchema(**body)

    record = token_store.get(data.email)
    if not record:
        raise HTTPException(status_code=400, detail="No token found")

    token, expires_at = record
    if time.time() > expires_at:
        token_store.pop(data.email, None)
        raise HTTPException(status_code=400, detail="Token expired")

    if data.token != token:
        raise HTTPException(status_code=400, detail="Invalid token")

    token_store.pop(data.email, None)
    return {"status": "verified"}
