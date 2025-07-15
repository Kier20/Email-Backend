from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
import os, time, random, string, requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Token storage
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

        # Prepare Elastic Email API request
        api_key = os.getenv("B0E82A2EC01EE44F9D383FC659D063E47D2B")
        sender_email = os.getenv("roca.ek.bscs@gmail.com")

        if not api_key or not sender_email:
            raise Exception("Missing ELASTICEMAIL_API_KEY or ELASTICEMAIL_SENDER env variable.")

        payload = {
            "apikey": api_key,
            "from": sender_email,
            "to": req.email,
            "subject": "Your Verification Code",
            "bodyHtml": f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>",
            "isTransactional": True
        }

        response = requests.post("https://api.elasticemail.com/v2/email/send", data=payload)
        if response.status_code != 200 or response.json().get("success") is not True:
            raise Exception(response.json().get("error", "Failed to send email"))

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
