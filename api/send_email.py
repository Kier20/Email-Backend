from flask import Flask, request, jsonify
from mailersend import emails
import os, time, random, string

app = Flask(__name__)

# Token storage
token_store: dict[str, tuple[str, float]] = {}
TOKEN_TTL = 5 * 60  # 5 minutes

# Generate 6-digit token
def generate_token(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

# Send auth token
@app.route("/api/send-auth-token", methods=["POST"])
def send_auth_token():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return jsonify({"error": "Email required"}), 400

        token = generate_token()
        token_store[email] = (token, time.time() + TOKEN_TTL)

        # Load MailerSend credentials
        api_key = os.getenv("mlsn.43d80840d49ecab1423ffa853a83061b24ea28a0e2dc78d2c3302da2e26c9bf1")
        from_email = os.getenv("noreply@test-zkq340eyd8xgd796.mlsender.net")
        if not api_key or not from_email:
            raise ValueError("Missing MAILERSEND_API_KEY or MAILERSEND_FROM_EMAIL")

        # MailerSend client
        mailer = emails.NewEmail(api_key)
        subject = "Your Verification Code"
        text = f"Your code is {token}. It expires in 5 minutes."
        html = f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>"

        # Send
        mailer.send(from_email, [email], subject, html, text)
        return jsonify({"status": "sent"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Verify token
@app.route("/api/verify-auth-token", methods=["POST"])
def verify_auth_token():
    data = request.get_json()
    email = data.get("email")
    user_token = data.get("token")

    if email not in token_store:
        return jsonify({"error": "No token found"}), 400

    token, expiry = token_store[email]
    if time.time() > expiry:
        token_store.pop(email)
        return jsonify({"error": "Token expired"}), 400

    if token != user_token:
        return jsonify({"error": "Invalid token"}), 400

    token_store.pop(email)
    return jsonify({"status": "verified"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
