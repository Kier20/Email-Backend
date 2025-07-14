import os
import time
import random
import string

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# send_email.py
from fastapi import Request
import json

def handler(request: Request):
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Vercel doesn't support FastAPI directly"})
    }

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["POST"],
    allow_headers=["*"],
)

# In-memory token storage: { email: (token, expiration_timestamp) }
token_store: dict[str, tuple[str, float]] = {}

TOKEN_TTL = 5 * 60  # 5 minutes

class RequestSchema(BaseModel):
    email: EmailStr

class VerifySchema(BaseModel):
    email: EmailStr
    token: str

def generate_token(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

@app.post("/api/send-auth-token")
async def send_auth_token(req: RequestSchema):
    token = generate_token()
    expires_at = time.time() + TOKEN_TTL
    token_store[req.email] = (token, expires_at)

    message = Mail(
        from_email=os.getenv("SENDGRID_FROM", "no-reply@admissionsystem.com"),
        to_emails=req.email,
        subject="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",
        html=f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>",
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "sent"}

@app.post("/api/verify-auth-token")
async def verify_auth_token(req: VerifySchema):
    data = token_store.get(req.email)
    if not data:
        raise HTTPException(status_code=400, detail="No token found")
    token, expires_at = data
    if time.time() > expires_at:
        token_store.pop(req.email, None)
        raise HTTPException(status_code=400, detail="Token expired")
    if req.token != token:
        raise HTTPException(status_code=400, detail="Invalid token")

    # Success – remove token so it cannot be reused
    token_store.pop(req.email, None)
    return {"status": "verified"}
