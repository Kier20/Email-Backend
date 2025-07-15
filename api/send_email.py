import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.post("/api/send-auth-token")
async def send_auth_token(req: RequestSchema):
    try:
        token = generate_token()
        token_store[req.email] = (token, time.time() + TOKEN_TTL)

        # Email setup
        smtp_server = "smtp.elasticemail.com"
        smtp_port = 2525
        smtp_user = os.getenv("roca.ek.bscs@gmail.com")
        smtp_password = os.getenv("B0E82A2EC01EE44F9D383FC659D063E47D2B")

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
