import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from app.core.errors import AccessPilotError


def require_scan_assets(axe_path: Path) -> None:
    if not axe_path.is_file():
        raise AccessPilotError("browser_unavailable", "The vendored axe engine is missing.", 503)


async def scan_url(url: str, axe_path: Path, timeout_ms: int) -> dict[str, Any]:
    require_scan_assets(axe_path)
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="load", timeout=timeout_ms)
                title = await page.title()
                await page.add_script_tag(path=str(axe_path))
                result = await page.evaluate(
                    """async () => {
                        const result = await axe.run(document, {
                          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"] }
                        });
                        return result;
                    }"""
                )
                return {"title": title, "axe": result}
            finally:
                await browser.close()
    except ImportError as error:
        raise AccessPilotError("browser_unavailable", "Install Playwright with Chromium before scanning.", 503) from error
    except asyncio.TimeoutError as error:
        raise AccessPilotError("scan_failed", "The page did not load before the scan timeout.", 502) from error
    except Exception as error:
        raise AccessPilotError("scan_failed", "The page could not be scanned.", 502) from error


def scan_url_sync(url: str, axe_path: Path, timeout_ms: int) -> dict[str, Any]:
    return asyncio.run(scan_url(url, axe_path, timeout_ms))


def browser_available(axe_path: Path) -> bool:
    if not axe_path.is_file():
        return False
    try:
        async def launch_and_close() -> None:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                await browser.close()
        asyncio.run(launch_and_close())
        return True
    except Exception:
        return False
