from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
import os, time, random, string, traceback
from mailersend import emails

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token TTL and in-memory storage
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

        # Print token for debugging
        print(f"Generated token for {req.email}: {token}")

        # Setup MailerSend client (read from ENV)
        api_key = os.getenv("mlsn.43d80840d49ecab1423ffa853a83061b24ea28a0e2dc78d2c3302da2e26c9bf1")
        from_email = os.getenv("kierroca@gmail.com", "no-reply@test-zkq340eyd8xgd796.mlsender.net")

        if not api_key or not from_email:
            raise ValueError("Missing MAILERSEND_API_KEY or MAILERSEND_FROM_EMAIL environment variable")

        mailer = emails.NewEmail(api_key)

        subject = "Your Verification Code"
        text = f"Your verification code is {token}. It expires in 5 minutes."
        html = f"<p>Your verification code is <strong>{token}</strong>. It expires in 5 minutes.</p>"

        response = mailer.send(
            from_email,
            [req.email],
            subject,
            html,
            text
        )

        print(f"MailerSend API response: {response}")

        return {"status": "sent"}

    except Exception as e:
        print("Error occurred in send_auth_token:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")

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
