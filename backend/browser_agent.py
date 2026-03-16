import asyncio
import io
import json
import base64
import logging
import traceback
import time
from typing import Callable, Awaitable
from pydantic import BaseModel, Field

from google import genai
from google.genai import types
from google.genai import errors
import os

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

class BrowserActionResult(BaseModel):
    success: bool = Field(..., description="Whether the action succeeded.")
    message: str = Field(..., description="A human-readable description of the result.")
    current_url: str = Field(default="", description="The URL of the browser after the action was performed.")
    page_summary: str = Field(default="", description="Summary of the current page content.")

# Type alias for the unified callback: (base64_screenshot, action_description) -> None
BrowserUpdateCallback = Callable[[str, str], Awaitable[None]]

class VisualAutomationAgent:
    # 🚨 REVERTED TO GEMINI-2.5-FLASH: It possesses superior spatial reasoning for complex e-commerce UIs!
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        # 🚨 PAID TIER ACTIVATED: This key will now use your $400 GCP Credits!
        browser_key = os.environ.get("GEMINI_API_KEY_BROWSER") or os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=browser_key)
        
        self.model_name = model_name
        self._DONE_SIGNALS = {"done", "finished", "complete", "task_fulfilled", "none"}
        self.MAX_STEPS = 15

    @staticmethod
    def _extract_search_term(goal: str) -> str:
        """Extract the actual search term from goals like 'YouTube and search for zainalabdeen'."""
        import re
        match = re.search(r'(?:search\s+for|look\s+up|find|search)\s+(.+)', goal, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    async def run_autonomous_loop(
        self,
        goal: str,
        on_update: "BrowserUpdateCallback | None" = None,
    ) -> BrowserActionResult:
        """
        Self-driving see → think → act loop.
        Wraps the synchronous Playwright execution in a thread to avoid blocking FastAPI.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._run_sync_loop,
            goal,
            on_update,
            loop,
        )

    def _run_sync_loop(
        self,
        goal: str,
        on_update: "BrowserUpdateCallback | None",
        asyncio_loop: asyncio.AbstractEventLoop,
    ) -> BrowserActionResult:
        """
        Synchronous Playwright loop running in a worker thread.
        After every action, fires the on_update callback with (screenshot_b64, action_description).
        """

        def _fire_update(b64_img: str, action_text: str):
            """Thread-safe bridge: schedule the async callback on the main event loop."""
            if on_update:
                future = asyncio.run_coroutine_threadsafe(
                    on_update(b64_img, action_text), asyncio_loop
                )
                try:
                    future.result(timeout=5)
                except Exception as cb_err:
                    logging.warning(f"[Loop] Callback error (non-fatal): {cb_err}")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-web-security",
                        "--disable-blink-features=AutomationControlled",
                        "--window-size=1280,720",
                        "--disable-extensions",
                        "--disable-default-apps",
                        "--disable-sync",
                        "--no-first-run",
                        "--no-zygote",
                        "--hide-scrollbars",
                        "--mute-audio"
                    ]
                )
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                context = browser.new_context(
                    user_agent=ua,
                    viewport={"width": 1280, "height": 720},
                    locale="en-US",
                    timezone_id="America/New_York",
                )
                page = context.new_page()
                page.set_default_timeout(15000)

                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                # 🚨 THE SMART DOMAIN ROUTER: Instantly routes to e-commerce sites!
                start_url = "https://duckduckgo.com"
                goal_lower = goal.lower()
                
                import re
                domain_match = re.search(r'(?:go to|navigate to|open)\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', goal_lower)
                
                if domain_match:
                    start_url = f"https://{domain_match.group(1).strip()}"
                elif "wikipedia" in goal_lower or "ukipedia" in goal_lower:
                    start_url = "https://www.wikipedia.org"
                elif "youtube" in goal_lower:
                    start_url = "https://www.youtube.com"
                elif "amazon" in goal_lower:
                    start_url = "https://www.amazon.com"

                logging.info(f"[Loop] Navigating to initial URL: {start_url}")
                try:
                    page.goto(start_url, wait_until="domcontentloaded")
                except Exception as e:
                    logging.warning(f"[Loop] Initial navigation timeout, but continuing: {e}")

                search_term = self._extract_search_term(goal)
                logging.info(f"[Loop] Extracted search term: '{search_term}' from goal: '{goal}'")

                for step in range(1, self.MAX_STEPS + 1):
                    logging.info(f"[Loop] Step {step}/{self.MAX_STEPS} — goal: {goal}")

                    screenshot_bytes = page.screenshot(type="jpeg", quality=80)
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

                    screenshot_part = types.Part.from_bytes(
                        data=screenshot_bytes, mime_type="image/jpeg"
                    )

                    _fire_update(screenshot_b64, f"Step {step}: Analyzing page...")

                    search_hint = ""
                    if search_term:
                        search_hint = f"\n*** THE SEARCH TERM YOU MUST TYPE IS: {search_term} ***\n"
                    
                    prompt = (
                        f"You are a browser automation agent. Your ONLY job is to fulfill this goal:\n"
                        f"GOAL: {goal}\n"
                        f"{search_hint}\n"
                        f"You are on step {step}. Study the screenshot carefully.\n\n"
                        f"ABSOLUTE RULES:\n"
                        f"- You must ONLY type text that comes directly from the GOAL above.\n"
                        f"- NEVER type random text like 'hello world', 'how to make a website', or 'weather'.\n"
                        f"- NEVER type placeholder text.\n"
                        f"- The ONLY text you are allowed to type is: {search_term if search_term else goal}\n"
                        f"- If the goal is already fulfilled (correct page is shown), respond: {{\"action\": \"done\", \"summary\": \"Goal completed\"}}\n\n"
                        f"Available actions (return exactly ONE as JSON):\n"
                        f"  {{\"action\": \"click\", \"x\": 640, \"y\": 400, \"description\": \"Search button\"}}\n"
                        f"  {{\"action\": \"type_text\", \"x\": 640, \"y\": 400, \"text\": \"{search_term if search_term else goal}\", \"description\": \"Search bar\"}}\n"
                        f"  {{\"action\": \"scroll\", \"direction\": \"down\"}}\n"
                        f"  {{\"action\": \"navigate\", \"url\": \"https://example.com\"}}\n"
                        f"  {{\"action\": \"done\", \"summary\": \"Goal completed\"}}\n\n"
                        f"Return ONLY valid JSON. No explanation."
                    )

                    while True:
                        try:
                            response = self.client.models.generate_content(
                                model=self.model_name,
                                contents=[prompt, screenshot_part],
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json",
                                    temperature=0.0,
                                )
                            )
                            result_text = (response.text or "").strip()
                            break 
                        except errors.ClientError as e:
                            if e.code == 429 or "RESOURCE_EXHAUSTED" in str(e):
                                logging.warning(f"[Loop] 🚨 Gemini Rate Limit Hit! Sleeping for 15 seconds...")
                                _fire_update(screenshot_b64, "Hit Rate Limit! Pausing for 15s to reset quota...")
                                time.sleep(15)
                                continue
                            else:
                                logging.error(f"[Loop] API Error: {e}")
                                raise e
                        except Exception as e:
                            logging.error(f"[Loop] Unexpected generic crash during generate_content: {e}")
                            raise e
                            
                    logging.info(f"[Loop] Model returned: {result_text}")

                    clean_text = result_text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    elif clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    clean_text = clean_text.strip()

                    try:
                        decision = json.loads(clean_text)
                    except json.JSONDecodeError:
                        logging.warning(f"[Loop] Non-JSON model output: {result_text}")
                        _fire_update(screenshot_b64, "Model formatting error. Retrying...")
                        time.sleep(2)
                        continue

                    action = decision.get("action", "").lower()

                    if action in self._DONE_SIGNALS:
                        summary = decision.get("summary", "Task completed.")
                        logging.info(f"[Loop] Model signaled done: {summary}")
                        _fire_update(screenshot_b64, f"Done: {summary}")
                        return BrowserActionResult(
                            success=True,
                            message=summary,
                            current_url=page.url,
                        )

                    action_description = ""
                    try:
                        if action == "click":
                            x, y = int(decision["x"]), int(decision["y"])
                            desc = decision.get("description", "element")
                            page.mouse.click(x, y)
                            action_description = f"Clicking {desc} at ({x}, {y})"
                            logging.info(f"[Loop] {action_description}")

                        elif action == "type_text":
                            x, y = int(decision["x"]), int(decision["y"])
                            text = decision.get("text", "")
                            desc = decision.get("description", "field")
                            page.mouse.click(x, y)
                            time.sleep(0.15)
                            page.keyboard.type(text)
                            action_description = f"Typing '{text}' into {desc}"
                            logging.info(f"[Loop] {action_description}")

                        elif action == "scroll":
                            direction = decision.get("direction", "down")
                            delta = 600 if direction == "down" else -600
                            page.mouse.wheel(delta_x=0, delta_y=delta)
                            action_description = f"Scrolling {direction}"
                            logging.info(f"[Loop] {action_description}")

                        elif action == "navigate":
                            url = decision.get("url", "")
                            page.goto(url, wait_until="domcontentloaded")
                            action_description = f"Navigating to {url}"
                            logging.info(f"[Loop] {action_description}")

                        else:
                            logging.warning(f"[Loop] Unknown action '{action}' — stopping.")
                            break

                    except Exception as action_err:
                        action_description = f"Action error: {action_err}"
                        logging.error(f"[Loop] {action_description}")
                        _fire_update(screenshot_b64, action_description)
                        continue

                    time.sleep(0.4)

                    try:
                        post_screenshot_bytes = page.screenshot(type="jpeg", quality=80)
                        post_screenshot_b64 = base64.b64encode(post_screenshot_bytes).decode("utf-8")
                        _fire_update(post_screenshot_b64, action_description)
                    except Exception:
                        _fire_update(screenshot_b64, action_description)

                    # 🚨 FULL SPEED AHEAD: Because you are on the Paid Tier, 
                    # we can blast through actions with just a tiny 1.5s visual processing buffer!
                    time.sleep(1.5)

                logging.warning(f"[Loop] Hit {self.MAX_STEPS}-step limit without completion.")
                return BrowserActionResult(
                    success=False,
                    message=f"Reached {self.MAX_STEPS}-step limit without completing the task.",
                    current_url=page.url,
                )

        except Exception as e:
            err_str = f"Browser thread generic crash: {str(e)}"
            logging.error(f"[Loop] {err_str}\n{traceback.format_exc()}")
            
            if on_update:
                try:
                    asyncio.run_coroutine_threadsafe(
                        on_update("", f"🚨 Fatal Error: {str(e)}"), asyncio_loop
                    )
                except:
                    pass
                    
            return BrowserActionResult(
                success=False,
                message=err_str,
                current_url="",
            )