import os, time, random, string
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Caution in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory token store
token_store: dict[str, tuple[str, float]] = {}
TOKEN_TTL = 5 * 60  # 5 minutes

# Pydantic Schemas
class RequestSchema(BaseModel):
    email: EmailStr

class VerifySchema(BaseModel):
    email: EmailStr
    token: str

# Token generator
def generate_token(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

# Send email via MailerSend
@app.post("/api/send-auth-token")
async def send_auth_token(req: RequestSchema):
    try:
        token = generate_token()
        token_store[req.email] = (token, time.time() + TOKEN_TTL)

        api_key = os.getenv("mlsn.43d80840d49ecab1423ffa853a83061b24ea28a0e2dc78d2c3302da2e26c9bf1")
        from_email = os.getenv("kierroce@gmail.com", "test-zkq340eyd8xgd796.mlsender.net")
        subject = "Your Verification Code"
        body_html = f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>"

        response = requests.post(
            "https://api.mailersend.com/v1/email",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": {"email": from_email},
                "to": [{"email": req.email}],
                "subject": subject,
                "html": body_html
            }
        )

        if response.status_code not in [200, 202]:
            raise Exception(f"MailerSend error: {response.text}")

        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Verify token
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
