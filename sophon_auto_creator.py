import time
import random
import re
import sys
import string
import requests
from playwright.sync_api import sync_playwright

MAIL_TM_BASE = "https://api.mail.tm"
INVITE_URL = "https://app.sophon.xyz/invite/"


def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def create_temp_email():
    for attempt in range(3):
        try:
            domains = requests.get(f"{MAIL_TM_BASE}/domains").json()["hydra:member"]
            domain = random.choice(domains)["domain"]
            user = f"user{random.randint(100000,999999)}"
            email = f"{user}@{domain}"
            password = "Password123!"

            reg = requests.post(f"{MAIL_TM_BASE}/accounts", json={"address": email, "password": password})
            if reg.status_code not in (200, 201):
                print(f"[WARN] Email registration failed, retrying... ({reg.status_code})")
                continue

            token_resp = requests.post(f"{MAIL_TM_BASE}/token", json={"address": email, "password": password})
            token = token_resp.json().get("token")
            if not token:
                continue

            return email, password, token

        except Exception as e:
            print(f"[ERROR] Temp mail error: {e}")
            time.sleep(2)

    raise Exception("❌ Failed to create temp mail account after 3 attempts.")


def get_verification_code(token):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(20):
        time.sleep(3)
        resp = requests.get(f"{MAIL_TM_BASE}/messages", headers=headers)
        messages = resp.json().get("hydra:member", [])
        for msg in messages:
            if "Sophon" in msg["subject"]:
                full = requests.get(f"{MAIL_TM_BASE}/messages/{msg['id']}", headers=headers).json()
                body = full.get("text", "")
                match = re.search(r"\b(\d{4,8})\b", body)
                if match:
                    return match.group(1)
    return None


def create_account(playwright, invite_code, idx):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    try:
        # Step 1: Create temp email
        email, password, token = create_temp_email()
        print(f"[{idx}] 📧 Temp email created: {email}")

        # Step 2: Go to invite page
        page.goto(INVITE_URL, wait_until="load")
        page.wait_for_selector("input", timeout=60000)

        # Fill invite form (adjust selectors here)
        page.fill("input[type='text']", invite_code)      # First text input
        page.fill("input[type='email']", email)           # Email input
        page.click("button")                              # Click first button (submit)
        print(f"[{idx}] Submitted invite form.")

        # Step 3: Get code from mail.tm
        code = get_verification_code(token)
        if not code:
            print(f"[{idx}] ❌ No verification code received.")
            return

        print(f"[{idx}] ✅ Verification code: {code}")

        # Step 4: Return and submit code
        page.goto(INVITE_URL, wait_until="load")
        page.fill("input[type='text']", invite_code)
        page.fill("input[type='email']", email)
        page.fill("input[type='number']", code)
        page.click("button")
        print(f"[{idx}] 🎉 Account #{idx} created!")

    except Exception as e:
        print(f"[{idx}] ❌ Error: {e}")

    finally:
        context.close()
        browser.close()


def main():
    if len(sys.argv) >= 3:
        invite_code = sys.argv[1]
        total = int(sys.argv[2])
    else:
        invite_code = input("Enter your Sophon invite code: ").strip()
        total = int(input("Enter number of accounts to create: "))

    with sync_playwright() as playwright:
        for i in range(1, total + 1):
            create_account(playwright, invite_code, i)
            time.sleep(random.uniform(4, 7))


if __name__ == "__main__":
    main()
