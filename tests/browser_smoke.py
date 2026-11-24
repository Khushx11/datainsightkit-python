"""Run with Python after installing Playwright and Google Chrome."""

import json
import subprocess
import sys
from tempfile import TemporaryDirectory

from playwright.sync_api import expect, sync_playwright


with TemporaryDirectory() as root, subprocess.Popen(
    [sys.executable, "-m", "datainsightkit.web", "--port", "0"],
    cwd=root, stdout=subprocess.PIPE, text=True,
) as server:
    try:
        address = server.stdout.readline().strip().removeprefix("Open ")
        assert address.startswith("http://127.0.0.1:"), address
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome")
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(address)
            expect(page.get_by_text("12,330", exact=True)).to_be_visible()
            page.get_by_text("Paste CSV instead").click()
            page.locator("#csv").fill("Browser,Revenue\n1,12\n2,18\n3,25\n")
            page.get_by_role("button", name="Profile pasted CSV").click()
            association = page.get_by_text("Browser × Revenue", exact=False)
            expect(association).to_be_visible()
            page.get_by_role("button", name="Inspect Browser").click()
            toggle = page.get_by_role("checkbox", name="Treat Browser as categorical")
            toggle.check()
            expect(page.get_by_role("status")).to_have_text("Column types updated.")
            expect(association).to_have_count(0)
            with page.expect_download() as export:
                page.get_by_role("button", name="Export JSON").click()
            report = json.loads(export.value.path().read_text())
            assert report["categorical_overrides"] == ["Browser"]
            assert report["associations"] == []
            toggle.uncheck()
            expect(association).to_be_visible()
            assert not errors, errors
    finally:
        server.terminate()
