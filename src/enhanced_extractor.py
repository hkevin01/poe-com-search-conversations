#!/usr/bin/env python3
"""Enhanced Poe.com Conversation Extractor (clean, deduplicated).

Reuses hardened scrolling/auth from quick_list_conversations when present.
Falls back to a minimal snapshot approach otherwise.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver  # type: ignore
from selenium.common.exceptions import TimeoutException  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore

from database import Conversation, ConversationDatabase  # type: ignore

try:  # Hardened logic
    from quick_list_conversations import \
        FIRST_CHAT_TIMEOUT as SHARED_FIRST_CHAT_TIMEOUT
    from quick_list_conversations import \
        build_driver as shared_build_driver  # type: ignore
    from quick_list_conversations import is_logged_in as shared_is_logged_in
    from quick_list_conversations import load_tokens as shared_load_tokens
    from quick_list_conversations import \
        scroll_until_exhausted as shared_scroll_until_exhausted
    from quick_list_conversations import \
        set_auth_cookies as shared_set_auth_cookies
    from quick_list_conversations import \
        wait_for_initial_content as shared_wait_for_initial_content
    HAVE_SHARED = True
except Exception:  # pragma: no cover
    HAVE_SHARED = False


class EnhancedPoeExtractor:
    def __init__(
        self,
        p_b_token: str,
        headless: bool = True,
        db_path: Optional[str] = None,
    ) -> None:
        self.p_b_token = p_b_token
        self.headless = headless
        self.db_path = db_path or "storage/conversations.db"
        self.db = ConversationDatabase(self.db_path)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
        self.total_found = 0
        self.new_added = 0
        self.updated = 0
        self.errors = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    # Driver -----------------------------------------------------------
    def setup_driver(self):  # type: ignore
        if HAVE_SHARED:
            drv = shared_build_driver(headless=self.headless, debug=False)
            try:
                drv.implicitly_wait(10)
            except Exception:
                pass
            self.logger.info("✅ Driver (shared) initialized")
            return drv
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        for arg in (
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1280,1600",
        ):
            opts.add_argument(arg)
        drv = webdriver.Chrome(options=opts)
        try:
            drv.implicitly_wait(10)
        except Exception:
            pass
        self.logger.info("✅ Driver (fallback) initialized")
        return drv

    # Authentication ---------------------------------------------------
    def login(self, driver) -> bool:  # type: ignore
        if HAVE_SHARED:
            tokens = {"p-b": self.p_b_token}
            for cfg in ("config/poe_tokens.json", "config/config.json"):
                if os.path.exists(cfg):
                    try:
                        tokens.update(shared_load_tokens(cfg))
                        break
                    except Exception:
                        continue
            shared_set_auth_cookies(driver, tokens, debug=False)
            if not shared_is_logged_in(driver, debug=False):
                self.logger.error("❌ Login failed (shared path)")
                return False
            driver.get("https://poe.com/chats")
            try:
                shared_wait_for_initial_content(
                    driver, timeout=SHARED_FIRST_CHAT_TIMEOUT, debug=False
                )
            except Exception as e:
                self.logger.warning(
                    f"⚠️ Initial content wait warning: {e}"
                )
            self.logger.info("✅ Authenticated (shared path)")
            return True
        driver.get("https://poe.com")
        time.sleep(2)
        driver.add_cookie(
            {"name": "p-b", "value": self.p_b_token, "domain": ".poe.com"}
        )
        driver.refresh()
        time.sleep(3)
        has_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/chat/']")
        if has_links:
            self.logger.info("✅ Authenticated (fallback path)")
            return True
        self.logger.error("❌ Authentication failed (fallback path)")
        return False

    # Collection -------------------------------------------------------
    def collect(self, driver) -> List[Dict[str, str]]:  # type: ignore
        if HAVE_SHARED:
            raw = shared_scroll_until_exhausted(
                driver,
                debug=False,
                max_scrolls=400,
                max_time=300,
                pause=0.9,
                limit=None,
            )
            out: List[Dict[str, str]] = []
            for r in raw:
                url = r.get("url", "")
                cid = ""
                if "/chat/" in url:
                    cid = url.split("/chat/")[-1].split("?")[0]
                elif "/c/" in url:
                    cid = url.split("/c/")[-1].split("?")[0]
                out.append(
                    {
                        "id": cid or r.get("id", ""),
                        "title": r.get("title") or f"Conversation {cid}",
                        "url": url,
                    }
                )
            self.total_found = len(out)
            return out
        anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='/chat/']")
        results: List[Dict[str, str]] = []
        seen = set()
        for a in anchors:
            try:
                href = a.get_attribute("href") or ""
                if not href or href in seen or "/chat/" not in href:
                    continue
                seen.add(href)
                cid = href.split("/chat/")[-1].split("?")[0]
                title = (a.text or "").strip() or f"Conversation {cid}"
                results.append(
                    {"id": cid, "title": title, "url": href}
                )
            except Exception:
                continue
        self.total_found = len(results)
        return results

    # Persistence ------------------------------------------------------
    def persist(self, conversations: List[Dict[str, str]]) -> None:
        for conv in conversations:
            try:
                existing = self.db.get_conversation_by_id(  # type: ignore
                    conv["id"]
                )
                if existing:
                    if not existing.url or existing.url != conv["url"]:
                        existing.url = conv["url"]
                        self.db.update_conversation(existing)
                        self.updated += 1
                else:
                    conversation = Conversation(  # type: ignore
                        id=conv["id"],
                        title=conv["title"],
                        url=conv["url"],
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        message_count=0,
                        content="",
                        bot_name="",
                        tags=[],
                    )
                    self.db.add_conversation(conversation)
                    self.new_added += 1
            except Exception as e:
                self.errors += 1
                self.logger.error(
                    f"❌ Store failed {conv.get('id')}: {e}"
                )

    # Public API -------------------------------------------------------
    def extract_all_conversations(self) -> bool:
        self.start_time = datetime.now()
        driver = None
        try:
            driver = self.setup_driver()
            if not self.login(driver):
                return False
            conversations = self.collect(driver)
            if not conversations:
                self.logger.error("❌ No conversations discovered")
                return False
            self.persist(conversations)
            return True
        except TimeoutException as e:
            self.logger.error(f"❌ Timeout: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Extraction error: {e}")
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            self.end_time = datetime.now()
            self.print_stats()

    def print_stats(self) -> None:
        duration = 0.0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        print("\n" + "=" * 50)
        print("📊 ENHANCED EXTRACTION SUMMARY")
        print("=" * 50)
        print(
            "Total: {} | New: {} | Updated: {} | Errors: {}".format(
                self.total_found, self.new_added, self.updated, self.errors
            )
        )
        if duration:
            rate = self.total_found / duration if duration else 0
            print(f"Duration: {duration:.1f}s | Rate: {rate:.2f}/s")
        print("=" * 50)


def main() -> int:
    cfg_paths = ["config/poe_tokens.json", "config/config.json"]
    config = None
    for pth in cfg_paths:
        if os.path.exists(pth):
            try:
                with open(pth, "r", encoding="utf-8") as f:
                    config = json.load(f)
                break
            except Exception as e:
                print(f"❌ Failed reading {pth}: {e}")
                return 1
    if not config:
        print("❌ No configuration file found")
        return 1
    p_b = config.get("p-b") or config.get("p_b_token")
    if not p_b:
        print("❌ Missing p-b token")
        return 1
    extractor = EnhancedPoeExtractor(p_b_token=p_b, headless=True)
    ok = extractor.extract_all_conversations()
    print("✅ Extraction completed" if ok else "❌ Extraction failed")
    return 0 if ok else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
    p_b = config.get("p-b") or config.get("p_b_token")
    if not p_b:
        print("❌ Missing p-b token")
        return 1
    extractor = EnhancedPoeExtractor(p_b_token=p_b, headless=True)
    ok = extractor.extract_all_conversations()
    print("✅ Extraction completed" if ok else "❌ Extraction failed")
    return 0 if ok else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
