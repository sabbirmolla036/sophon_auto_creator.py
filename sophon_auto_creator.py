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
                print(f"[WARN] ইমেইল তৈরি করতে সমস্যা হচ্ছে, আবার চেষ্টা করছে... ({reg.status_code})")
                continue

            token_resp = requests.post(f"{MAIL_TM_BASE}/token", json={"address": email, "password": password})
            token = token_resp.json().get("token")
            if not token:
                continue

            return email, password, token

        except Exception as e:
            print(f"[ERROR] টেম্প ইমেইল তৈরিতে সমস্যা: {e}")
            time.sleep(2)

    raise Exception("❌ ৩ বার চেষ্টা করেও টেম্প ইমেইল তৈরি হয়নি।")


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
        email, password, token = create_temp_email()
        print(f"[{idx}] 📧 টেম্প ইমেইল তৈরি হয়েছে: {email}")

        # Go to Sophon invite page
        page.goto(INVITE_URL, wait_until="load")
        page.wait_for_selector("#email_field", timeout=60000)

        # Fill in email and invite code
        page.fill("#email_field", email)
        page.fill("input[type='text']", invite_code)
        page.click("button")

        print(f"[{idx}] 📨 ইমেইল ও ইনভাইট কোড সাবমিট হয়েছে। কোডের জন্য অপেক্ষা করছে...")

        # Wait for code from email
        code = get_verification_code(token)
        if not code:
            print(f"[{idx}] ❌ ভেরিফিকেশন কোড পাওয়া যায়নি।")
            return

        print(f"[{idx}] ✅ কোড পাওয়া গেছে: {code}")

        # Go back and submit verification code
        page.goto(INVITE_URL, wait_until="load")
        page.fill("#email_field", email)
        page.fill("input[type='text']", invite_code)
        page.fill("input[type='number']", code)
        page.click("button")

        print(f"[{idx}] 🎉 অ্যাকাউন্ট #{idx} সফলভাবে তৈরি হয়েছে!")

    except Exception as e:
        print(f"[{idx}] ❌ সমস্যা: {e}")

    finally:
        context.close()
        browser.close()


def main():
    invite_code = input("🔑 আপনার Sophon ইনভাইট কোড দিন: ").strip()
    total = int(input("🔢 কয়টা অ্যাকাউন্ট বানাতে চান?: "))

    with sync_playwright() as playwright:
        for i in range(1, total + 1):
            create_account(playwright, invite_code, i)
            time.sleep(random.uniform(5, 8))


if __name__ == "__main__":
    main()
