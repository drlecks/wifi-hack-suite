import asyncio
import aiohttp
import random
from bs4 import BeautifulSoup

# === CONFIGURATION ===
PORTAL_TEST_URL = "http://example.com"  # Change this to the actual portal URL
FLOOD_COUNT = 10  # Number of form submissions (default: 10)

# === Realistic and Absurd User Agents ===
USER_AGENTS = [
    lambda: f"Mozilla/5.0 (Linux; Android {random.randint(7,13)}; SM-A{random.randint(100,999)}F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(80,120)}.0.{random.randint(1000,5000)}.120 Mobile Safari/537.36",
    lambda: f"Mozilla/5.0 (Windows NT {random.choice(['10.0', '11.0'])}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,120)}.0.{random.randint(1000,4000)}.100 Safari/537.36",
    lambda: f"Mozilla/5.0 (SmartFridge; Linux {random.randint(3,5)}.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(50,90)}.0.3987.132 Safari/537.36",
    lambda: f"Mozilla/5.0 (ToasterOS 1.0; en-US) AppleWebKit/{random.randint(530,540)}.7 Chrome/9.0 Safari/534.7",
    lambda: f"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:{random.randint(60,110)}) Gecko/20100101 Firefox/{random.randint(60,110)}.0",
    lambda: f"curl/7.{random.randint(20,90)}.{random.randint(0,10)}",
    lambda: f"Wget/1.{random.randint(10,21)}.{random.randint(1,5)}"
]

async def fetch_html(session, url):
    async with session.get(url) as resp:
        if 'text/html' not in resp.headers.get("Content-Type", ""):
            print("[x] Not a captive portal (HTML not found).")
            return None
        return await resp.text(), str(resp.url)

def parse_form(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    if not form:
        return None, None, None
    action = form.get("action") or base_url
    if not action.startswith("http"):
        if action.startswith("/"):
            action = base_url.rstrip("/") + action
        else:
            action = base_url.rstrip("/") + "/" + action
    method = form.get("method", "post").lower()
    fields = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if name:
            if "user" in name.lower():
                fields[name] = "test"
            elif "pass" in name.lower():
                fields[name] = "123"
            else:
                fields[name] = "dummy"
    return action, method, fields

def generate_fields(fields):
    user = random.choice(["admin", "user", "hacker", "root"]) + str(random.randint(1, 999))
    password = random.choice(["123456", "password", "letmein", "qwerty"])
    new_fields = {}
    for k in fields:
        if "user" in k.lower():
            new_fields[k] = user
        elif "pass" in k.lower():
            new_fields[k] = password
        else:
            new_fields[k] = "filler" + str(random.randint(100,999))
    return new_fields

async def flood(session, action, method, fields, i):
    payload = generate_fields(fields)
    headers = {
        "User-Agent": random.choice(USER_AGENTS)()
    }
    try:
        if method == "post":
            async with session.post(action, data=payload, headers=headers) as resp:
                print(f"[{i}] {resp.status} -> {headers['User-Agent'][:35]}...")
        else:
            async with session.get(action, params=payload, headers=headers) as resp:
                print(f"[{i}] {resp.status} -> {headers['User-Agent'][:35]}...")
    except Exception as e:
        print(f"[{i}] Error: {e}")

async def main():
    print("=== Captive Phish Jammer v3.0 (Asyncio) ===")
    async with aiohttp.ClientSession() as session:
        html, url = await fetch_html(session, PORTAL_TEST_URL)
        if not html:
            return

        # Optional: Heuristic detection of suspicious portals
        if any(kw in html.lower() for kw in ["pineapple", "flipper", "reaver", "portal"]):
            print("[!] Suspicious captive portal detected! Might be a Pineapple or Flipper attack.")

        action, method, fields = parse_form(html, url)
        if not action:
            print("[-] No form found on the portal.")
            return

        print(f"[✓] Target parsed: {action} ({method.upper()})")
        tasks = [flood(session, action, method, fields, i) for i in range(FLOOD_COUNT)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
