import time
import random
import re
import requests
from playwright.sync_api import sync_playwright

INVITE_URL = "https://app.sophon.xyz/invite/"

def random_string(length=10):
    import string
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def create_temp_email():
    user = random_string(10)
    domain = "1secmail.com"
    email = f"{user}@{domain}"
    return user, domain, email

def get_messages(user, domain):
    url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={user}&domain={domain}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except:
        return []

def read_message(user, domain, message_id):
    url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={user}&domain={domain}&id={message_id}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()
    except:
        return None

def get_verification_code(user, domain, wait_time=120):
    start = time.time()
    while time.time() - start < wait_time:
        messages = get_messages(user, domain)
        for msg in messages:
            subject = msg.get("subject", "").lower()
            if "code" in subject or "verify" in subject or "sophon" in subject:
                msg_data = read_message(user, domain, msg["id"])
                if msg_data:
                    body = msg_data.get("body", "") + " " + msg_data.get("textBody", "")
                    code = re.search(r"\b(\d{4,8})\b", body)
                    if code:
                        return code.group(1)
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
            page.wait_for_selector("#email_field", timeout=15000)
            page.fill("#email_field", email)
        except:
            print(f"[{idx}] ⚠️ Warning: #email_field পাওয়া যায়নি, fallback চেষ্টা করছে...")
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
            print(f"[{idx}] ⚠️ Invite code ইনপুট খুঁজে পাওয়া যায়নি!")

        page.click("button")

        print(f"[{idx}] 📨 ইমেইল ও কোড সাবমিট হয়েছে। কোডের জন্য অপেক্ষা করছে...")

        code = get_verification_code(user, domain)
        if not code:
            print(f"[{idx}] ❌ কোড পাওয়া যায়নি।")
            return

        print(f"[{idx}] ✅ কোড পাওয়া গেছে: {code}")

        page.goto(INVITE_URL, wait_until="load")
        time.sleep(2)

        try:
            page.wait_for_selector("#email_field", timeout=15000)
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
