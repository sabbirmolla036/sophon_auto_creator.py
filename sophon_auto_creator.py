import time
import random
import re
import requests
import string
from playwright.sync_api import sync_playwright

INVITE_URL = "https://app.sophon.xyz/invite/"

def random_string(length=10):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

# getnada ডোমেইন গুলো
GETNADA_DOMAINS = [
    "getnada.com", "nada.email", "amail.club", "robot-mail.com", "cafemom.com",
    "tafmail.com", "dropjar.com", "easytrashmail.com"
]

def create_temp_email():
    user = random_string(10)
    domain = random.choice(GETNADA_DOMAINS)
    email = f"{user}@{domain}"
    return user, domain, email

def get_messages(email):
    url = f"https://getnada.com/api/v1/inboxes/{email}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        return data.get("msgs", [])
    except Exception as e:
        print(f"Error fetching messages for {email}: {e}")
        return []

def read_message(message_id):
    url = f"https://getnada.com/api/v1/messages/{message_id}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error reading message {message_id}: {e}")
        return None

def get_verification_code(email, wait_time=120):
    start = time.time()
    pattern = r"Enter the code below on the login screen to continue:\s*(\d{6})"
    while time.time() - start < wait_time:
        messages = get_messages(email)
        for msg in messages:
            msg_data = read_message(msg["uid"])
            if msg_data:
                body = msg_data.get("text", "") + " " + msg_data.get("html", "")
                print(f"[DEBUG] মেইল বডি:\n{body}\n{'-'*50}")
                match = re.search(pattern, body)
                if match:
                    return match.group(1)
        time.sleep(5)
    return None

def create_account(playwright, invite_code, idx):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    try:
        user, domain, email = create_temp_email()
        print(f"[{idx}] 📧 টেম্প ইমেইল তৈরি: {email}")

        page.goto(INVITE_URL, wait_until="load")
        time.sleep(2)

        try:
            page.fill("#email_field", email)
        except Exception:
            print(f"[{idx}] ⚠️ #email_field পাওয়া যায়নি, fallback চলছে...")
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
        except Exception:
            print(f"[{idx}] ⚠️ ইনভাইট কোড ইনপুট খুঁজে পাওয়া যায়নি!")

        page.click("button")

        print(f"[{idx}] 📨 ইমেইল ও কোড সাবমিট হয়েছে। কোডের জন্য অপেক্ষা করছে...")

        code = get_verification_code(email)
        if not code:
            print(f"[{idx}] ❌ কোড পাওয়া যায়নি।")
            return

        print(f"[{idx}] ✅ কোড পাওয়া গেছে: {code}")

        try:
            page.fill("input[type='number']", code)
            page.click("button")
        except Exception:
            print(f"[{idx}] ⚠️ ভেরিফিকেশন কোড ফিল্ড বা সাবমিট বোতাম পাওয়া যায়নি!")

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
