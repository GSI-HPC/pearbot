import os
import jwt
import time
import requests
import hmac
import hashlib

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")
GITHUB_APP_WEBHOOK_SECRET = os.getenv("GITHUB_APP_WEBHOOK_SECRET")

if not all([GITHUB_APP_ID, GITHUB_PRIVATE_KEY, GITHUB_APP_WEBHOOK_SECRET]):
    raise EnvironmentError("Missing required environment variables. Please check your .env file.")

GITHUB_PRIVATE_KEY = GITHUB_PRIVATE_KEY.replace('\\n', '\n') if GITHUB_PRIVATE_KEY else None

def verify_webhook_signature(request):
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        return False

    sha_name, signature = signature.split('=')
    if sha_name != 'sha256':
        return False

    secret = GITHUB_APP_WEBHOOK_SECRET.encode()
    mac = hmac.new(secret, msg=request.data, digestmod=hashlib.sha256)

    return hmac.compare_digest(mac.hexdigest(), signature)

def create_jwt():
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + (10 * 60),  # JWT expires in 10 minutes
        "iss": GITHUB_APP_ID
    }
    return jwt.encode(payload, GITHUB_PRIVATE_KEY, algorithm="RS256")

def get_installation_access_token(installation_id):
    jwt_token = create_jwt()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers=headers
    )
    return response.json()["token"]
