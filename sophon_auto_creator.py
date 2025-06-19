import time, random, re, sys
from playwright.sync_api import sync_playwright

# === CONFIGURATION ===
INVITE_LINK = "https://app.sophon.xyz/invite/"
INVITE_CODE = "YOUR_INVITE_CODE_HERE"  # <== Replace this with your actual code


def stealth_setup(page):
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
          "AppleWebKit/537.36 (KHTML, like Gecko) " +
          f"Chrome/{random.randint(90,114)}.0.{random.randint(1000,4000)}.0 Safari/537.36")
    page.set_user_agent(ua)
    page.set_viewport_size({
        "width": random.randint(1280, 1920),
        "height": random.randint(720, 1080)
    })
    page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font"] else route.continue_())
    page.add_init_script("""() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
    }""")


def create_account(playwright, idx):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    stealth_setup(page)

    # 1. Get temporary email
    page.goto("https://etempmail.net/", wait_until="networkidle")
    email = page.locator("#mail").input_value()
    print(f"[{idx}] Temporary email: {email}")

    # 2. Open Sophon invite page
    page.goto(INVITE_LINK, wait_until="networkidle")
    page.fill('input[name="inviteCode"]', INVITE_CODE)
    page.fill('input[name="email"]', email)
    page.click('button[type="submit"]')
    print(f"[{idx}] Invite code submitted. Waiting for verification email...")

    # 3. Poll for verification email
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
        print(f"[{idx}] ❌ No verification code found. Skipping.")
    else:
        print(f"[{idx}] 🔑 Code received: {verification_code}")
        page.goto(INVITE_LINK, wait_until="networkidle")
        page.fill('input[name="inviteCode"]', INVITE_CODE)
        page.fill('input[name="email"]', email)
        page.fill('input[name="verificationCode"]', verification_code)
        page.click('button[type="verify"]')
        print(f"[{idx}] ✅ Account #{idx} created successfully!")

    browser.close()


def main():
    if len(sys.argv) > 1:
        try:
            target = int(sys.argv[1])
        except ValueError:
            print("Invalid number passed. Usage: python sophon_auto_creator.py <number>")
            return
    else:
        target = int(input("🔢 Enter how many accounts to create: "))

    with sync_playwright() as p:
        for i in range(1, target + 1):
            try:
                create_account(p, i)
            except Exception as e:
                print(f"[{i}] ❌ Error: {str(e)}")
            time.sleep(random.uniform(5, 8))


if __name__ == "__main__":
    main()
