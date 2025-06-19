import time
import random
import re
import sys
import requests
from playwright.sync_api import sync_playwright

INVITE_LINK = "https://app.sophon.xyz/invite/"
MAIL_TM_BASE = "https://api.mail.tm"


def create_temp_email():
    # Get domains available
    resp = requests.get(f"{MAIL_TM_BASE}/domains")
    resp.raise_for_status()
    domains = resp.json()["hydra:member"]
    domain = domains[0]["domain"]  # pick first domain

    # Create random user part
    user = f"user{random.randint(100000,999999)}"
    email = f"{user}@{domain}"
    password = "Password123!"

    # Register account on mail.tm
    data = {"address": email, "password": password}
    resp = requests.post(f"{MAIL_TM_BASE}/accounts", json=data)
    if resp.status_code not in (200, 201):
        raise Exception(f"Failed to create temp mail account: {resp.text}")

    # Get token for mail.tm API auth
    resp = requests.post(f"{MAIL_TM_BASE}/token", json={"address": email, "password": password})
    resp.raise_for_status()
    token = resp.json()["token"]

    return email, password, token


def get_latest_verification_code(token):
    headers = {"Authorization": f"Bearer {token}"}
    # Poll inbox for 60 seconds max
    for _ in range(20):
        resp = requests.get(f"{MAIL_TM_BASE}/messages", headers=headers)
        resp.raise_for_status()
        messages = resp.json()["hydra:member"]
        for msg in messages:
            if "Sophon" in msg["subject"] or "verification" in msg["subject"].lower():
                # Get full message
                msg_resp = requests.get(f"{MAIL_TM_BASE}/messages/{msg['id']}", headers=headers)
                msg_resp.raise_for_status()
                body = msg_resp.json()["text"]
                # Extract 4-8 digit code
                match = re.search(r"\b(\d{4,8})\b", body)
                if match:
                    return match.group(1)
        time.sleep(3)
    return None


def create_account(playwright, invite_code, idx):
    user_agent = (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{random.randint(90,114)}.0.{random.randint(1000,4000)}.0 Safari/537.36"
    )

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
        java_script_enabled=True,
        ignore_https_errors=True,
    )
    page = context.new_page()

    page.add_init_script(
        """() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
    }"""
    )

    try:
        # Step 1: Create temp mail
        email, password, token = create_temp_email()
        print(f"[{idx}] 📧 Temp email created: {email}")

        # Step 2: Go to Sophon invite page and fill form
        page.goto(INVITE_LINK, wait_until="networkidle")

        # Assuming these are the input field selectors - adjust if needed
        page.fill('input[name="inviteCode"]', invite_code)
        page.fill('input[name="email"]', email)
        page.click('button[type="submit"]')

        print(f"[{idx}] Submitted invite code and email. Waiting for verification email...")

        # Step 3: Poll mail.tm inbox for verification code
        verification_code = get_latest_verification_code(token)
        if not verification_code:
            print(f"[{idx}] ❌ Verification code not received. Skipping account.")
            return

        print(f"[{idx}] Verification code received: {verification_code}")

        # Step 4: Submit verification code to sophon.xyz
        page.goto(INVITE_LINK, wait_until="networkidle")

        page.fill('input[name="inviteCode"]', invite_code)
        page.fill('input[name="email"]', email)
        page.fill('input[name="verificationCode"]', verification_code)
        page.click('button[type="verify"]')

        print(f"[{idx}] ✅ Account #{idx} created successfully!")

    except Exception as e:
        print(f"[{idx}] ❌ Error: {e}")

    finally:
        context.close()
        browser.close()


def main():
    if len(sys.argv) > 2:
        invite_code = sys.argv[1]
        try:
            total_accounts = int(sys.argv[2])
        except ValueError:
            print("Invalid number of accounts. Usage: python script.py <invite_code> <number_of_accounts>")
            return
    else:
        invite_code = input("Enter your Sophon invite code: ").strip()
        total_accounts = int(input("Enter number of accounts to create: "))

    with sync_playwright() as playwright:
        for i in range(1, total_accounts + 1):
            try:
                create_account(playwright, invite_code, i)
            except Exception as e:
                print(f"[{i}] ❌ Error during account creation: {e}")
            time.sleep(random.uniform(5, 8))


if __name__ == "__main__":
    main()
