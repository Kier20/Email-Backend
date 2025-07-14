import os
import time
import random
import string

from fastapi import FastAPI, Request
from pydantic import BaseModel, EmailStr
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = FastAPI()

token_store = {}
TOKEN_TTL = 5 * 60  # 5 minutes

class RequestSchema(BaseModel):
    email: EmailStr

def generate_token(length: int = 6):
    return ''.join(random.choices(string.digits, k=length))

@app.post("/")
async def handler(req: Request):
    body = await req.json()
    data = RequestSchema(**body)

    token = generate_token()
    expires_at = time.time() + TOKEN_TTL
    token_store[data.email] = (token, expires_at)

    message = Mail(
        from_email=os.getenv("SENDGRID_FROM", "no-reply@admissionsystem.com"),
        to_emails=data.email,
        subject="Your Verification Code",
        html_content=f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>",
    )

    try:
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        sg.send(message)
    except Exception as e:
        return {"error": str(e)}

    return {"status": "sent"}
