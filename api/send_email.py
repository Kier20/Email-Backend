from flask import Flask, request, jsonify
from mailersend import emails
import os, time, random, string, traceback

app = Flask(__name__)

token_store: dict[str, tuple[str, float]] = {}
TOKEN_TTL = 5 * 60  # 5 minutes

def generate_token(length=6):
    return ''.join(random.choices(string.digits, k=length))

@app.route("/api/send-auth-token", methods=["POST"])
def send_auth_token():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            return jsonify({"error": "Email required"}), 400

        token = generate_token()
        token_store[email] = (token, time.time() + TOKEN_TTL)

        api_key = os.getenv("Api_Key")
        from_email = os.getenv("Verified_Email")

        if not api_key or not from_email:
            raise ValueError("Missing MAILERSEND_API_KEY or MAILERSEND_FROM_EMAIL")

        mailer = emails.NewEmail(api_key)
        subject = "Your Verification Code"
        text = f"Your code is {token}. It expires in 5 minutes."
        html = f"<p>Your code is <strong>{token}</strong>. It expires in 5 minutes.</p>"

        response = mailer.send(
            from_email,
            [email],
            subject,
            html,
            text
        )

        print("MailerSend response:", response)
        return jsonify({"status": "sent"})

    except Exception as e:
        print("Error occurred in send_auth_token:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
