import json
import os
import time
import random
import string

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

TOKEN_TTL = 5 * 60  # 5 minutes
token_store = {}

def generate_token(length=6):
    return ''.join(random.choices(string.digits, k=length))

def handler(request):
    if request.method == "POST":
        try:
            body = request.json()

            if request.path == "/api/send-auth-token":
                email = body["email"]
                token = generate_token()
                expires_at = time.time() + TOKEN_TTL
                token_store[email] = (token, expires_at)

                message = Mail(
                    from_email=os.getenv("SENDGRID_FROM", "no-reply@admissionsystem.com"),
                    to_emails=email,
                    subject="Your Authentication Code",
                    html_content=f"<p>Your token is <strong>{token}</strong>. Expires in 5 minutes.</p>",
                )

                sg = SendGridAPIClient(os.getenv("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"))
                sg.send(message)

                return {
                    "statusCode": 200,
                    "body": json.dumps({"status": "sent"})
                }

            elif request.path == "/api/verify-auth-token":
                email = body["email"]
                token = body["token"]
                stored = token_store.get(email)

                if not stored:
                    return {"statusCode": 400, "body": json.dumps({"error": "No token found"})}

                stored_token, expires_at = stored
                if time.time() > expires_at:
                    return {"statusCode": 400, "body": json.dumps({"error": "Token expired"})}

                if stored_token != token:
                    return {"statusCode": 400, "body": json.dumps({"error": "Invalid token"})}

                return {"statusCode": 200, "body": json.dumps({"status": "verified"})}

        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    return {"statusCode": 405, "body": json.dumps({"error": "Method not allowed"})}
