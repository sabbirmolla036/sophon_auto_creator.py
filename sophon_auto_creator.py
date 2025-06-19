import time
import random
import re
import requests
import string
from playwright.sync_api import sync_playwright

INVITE_URL = "https://app.sophon.xyz/invite/"

GETNADA_DOMAINS = [
    "getnada.com", "nada.email", "amail.club", "robot-mail.com",
    "tafmail.com", "dropjar.com", "easytrashmail.com"
]

def random_string(length=10):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def create_temp_email():
    user = random_string(10)
    domain = random.choice(GETNADA_DOMAINS)
    email = f"{user}@{domain}"
    return user, domain, email

def get_messages(username):
    url = f"https://getnada.com/api/v1/inboxes/{username}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("msgs", [])
    except Exception as e:
        print(f"Error fetching messages for {username}: {e}")
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

def get_verification_code(username, wait_time=120):
    start = time.time()
    pattern = r"Enter the code below on the login screen to continue:\s*(\d{6})"
    while time.time() - start < wait_time:
        msgs = get_messages(username)
        for m in msgs:
            md = read_message(m["uid"])
            if not md:
                continue
            body = md.get("text", "") + " " + md.get("html", "")
            print(f"[DEBUG] মেইল:\n{body}\n{'-'*50}")
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
        print(f"[{idx}] 📧 টেম্প ইমেইল: {email}")

        page.goto(INVITE_URL, wait_until="load")
        time.sleep(2)

        # ইমেইল ইনপুট
        filled = False
        try:
            page.fill("#email_field", email)
            filled = True
        except:
            inputs = page.locator("input")
            for i in range(inputs.count()):
                ph = inputs.nth(i).get_attribute("placeholder") or ""
                if "email" in ph.lower():
                    inputs.nth(i).fill(email)
                    filled = True
                    break
        if not filled:
            print(f"[{idx}] ⚠️ ইমেইল ইনপুট খুঁজে পাওয়া যায়নি!")

        # ইনভাইট কোড
        try:
            page.fill("input[type='text']", invite_code)
        except:
            print(f"[{idx}] ⚠️ ইনভাইট কোড ফিল করতে সমস্যা!")

        page.click("button")
        print(f"[{idx}] 📨 ইনভাইট ও মেইল সাবমিট, কোড অপেক্ষা করছে...")

        code = get_verification_code(user)
        if not code:
            print(f"[{idx}] ❌ কোড পাওয়া যায়নি।")
            return
        print(f"[{idx}] ✅ কোড পাওয়া গেছে: {code}")

        # অটোমেটিক কোড এন্ট্রি ও সাবমিশন
        try:
            page.fill("input[type='number']", code)
            time.sleep(1)
            page.click("button")
            print(f"[{idx}] 🎉 অ্যাকাউন্ট #{idx} তৈরি হয়েছে!")
        except Exception as e:
            print(f"[{idx}] ⚠️ কোড সাবমিটে সমস্যা: {e}")

    except Exception as err:
        print(f"[{idx}] ❌ এরর: {err}")
    finally:
        context.close()
        browser.close()

def main():
    invite = input("🔑 Sophon ইনভাইট কোড দিন: ").strip()
    num = int(input("🔢 কতগুলো অ্যাকাউন্ট বানাবেন?: "))

    with sync_playwright() as pw:
        for i in range(1, num + 1):
            create_account(pw, invite, i)
            time.sleep(random.uniform(5, 8))

if __name__ == "__main__":
    main()
