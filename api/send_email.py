from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os, time, random, string

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# In-memory token store
token_store: dict[str, tuple[str, float]] = {}
TOKEN_TTL = 5 * 60

class RequestSchema(BaseModel):
    email: EmailStr

class VerifySchema(BaseModel):
    email: EmailStr
    token: str

@app.get("/api/send-auth-token")
def send_auth_token_info():
    return {"detail": "This endpoint only supports POST requests."}

@app.post("/api/send-auth-token")
async def send_auth_token(req: RequestSchema):
    token = "".join(random.choices(string.digits, k=6))
    expires_at = time.time() + TOKEN_TTL
    token_store[req.email] = (token, expires_at)

    message = Mail(
        from_email=os.getenv("SENDGRID_FROM", "no-reply@admissionsystem.com"),
        to_emails=req.email,
        subject="Your Verification Code",
        html_content=f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>",
    )

    try:
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            raise Exception("Missing SENDGRID_API_KEY")

        sg = SendGridAPIClient(api_key)
        sg.send(message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SendGrid error: {str(e)}")

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

    token_store.pop(req.email, None)
    return {"status": "verified"}
