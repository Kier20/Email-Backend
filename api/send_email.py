import os, time, random, string
import smtplib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory token store
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
    return "".join(random.choices(string.digits, k=length))

# Send token endpoint
@app.post("/api/send-auth-token")
async def send_auth_token(req: RequestSchema):
    try:
        token = generate_token()
        token_store[req.email] = (token, time.time() + TOKEN_TTL)

        # Elastic Email SMTP config
        smtp_server = "smtp.elasticemail.com"
        smtp_port = 2525
        smtp_user = os.getenv("roca.ek.bscs@gmail.com")  # e.g., roca.ek.bscs@gmail.com
        smtp_password = os.getenv("B0E82A2EC01EE44F9D383FC659D063E47D2B")  # API key from Elastic Email

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = req.email
        msg["Subject"] = "Your Verification Code"

        html_body = f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>"
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, req.email, msg.as_string())

        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Verify token endpoint
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
import os, time, random, string
import smtplib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory token store
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
    return "".join(random.choices(string.digits, k=length))

# Send token endpoint
@app.post("/api/send-auth-token")
async def send_auth_token(req: RequestSchema):
    try:
        token = generate_token()
        token_store[req.email] = (token, time.time() + TOKEN_TTL)

        # Elastic Email SMTP config
        smtp_server = "smtp.elasticemail.com"
        smtp_port = 2525
        smtp_user = os.getenv("ELASTIC_EMAIL_FROM")  # e.g., roca.ek.bscs@gmail.com
        smtp_password = os.getenv("ELASTIC_EMAIL_API_KEY")  # API key from Elastic Email

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = req.email
        msg["Subject"] = "Your Verification Code"

        html_body = f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>"
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, req.email, msg.as_string())

        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Verify token endpoint
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
