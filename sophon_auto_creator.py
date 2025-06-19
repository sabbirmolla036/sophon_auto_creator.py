import time
import random
import re
import sys
from playwright.sync_api import sync_playwright


# === CONFIGURATION ===
INVITE_LINK = "https://app.sophon.xyz/invite/"
INVITE_CODE = "YOUR_INVITE_CODE_HERE"  # <-- Replace this with your invite code


def create_account(playwright, idx):
    # Random user-agent for stealth
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

    # Anti-bot JS
    page.add_init_script(
        """() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
    }"""
    )

    # Block images/styles/fonts for faster loading
    page.route(
        "**/*",
        lambda route: route.abort()
        if route.request.resource_type in ["image", "stylesheet", "font"]
        else route.continue_(),
    )

    try:
        # Step 1: Get temp email
        page.goto("https://etempmail.net/", wait_until="networkidle")
        email = page.locator("#mail").input_value()
        print(f"[{idx}] Temporary email: {email}")

        # Step 2: Visit Sophon invite page and submit invite code + email
        page.goto(INVITE_LINK, wait_until="networkidle")
        page.fill('input[name="inviteCode"]', INVITE_CODE)
        page.fill('input[name="email"]', email)
        page.click('button[type="submit"]')
        print(f"[{idx}] Submitted invite and email, waiting for verification email...")

        # Step 3: Poll etempmail for verification code
        page.goto("https://etempmail.net/", wait_until="networkidle")
        verification_code = None
        for _ in range(20):
            time.sleep(3)
            if page.locator(".message-item").count() > 0:
                page.locator(".message-item").first.click()
                page.wait_for_selector(".mail-text")
                body = page.inner_text(".mail-text")
                match = re.search(r"\b(\d{4,8})\b", body)
                if match:
                    verification_code = match.group(1)
                    break
            page.reload(wait_until="networkidle")

        if not verification_code:
            print(f"[{idx}] ❌ Verification code not found, skipping.")
        else:
            print(f"[{idx}] Verification code received: {verification_code}")

            # Step 4: Submit the verification code to complete signup
            page.goto(INVITE_LINK, wait_until="networkidle")
            page.fill('input[name="inviteCode"]', INVITE_CODE)
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
    # Get number of accounts to create
    if len(sys.argv) > 1:
        try:
            total_accounts = int(sys.argv[1])
        except ValueError:
            print("Invalid input. Usage: python sophon_account_creator.py <number_of_accounts>")
            return
    else:
        total_accounts = int(input("Enter number of accounts to create: "))

    with sync_playwright() as playwright:
        for i in range(1, total_accounts + 1):
            try:
                create_account(playwright, i)
            except Exception as e:
                print(f"[{i}] ❌ Error during account creation: {e}")
            time.sleep(random.uniform(5, 8))  # wait to reduce bot detection


if __name__ == "__main__":
    main()
