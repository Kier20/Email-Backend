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
    try:
        print("Generating token...")
        token = generate_token()
        expires_at = time.time() + TOKEN_TTL
        token_store[req.email] = (token, expires_at)

        message = Mail(
            from_email=os.getenv("SENDGRID_FROM", "no-reply@admissionsystem.com"),
            to_emails=req.email,
            subject="Your Verification Code",
            html_content=f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>",
        )

        print("Sending email to:", req.email)
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)

        print("Email sent!")
        return {"status": "sent"}

    except Exception as e:
        print("Error sending email:", e)
        raise HTTPException(status_code=500, detail=str(e))
