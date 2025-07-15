from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
import os, time, random, string
from mailersend import NewApiClient

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token TTL and storage
token_store: dict[str, tuple[str, float]] = {}
TOKEN_TTL = 5 * 60  # 5 minutes

# Schemas
class RequestSchema(BaseModel):
    email: EmailStr

class VerifySchema(BaseModel):
    email: EmailStr
    token: str

# Token generator
def generate_token(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

# Send token
@app.post("/api/send-auth-token")
async def send_auth_token(req: RequestSchema):
    try:
        token = generate_token()
        token_store[req.email] = (token, time.time() + TOKEN_TTL)

        # Setup MailerSend client
        mailer = NewApiClient(api_key=os.getenv("mlsn.43d80840d49ecab1423ffa853a83061b24ea28a0e2dc78d2c3302da2e26c9bf1"))

        from_email = os.getenv("kierroce@gmail.com", "test-zkq340eyd8xgd796.mlsender.net")
        subject = "Your Verification Code"
        text = f"Your verification code is {token}. It expires in 5 minutes."
        html = f"<p>Your verification code is <strong>{token}</strong>. It expires in 5 minutes.</p>"

        mailer.send(
            from_email,
            [req.email],
            subject,
            html,
            text
        )

        return {"status": "sent"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Verify token
@app.post("/api/verify-auth-token")
async def verify_token(req: VerifySchema):
    data = token_store.get(req.email)
    if not data:
        raise HTTPException(status_code=400, detail="No token found")

    token, expiry = data
    if time.time() > expiry:
        token_store.pop(req.email, None)
        raise HTTPException(status_code=400, detail="Token expired")

    if req.token != token:
        raise HTTPException(status_code=400, detail="Invalid token")

    token_store.pop(req.email, None)
    return {"status": "verified"}
