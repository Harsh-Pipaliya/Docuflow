"""Verify desktop and phone views against the running Compose stack."""

from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = "http://127.0.0.1:8080"
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base)
    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill(Path(".env.demo-login").read_text().strip())
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
    page.get_by_role("link", name="Upload", exact=True).click()
    page.locator("input[type=file]").set_input_files("samples/generated/valid.pdf")
    page.get_by_role("button", name="Upload", exact=True).click()
    page.get_by_role("link", name="View document").click()
    expect(page.locator("#history")).to_contain_text("Processed")
    page.screenshot(path="evidence/after/browser-detail.png", full_page=True)
    page.get_by_role("link", name="Documents", exact=True).click()
    page.get_by_label("Search by filename").fill("valid.pdf")
    expect(page.locator("#list")).to_contain_text("valid.pdf")
    page.set_viewport_size({"width": 390, "height": 844})
    page.get_by_role("link", name="Integrations").click()
    expect(page.locator("#services")).to_contain_text("Simulated")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.screenshot(path="evidence/after/browser-mobile.png", full_page=True)
    page.get_by_role("button", name="Sign out").click()
    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
    assert not errors, errors
    browser.close()
print(
    "Edge desktop sign-in/upload/detail/history/search and mobile integrations/sign-out passed."
)
