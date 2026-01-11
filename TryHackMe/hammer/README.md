# 🔨 Hammer - TryHackMe Write-up

## 📌 Challenge Info
- **Platform:** TryHackMe
- **Name:** Hammer
- **Difficulty:** Medium
- **Category:** Web Exploitation / Logic Flaw

## 📝 Reconnaissance & Analysis
The challenge starts with a login page requiring an email. After inputting a valid email, it asks for a 4-digit recovery code.
- **Vulnerability Found:** The rate limit (max 8 attempts) is tied to the `PHPSESSID` cookie, not the user's email or IP.
- **Exploitation Strategy:** We can bypass the rate limit by generating a new session cookie every time the counter nears the limit, allowing for infinite brute-force attempts.

## 💥 Exploitation
### 1. Rate Limit Bypass (OTP)
I developed a multi-threaded Python script to brute-force the 4-digit code. The script monitors the `Rate-Limit-Pending` header and rotates the session cookie automatically to reset the counter.

**Script:** [brute_v2.py](./scripts/brute_v2.py)

### 2. Authentication Bypass & Command Injection
After logging in, the dashboard executes commands via a hidden input. The authorization relies on a JWT token with a vulnerability in the `kid` (Key ID) header.
- **Vulnerability:** Path Traversal in JWT `kid` parameter.
- **Exploit:** I pointed the `kid` header to a known static file on the server (`hmr_css/bootstrap.min.css`) and signed a forged admin token using the content of that CSS file as the secret key.

**Script:** [forge_jwt_css.py](./scripts/forge_jwt_css.py)

## 🛡️ Mitigation (Blue Team)
To fix these vulnerabilities:
1.  **Rate Limit:** Associate the attempt counter with the `user_id` or `email` in a backend store (e.g., Redis), not the session cookie.
2.  **JWT Validation:** Implement a whitelist of allowed `kid` values or strictly validate the file path to prevent directory traversal. Ensure the signing key is never user-controllable.
