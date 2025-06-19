import time
import random
import re
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
                print(f"[WARN] ইমেইল তৈরি ব্যর্থ, আবার চেষ্টা করছে... ({reg.status_code})")
                continue

            token_resp = requests.post(f"{MAIL_TM_BASE}/token", json={"address": email, "password": password})
            token = token_resp.json().get("token")
            if not token:
                continue

            return email, password, token

        except Exception as e:
            print(f"[ERROR] টেম্প ইমেইল ত্রুটি: {e}")
            time.sleep(2)

    raise Exception("❌ টেম্প ইমেইল তৈরি হয়নি (৩ বার চেষ্টা করেও)।")

def get_verification_code(token):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(40):  # প্রায় ২ মিনিট পর্যন্ত চেক
        time.sleep(3)
        resp = requests.get(f"{MAIL_TM_BASE}/messages", headers=headers)
        messages = resp.json().get("hydra:member", [])
        for msg in messages:
            subject = msg.get("subject", "").lower()
            if "code" in subject or "verify" in subject or "sophon" in subject:
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
        print(f"[{idx}] 📧 টেম্প ইমেইল তৈরি: {email}")

        page.goto(INVITE_URL, wait_until="load")
        time.sleep(2)

        try:
            page.wait_for_selector("#email_field", timeout=30000)
            page.fill("#email_field", email)
        except:
            print(f"[{idx}] ⚠️ Warning: সরাসরি #email_field পাওয়া যায়নি, fallback চেষ্টা চলছে...")
            inputs = page.locator("input")
            for i in range(inputs.count()):
                try:
                    placeholder = inputs.nth(i).get_attribute("placeholder")
                    if placeholder and "email" in placeholder.lower():
                        inputs.nth(i).fill(email)
                        break
                except:
                    continue

        try:
            page.fill("input[type='text']", invite_code)
        except:
            print(f"[{idx}] ⚠️ Invite code ইনপুট খুঁজে পাওয়া যাচ্ছে না!")

        page.click("button")

        print(f"[{idx}] 📨 ইমেইল ও কোড সাবমিট হয়েছে। কোডের জন্য অপেক্ষা করছে...")

        code = get_verification_code(token)
        if not code:
            print(f"[{idx}] ❌ কোড পাওয়া যায়নি।")
            return

        print(f"[{idx}] ✅ কোড পাওয়া গেছে: {code}")

        page.goto(INVITE_URL, wait_until="load")
        time.sleep(2)

        try:
            page.wait_for_selector("#email_field", timeout=30000)
            page.fill("#email_field", email)
        except:
            inputs = page.locator("input")
            for i in range(inputs.count()):
                try:
                    ph = inputs.nth(i).get_attribute("placeholder")
                    if ph and "email" in ph.lower():
                        inputs.nth(i).fill(email)
                        break
                except:
                    continue

        page.fill("input[type='text']", invite_code)
        page.fill("input[type='number']", code)
        page.click("button")

        print(f"[{idx}] 🎉 সফলভাবে অ্যাকাউন্ট #{idx} তৈরি হয়েছে!")

    except Exception as e:
        print(f"[{idx}] ❌ ত্রুটি: {e}")
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
