import time
import random
import string
from playwright.sync_api import sync_playwright

INVITE_URL = "https://app.sophon.xyz/invite/"

def random_string(length=10):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def create_temp_email():
    user = random_string(10)
    domain = "1secmail.com"
    email = f"{user}@{domain}"
    return user, domain, email

def get_verification_code_manual(idx):
    return input(f"[{idx}] ইমেইল থেকে ভেরিফিকেশন কোড দিন (কপি করে পেস্ট করুন): ").strip()

def create_account(playwright, invite_code, idx):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    try:
        user, domain, email = create_temp_email()
        print(f"[{idx}] 📧 টেম্প ইমেইল তৈরি: {email}")

        page.goto(INVITE_URL, wait_until="load")
        time.sleep(2)

        # ইমেইল ফিল্ড খোঁজা ও পূরণ
        try:
            page.fill("#email_field", email)
        except:
            print(f"[{idx}] ⚠️ #email_field পাওয়া যায়নি, fallback চেষ্টা চলছে...")
            inputs = page.locator("input")
            for i in range(inputs.count()):
                try:
                    placeholder = inputs.nth(i).get_attribute("placeholder")
                    if placeholder and "email" in placeholder.lower():
                        inputs.nth(i).fill(email)
                        break
                except:
                    continue

        # ইনভাইট কোড পূরণ
        try:
            page.fill("input[type='text']", invite_code)
        except:
            print(f"[{idx}] ⚠️ ইনভাইট কোড ইনপুট খুঁজে পাওয়া যায়নি!")

        # সাবমিট বাটনে ক্লিক
        page.click("button")

        print(f"[{idx}] 📨 ইমেইল ও কোড সাবমিট হয়েছে। ইমেইল খুলে কোড কপি করে এখানে পেস্ট করুন।")

        code = get_verification_code_manual(idx)
        if not code:
            print(f"[{idx}] ❌ কোড দেওয়া হয়নি।")
            return

        # কোড সাবমিট করা
        try:
            page.fill("input[type='number']", code)
            page.click("button")
        except:
            print(f"[{idx}] ⚠️ ভেরিফিকেশন কোড ইনপুট বা সাবমিট বাটন পাওয়া যায়নি!")

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
