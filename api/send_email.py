from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os, time, random, string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in prod
    allow_methods=["POST"],
    allow_headers=["*"],
)

# In-memory token storage
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
    try:
        token = generate_token()
        token_store[req.email] = (token, time.time() + TOKEN_TTL)

        message = Mail(
            from_email=os.getenv("SENDGRID_FROM"),
            to_emails=req.email,
            subject="Your Verification Code",
            html_content=f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>",
        )

        sg = SendGridAPIClient(os.getenv("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"))
        sg.send(message)

        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify-auth-token")
async def verify_token(req: VerifySchema):
    if req.email not in token_store:
        raise HTTPException(status_code=400, detail="No token found")

    token, expiry = token_store[req.email]
    if time.time() > expiry:
        del token_store[req.email]
        raise HTTPException(status_code=400, detail="Token expired")

    if req.token != token:
        raise HTTPException(status_code=400, detail="Invalid token")

    del token_store[req.email]
    return {"status": "verified"}
