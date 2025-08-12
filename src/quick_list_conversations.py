#!/usr/bin/env python3
"""Hardened Poe.com conversation lister with resilient scrolling.

Features:
  * Auth cookie injection (p-b required; p-lat/formkey optional)
  * Handles /chat/ and /c/ link variants
  * Detects scroll container or falls back to window + END key presses
  * Multi‑strategy initial content wait (robust to DOM/UI changes)
  * Anti‑bot stealth flags; optional undetected-chromedriver
  * Time, scroll, and count based stopping criteria
  * Debug mode: verbose logging + screenshot + HTML dump on failure
  * Backwards‑compatible wrappers: setup_browser, extract_conversations
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

try:  # core selenium imports
    from selenium import webdriver  # type: ignore
    from selenium.common.exceptions import (  # type: ignore
        JavascriptException, TimeoutException, WebDriverException)
    from selenium.webdriver.chrome.options import Options  # type: ignore
    from selenium.webdriver.chrome.service import \
        Service as ChromeService  # type: ignore
    from selenium.webdriver.common.action_chains import \
        ActionChains  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.webdriver.common.keys import Keys  # type: ignore
    from selenium.webdriver.support import \
        expected_conditions as EC  # type: ignore
    from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
    SELENIUM_AVAILABLE = True
except Exception:  # pragma: no cover - provide lightweight fallbacks
    SELENIUM_AVAILABLE = False

    class _DummyChrome:  # minimal stub for tests sans selenium
        current_url = "https://poe.com/chats"
        page_source = ""

        def set_page_load_timeout(self, *_, **__):
            pass

        def get(self, *_, **__):
            pass

        def add_cookie(self, *_, **__):
            pass

        def find_elements(self, *_, **__):
            return []

        def execute_script(self, *_, **__):
            return 0

        def save_screenshot(self, *_, **__):
            return True

        def quit(self):  # noqa: D401
            pass

    class _WebDriverModule:
        Chrome = _DummyChrome

    webdriver = _WebDriverModule()  # type: ignore

    class By:  # type: ignore
        CSS_SELECTOR = "css"

    class Keys:  # type: ignore
        END = "END"

    class Options:  # type: ignore
        def add_argument(self, *_):
            pass

        def add_experimental_option(self, *_):
            pass

    class ChromeService:  # type: ignore
        def __init__(self, *_, **__):
            pass

    class ActionChains:  # type: ignore
        def __init__(self, *_, **__):
            pass

        def key_down(self, *_, **__):
            return self

        def key_up(self, *_, **__):
            return self

        def perform(self):
            pass

    # Exception stubs (only when selenium missing)
    class TimeoutException(Exception):  # type: ignore
        pass

    class WebDriverException(Exception):  # type: ignore
        pass

    class JavascriptException(Exception):  # type: ignore
        pass

    class EC:  # type: ignore
        @staticmethod
        def presence_of_element_located(_):
            return True
    class WebDriverWait:  # type: ignore
        def __init__(self, *_, **__):
            pass

        def until(self, condition):
            if callable(condition):
                return condition(None)
            return True

try:  # optional managers
    from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
    HAVE_WDM = True
except Exception:
    HAVE_WDM = False

try:  # optional stealth driver
    import undetected_chromedriver as uc  # type: ignore
    HAVE_UC = True
except Exception:
    HAVE_UC = False

POE_BASE = "https://poe.com"
POE_LOGIN = f"{POE_BASE}/login"
POE_CHATS = f"{POE_BASE}/chats"
CHAT_HREF_RE = re.compile(r"^/(chat|c)/")
ABS_CHAT_HREF_RE = re.compile(r"^https?://poe\.com/(chat|c)/", re.I)

PAGE_LOAD_TIMEOUT = 60
FIRST_CHAT_TIMEOUT = 30


def log(debug: bool, *args):
    if debug:
        print("[DEBUG]", *args, file=sys.stderr)


def load_tokens(config_path: str) -> Dict[str, str]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tokens: Dict[str, str] = {}
    for k in ["p-b", "p-lat", "formkey"]:
        if k in data and data[k]:
            tokens[k] = data[k]
    if "p-b" not in tokens:
        # Preserve existing test expectation of KeyError
        raise KeyError("p-b")
    return tokens


def build_driver(headless: bool, debug: bool) -> Any:
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,2000")
    chrome_options.add_argument("--lang=en-US,en")
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )
    try:
        chrome_options.add_experimental_option(  # type: ignore
            "excludeSwitches", ["enable-automation"]
        )
        chrome_options.add_experimental_option(  # type: ignore
            "useAutomationExtension", False
        )
    except Exception:
        pass
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )

    driver = None
    if HAVE_UC:
        log(debug, "Using undetected_chromedriver")
        try:
            driver = uc.Chrome(  # type: ignore
                options=chrome_options, headless=headless
            )
        except Exception as e:  # fallback
            log(debug, f"undetected_chromedriver failed: {e}")
            driver = None
    if driver is None:
        if HAVE_WDM:
            try:
                service = ChromeService(  # type: ignore
                    ChromeDriverManager().install()
                )
                driver = webdriver.Chrome(
                    service=service, options=chrome_options
                )
            except Exception as e:
                log(debug, f"webdriver_manager path failed: {e}")
                driver = None
        if driver is None:
            driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    except Exception:
        pass
    # Stealth: mask webdriver property
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": (
                    "Object.defineProperty(navigator, 'webdriver', "
                    "{get: () => undefined});"
                )
            },
        )
    except Exception:
        pass
    return driver


def set_auth_cookies(driver: Any, tokens: Dict[str, str], debug: bool) -> None:
    driver.get(POE_BASE)
    time.sleep(0.8)

    def add_cookie(name: str, value: str):
        cookie = {
            "name": name,
            "value": value,
            "domain": ".poe.com",
            "path": "/",
            "secure": True,
            "httpOnly": False,
        }
        driver.add_cookie(cookie)

    for k, v in tokens.items():
        try:
            add_cookie(k, v)
            log(debug, f"Set cookie {k}")
        except WebDriverException as e:
            log(debug, f"Retry cookie {k}: {e}")
            driver.get(POE_BASE)
            time.sleep(0.5)
            add_cookie(k, v)


def is_logged_in(driver: Any, debug: bool) -> bool:
    driver.get(POE_CHATS)
    time.sleep(2.0)
    path = urlparse(driver.current_url).path
    log(debug, "Current path after auth:", path)
    return "/login" not in path


def wait_for_initial_content(driver: Any, timeout: int, debug: bool) -> None:
    strategies = [
        (By.CSS_SELECTOR, 'a[href*="/chat/"]'),
        (By.CSS_SELECTOR, 'a[href^="/c/"]'),
        (By.CSS_SELECTOR, 'a[href^="https://poe.com/chat/"]'),
        (By.CSS_SELECTOR, 'a[href^="https://poe.com/c/"]'),
        (By.CSS_SELECTOR, 'main a[href]'),
    ]
    last = None
    for by, sel in strategies:
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, sel))  # type: ignore
            )
            log(debug, f"Initial content via selector: {sel}")
            return
        except Exception as e:
            last = e
    raise TimeoutException(f"Chats did not appear within {timeout}s") from last


def find_scrollable_container(driver: Any, debug: bool):
    try:
        containers = driver.execute_script(
            """
            const els = Array.from(document.querySelectorAll('*'));
            const c = els.filter(el => {
              const st = getComputedStyle(el);
              const can = el.scrollHeight - el.clientHeight > 80;
              const oy = st.overflowY;
              return can && (oy === 'auto' || oy === 'scroll');
            });
            c.sort((a,b)=>b.scrollHeight - a.scrollHeight);
            return c.slice(0,3);
            """
        )
        if containers:
            log(debug, f"Found {len(containers)} scrollable candidates")
        return containers or []
    except JavascriptException:
        return []


def get_scroll_height(driver: Any, el=None) -> int:
    if el:
        return driver.execute_script(
            "return arguments[0].scrollHeight || 0;", el
        )
    return driver.execute_script("return document.body.scrollHeight || 0;")


def scroll_container(driver: Any, el, amount: int = 1600):
    driver.execute_script(
        "arguments[0].scrollTop = arguments[0].scrollTop + arguments[1];",
        el,
        amount,
    )


def scroll_window_to_bottom(driver: Any):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


def press_end_key(driver: Any):
    try:
        ActionChains(driver).key_down(Keys.END).key_up(Keys.END).perform()
    except Exception:
        pass


def normalize_href(href: str) -> str:
    if not href:
        return ""
    if href.startswith("/"):
        return urljoin(POE_BASE, href)
    return href


def looks_like_chat_href(href: str) -> bool:
    if not href:
        return False
    path = urlparse(href).path or ""
    return bool(CHAT_HREF_RE.match(path) or ABS_CHAT_HREF_RE.match(href))


def collect_chat_links(driver: Any, debug: bool) -> List[Tuple[str, str]]:
    selectors = [
        'a[href^="/chat/"]',
        'a[href*="/chat/"]',
        'a[href^="/c/"]',
        'a[href^="https://poe.com/chat/"]',
        'a[href^="https://poe.com/c/"]',
    ]
    anchors = []
    for sel in selectors:
        try:
            anchors.extend(
                driver.find_elements(By.CSS_SELECTOR, sel)  # type: ignore
            )
        except Exception:
            continue
    items: List[Tuple[str, str]] = []
    seen_elem_ids: Set[str] = set()
    for a in anchors:
        try:
            elem_id = getattr(a, "id", None)
            if elem_id and elem_id in seen_elem_ids:
                continue
            if elem_id:
                seen_elem_ids.add(elem_id)
            href = normalize_href(a.get_attribute("href") or "")
            if not looks_like_chat_href(href):
                continue
            title = (a.text or "").strip()
            if not title:
                title = (
                    a.get_attribute("aria-label")
                    or a.get_attribute("title")
                    or ""
                ).strip()
            items.append((href, title))
        except Exception:
            continue
    # Deduplicate by href
    dedup: Dict[str, str] = {}
    for href, title in items:
        if href not in dedup:
            dedup[href] = title
    result = [(k, v) for k, v in dedup.items()]
    log(debug, f"Collected {len(result)} unique links")
    return result


def scroll_until_exhausted(
    driver: Any,
    debug: bool,
    max_scrolls: int,
    max_time: float,
    pause: float,
    limit: Optional[int],
) -> List[Dict]:
    start = time.time()
    containers = find_scrollable_container(driver, debug=debug)
    container = containers[0] if containers else None
    collected: List[Dict] = []
    seen_hrefs: Set[str] = set()

    def harvest():
        for href, title in collect_chat_links(driver, debug):
            if href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            collected.append(
                {
                    "id": len(collected) + 1,
                    "title": title or "",
                    "url": href,
                    "method": "link",
                }
            )

    harvest()
    prev_height = get_scroll_height(driver, container)
    no_new = 0
    scrolls = 0
    while scrolls < max_scrolls:
        if limit and len(collected) >= limit:
            break
        if (time.time() - start) > max_time:
            break
        if container:
            scroll_container(driver, container, amount=1800)
        else:
            scroll_window_to_bottom(driver)
        press_end_key(driver)
        time.sleep(pause)
        harvest()
        h = get_scroll_height(driver, container)
        if h <= prev_height:
            no_new += 1
        else:
            no_new = 0
        prev_height = h
        scrolls += 1
        if no_new >= 3:
            break
    log(
        debug,
        f"Scrolling ended after {scrolls} scrolls; collected {len(collected)}",
    )
    return collected


def write_output(data: List[Dict], out_path: Optional[str]) -> str:
    if out_path:
        path = Path(out_path)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path(f"conversations_{ts}.json")
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return str(path)


def dump_debug_artifacts(driver: Any, debug_dir: Path, debug: bool):
    try:
        debug_dir.mkdir(parents=True, exist_ok=True)
        png = debug_dir / "screenshot.png"
        html_path = debug_dir / "page.html"
        try:
            driver.save_screenshot(str(png))
        except Exception:
            pass
        html_path.write_text(
            getattr(driver, "page_source", ""), encoding="utf-8"
        )
        log(debug, f"Debug artifacts written to {debug_dir}")
    except Exception as e:
        log(debug, f"Failed writing debug artifacts: {e}")


def parse_args(argv: Optional[List[str]] = None):
    p = argparse.ArgumentParser(
        description="List Poe.com conversations (robust scrolling)."
    )
    p.add_argument(
        "--config", default="config/poe_tokens.json",
        help="Path to poe_tokens.json",
    )
    p.add_argument(
        "--no-headless", action="store_true", help="Show browser window"
    )
    p.add_argument(
        "--max-scrolls", type=int, default=300, help="Max scroll iterations"
    )
    p.add_argument(
        "--scroll-pause", type=float, default=0.7,
        help="Seconds to sleep after each scroll"
    )
    p.add_argument(
        "--limit", type=int, default=0,
        help="Stop after collecting this many conversations (0 = all)"
    )
    p.add_argument(
        "--output", default="",
        help=(
            "Output JSON path (default: conversations_YYYYMMDD_HHMMSS.json)"
        ),
    )
    p.add_argument(
        "--max-time", type=float, default=120.0,
        help="Overall time budget for scrolling (seconds)"
    )
    p.add_argument(
        "--debug", action="store_true",
        help="Enable verbose debug logging & artifacts on failure"
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    headless = not args.no_headless
    debug = bool(args.debug)
    try:
        tokens = load_tokens(args.config)
    except Exception as e:
        print(
            f"[ERROR] Could not load tokens from {args.config}: {e}",
            file=sys.stderr,
        )
        return 2
    driver = None
    try:
        driver = build_driver(headless=headless, debug=debug)
        set_auth_cookies(driver, tokens, debug=debug)
        if not is_logged_in(driver, debug=debug):
            print(
                "[ERROR] Authentication failed (redirected to /login). "
                "Refresh p-b (and optionally p-lat, formkey).",
                file=sys.stderr,
            )
            return 3
        driver.get(POE_CHATS)
        wait_for_initial_content(
            driver, timeout=FIRST_CHAT_TIMEOUT, debug=debug
        )
        limit = args.limit if args.limit and args.limit > 0 else None
        results = scroll_until_exhausted(
            driver,
            debug=debug,
            max_scrolls=args.max_scrolls,
            max_time=args.max_time,
            pause=args.scroll_pause,
            limit=limit,
        )
        out_file = write_output(results, args.output or None)
        print(f"[OK] Found {len(results)} conversations")
        print(f"[OK] Saved to {out_file}")
        return 0
    except TimeoutException as e:
        print(
            f"[ERROR] Timed out waiting for chats to load: {e}",
            file=sys.stderr,
        )
        if driver and debug:
            dump_debug_artifacts(driver, Path("debug_artifacts"), debug=True)
        print(
            "[HINT] Try: --no-headless, increase --scroll-pause (1.0–1.5), "
            "or --max-time 180.",
            file=sys.stderr,
        )
        return 4
    except WebDriverException as e:
        print(f"[ERROR] WebDriver error: {e}", file=sys.stderr)
        if driver and debug:
            dump_debug_artifacts(driver, Path("debug_artifacts"), debug=True)
        return 5
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.", file=sys.stderr)
        return 130
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


# --- Backwards-compatible legacy wrappers for existing tests ---
def setup_browser(headless: bool = True):  # type: ignore
    drv = build_driver(headless=headless, debug=False)
    try:
        drv.implicitly_wait(10)  # type: ignore
    except Exception:
        pass
    return drv


def extract_conversations(driver, limit: int = 0):  # type: ignore
    """Lightweight single-pass extraction used in unit tests."""
    items = collect_chat_links(driver, debug=False)
    results: List[Dict] = []
    for idx, (href, title) in enumerate(items, start=1):
        results.append({
            "id": idx,
            "title": title,
            "url": href,
            "method": "link",
        })
        if limit and len(results) >= limit:
            break
    return results


def scroll_to_bottom(driver):  # pragma: no cover
    try:
        scroll_window_to_bottom(driver)
    except Exception:
        pass


if __name__ == "__main__":  # script entry
    sys.exit(main())
