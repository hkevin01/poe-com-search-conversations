#!/usr/bin/env python3
"""
Enhanced Poe.com Conversation Extractor with Infinite Scroll
Extracts ALL conversations by scrolling through the entire conversation list
"""

import json
import time
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from database import ConversationDatabase, Conversation

class EnhancedPoeExtractor:
    """Enhanced extractor with infinite scroll and URL storage capabilities."""
    
    def __init__(self, p_b_token: str, headless: bool = True, db_path: str = None):
        self.p_b_token = p_b_token
        self.headless = headless
        self.db_path = db_path or "storage/conversations.db"
        self.db = ConversationDatabase(self.db_path)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Extraction statistics
        self.stats = {
            'total_found': 0,
            'new_conversations': 0,
            'updated_conversations': 0,
            'errors': 0,
            'scroll_iterations': 0,
            'start_time': None,
            'end_time': None
        }

    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with optimized settings - based on quick_*.py approach."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Essential arguments (from working quick_*.py files)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        # Set realistic user agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Window size for consistency
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            
            self.logger.info("✅ Chrome driver initialized successfully")
            return driver
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            raise

    def login_to_poe(self, driver: webdriver.Chrome) -> bool:
        """Login to Poe.com using p-b token - based on quick_*.py approach."""
        try:
            self.logger.info("🔐 Logging in to Poe.com...")
            
            # Navigate to Poe.com first
            driver.get("https://poe.com")
            time.sleep(3)
            
            # Add both p-b and p-lat cookies if available
            cookies_to_set = [
                {'name': 'p-b', 'value': self.p_b_token, 'domain': '.poe.com'},
            ]
            
            # Try to add p-lat token if we have one (from config)
            try:
                config_files = ["config/config.json", "config/poe_tokens.json"]
                for config_file in config_files:
                    if os.path.exists(config_file):
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                        p_lat_token = config.get('p_lat') or config.get('p-lat')
                        if p_lat_token:
                            cookies_to_set.append({
                                'name': 'p-lat', 
                                'value': p_lat_token, 
                                'domain': '.poe.com'
                            })
                        break
            except:
                pass  # p-lat is optional
            
            # Set cookies
            for cookie in cookies_to_set:
                try:
                    driver.add_cookie(cookie)
                    self.logger.info(f"✅ Added cookie: {cookie['name']}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to add cookie {cookie['name']}: {e}")
            
            # Refresh to apply cookies
            driver.refresh()
            time.sleep(5)
            
            # Wait for page to load and check if we're logged in
            # Look for elements that indicate we're on the main Poe page
            login_indicators = [
                "div[class*='ChatMessage']",  # Chat messages
                "div[class*='sidebar']",      # Sidebar with conversations
                "a[href*='/chat/']",          # Conversation links
                "[data-testid*='conversation']", # Conversation elements
                "div[class*='conversation']", # Any conversation div
            ]
            
            logged_in = False
            for selector in login_indicators:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.info(f"✅ Found login indicator: {selector}")
                    logged_in = True
                    break
                except TimeoutException:
                    continue
            
            if logged_in:
                self.logger.info("✅ Successfully logged in to Poe.com")
                return True
            else:
                # Try alternative check - look for any conversation-related content
                try:
                    # Check if we can find conversation elements with a longer wait
                    driver.implicitly_wait(15)
                    elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/chat/']")
                    if elements:
                        self.logger.info(f"✅ Found {len(elements)} conversation links - login successful")
                        return True
                except:
                    pass
                
                self.logger.error("❌ Login failed - no conversation elements found")
                
                # Debug: Print current URL and page title
                self.logger.info(f"Current URL: {driver.current_url}")
                self.logger.info(f"Page title: {driver.title}")
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Login failed with exception: {e}")
            return False

    def scroll_to_load_all_conversations(self, driver: webdriver.Chrome) -> List[Dict]:
        """Scroll through the conversation list to load ALL conversations."""
        self.logger.info("📜 Starting infinite scroll to load all conversations...")
        
        conversations = []
        last_height = 0
        scroll_pause_time = 2
        no_new_content_count = 0
        max_no_new_content = 3
        
        # Find the scrollable container
        try:
            # Try different possible selectors for the conversation list container
            container_selectors = [
                "[data-testid='conversation-list']",
                "[aria-label*='conversation']",
                "div[class*='conversation']",
                "div[class*='sidebar']",
                "aside",
                ".sidebar"
            ]
            
            container = None
            for selector in container_selectors:
                try:
                    container = driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.info(f"📍 Found conversation container: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not container:
                self.logger.warning("⚠️ No specific container found, using document body")
                container = driver.find_element(By.TAG_NAME, "body")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to find scrollable container: {e}")
            return []

        while True:
            self.stats['scroll_iterations'] += 1
            self.logger.info(f"🔄 Scroll iteration {self.stats['scroll_iterations']}")
            
            # Get current conversations before scrolling
            current_conversations = self.extract_visible_conversations(driver)
            
            # Add new conversations to our list
            new_found = 0
            for conv in current_conversations:
                if not any(existing['url'] == conv['url'] for existing in conversations):
                    conversations.append(conv)
                    new_found += 1
            
            if new_found > 0:
                self.logger.info(f"📝 Found {new_found} new conversations (Total: {len(conversations)})")
                no_new_content_count = 0
            else:
                no_new_content_count += 1
                self.logger.info(f"⏳ No new conversations found ({no_new_content_count}/{max_no_new_content})")
            
            # Check if we should stop scrolling
            if no_new_content_count >= max_no_new_content:
                self.logger.info("🛑 No new content after multiple scrolls - stopping")
                break
            
            # Scroll down
            try:
                # Method 1: Scroll the container
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                    container
                )
                time.sleep(scroll_pause_time)
                
                # Method 2: Also try page-level scroll as backup
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)
                
                # Method 3: Use keyboard shortcut as final attempt
                ActionChains(driver).send_keys_to_element(container, " ").perform()
                time.sleep(1)
                
            except Exception as e:
                self.logger.warning(f"⚠️ Scroll method failed: {e}")
                # Fallback: simple page scroll
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(scroll_pause_time)
            
            # Check for "Load more" or similar buttons
            try:
                load_more_selectors = [
                    "button[aria-label*='load']",
                    "button[aria-label*='more']",
                    "button:contains('Load more')",
                    "button:contains('Show more')",
                    ".load-more",
                    ".show-more"
                ]
                
                for selector in load_more_selectors:
                    try:
                        load_more_btn = driver.find_element(By.CSS_SELECTOR, selector)
                        if load_more_btn.is_displayed() and load_more_btn.is_enabled():
                            self.logger.info("🔘 Clicking 'Load More' button")
                            driver.execute_script("arguments[0].click();", load_more_btn)
                            time.sleep(3)
                            break
                    except NoSuchElementException:
                        continue
                        
            except Exception as e:
                pass  # No load more button found, continue
            
            # Safety check: don't scroll forever
            if self.stats['scroll_iterations'] > 100:
                self.logger.warning("⚠️ Maximum scroll iterations reached - stopping")
                break
        
        self.logger.info(f"✅ Scroll complete! Found {len(conversations)} total conversations")
        self.stats['total_found'] = len(conversations)
        return conversations

    def extract_visible_conversations(self, driver: webdriver.Chrome) -> List[Dict]:
        """Extract all currently visible conversations from the page."""
        conversations = []
        
        # Multiple selectors to try for conversation items
        conversation_selectors = [
            "a[href*='/chat/']",
            "div[class*='conversation'] a",
            "div[class*='chat'] a",
            "[data-testid*='conversation'] a",
            "li a[href*='/chat/']"
        ]
        
        conversation_elements = []
        for selector in conversation_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    conversation_elements.extend(elements)
                    self.logger.debug(f"Found {len(elements)} elements with selector: {selector}")
            except Exception as e:
                continue
        
        # Remove duplicates based on href
        seen_urls = set()
        unique_elements = []
        for element in conversation_elements:
            try:
                href = element.get_attribute('href')
                if href and href not in seen_urls:
                    seen_urls.add(href)
                    unique_elements.append(element)
            except:
                continue
        
        # Extract conversation data
        for element in unique_elements:
            try:
                href = element.get_attribute('href')
                if not href or '/chat/' not in href:
                    continue
                
                # Extract conversation ID from URL
                conv_id = href.split('/chat/')[-1].split('?')[0]
                
                # Get title (try multiple methods)
                title = ""
                try:
                    # Method 1: Direct text
                    title = element.text.strip()
                    
                    # Method 2: Find title element within the link
                    if not title:
                        title_selectors = [
                            "span[class*='title']",
                            "div[class*='title']",
                            "h3", "h4", "h5",
                            ".conversation-title"
                        ]
                        for title_sel in title_selectors:
                            try:
                                title_elem = element.find_element(By.CSS_SELECTOR, title_sel)
                                title = title_elem.text.strip()
                                if title:
                                    break
                            except:
                                continue
                    
                    # Method 3: Get any text content
                    if not title:
                        title = element.get_attribute('textContent').strip()
                    
                    # Method 4: Use aria-label or title attribute
                    if not title:
                        title = element.get_attribute('aria-label') or element.get_attribute('title')
                    
                except Exception as e:
                    self.logger.debug(f"Failed to extract title: {e}")
                
                # Default title if none found
                if not title:
                    title = f"Conversation {conv_id}"
                
                # Clean up title
                title = title.replace('\n', ' ').strip()
                if len(title) > 200:
                    title = title[:200].strip() + "..."
                
                conversation = {
                    'id': conv_id,
                    'title': title,
                    'url': href,
                    'discovered_at': datetime.now().isoformat()
                }
                
                conversations.append(conversation)
                self.logger.debug(f"📝 Extracted: {title[:50]}...")
                
            except Exception as e:
                self.logger.debug(f"Failed to extract conversation data: {e}")
                continue
        
        return conversations

    def extract_all_conversations(self) -> bool:
        """Main method to extract all conversations with infinite scroll."""
        self.stats['start_time'] = datetime.now()
        self.logger.info("🚀 Starting enhanced conversation extraction...")
        
        driver = None
        try:
            # Setup driver
            driver = self.setup_driver()
            
            # Login
            if not self.login_to_poe(driver):
                return False
            
            # Navigate to conversations/chats page
            self.logger.info("📂 Navigating to conversations page...")
            driver.get("https://poe.com")
            time.sleep(5)
            
            # Scroll and extract all conversations
            conversations = self.scroll_to_load_all_conversations(driver)
            
            if not conversations:
                self.logger.error("❌ No conversations found!")
                return False
            
            # Store conversations in database
            self.logger.info(f"💾 Storing {len(conversations)} conversations in database...")
            
            for conv_data in conversations:
                try:
                    # Check if conversation already exists
                    existing = self.db.get_conversation_by_id(conv_data['id'])
                    
                    if existing:
                        # Update URL if it's missing or different
                        if not existing.url or existing.url != conv_data['url']:
                            existing.url = conv_data['url']
                            self.db.update_conversation(existing)
                            self.stats['updated_conversations'] += 1
                            self.logger.debug(f"📝 Updated URL for: {conv_data['title'][:50]}...")
                    else:
                        # Create new conversation record
                        conversation = Conversation(
                            id=conv_data['id'],
                            title=conv_data['title'],
                            url=conv_data['url'],
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                            message_count=0,
                            content="",  # Will be filled by content extraction later
                            bot_name="",
                            tags=[]
                        )
                        
                        self.db.add_conversation(conversation)
                        self.stats['new_conversations'] += 1
                        self.logger.debug(f"✅ Added new: {conv_data['title'][:50]}...")
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to store conversation {conv_data.get('id', 'unknown')}: {e}")
                    self.stats['errors'] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Extraction failed: {e}")
            return False
            
        finally:
            if driver:
                driver.quit()
            
            self.stats['end_time'] = datetime.now()
            self.print_final_stats()

    def print_final_stats(self):
        """Print final extraction statistics."""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*60)
        print("📊 EXTRACTION COMPLETE - FINAL STATISTICS")
        print("="*60)
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"🔄 Scroll iterations: {self.stats['scroll_iterations']}")
        print(f"📝 Total conversations found: {self.stats['total_found']}")
        print(f"🆕 New conversations added: {self.stats['new_conversations']}")
        print(f"📝 Conversations updated: {self.stats['updated_conversations']}")
        print(f"❌ Errors encountered: {self.stats['errors']}")
        
        if duration > 0:
            rate = self.stats['total_found'] / duration
            print(f"⚡ Extraction rate: {rate:.1f} conversations/second")
        
        print("="*60)

def main():
    """Main execution function."""
    import sys
    import os
    
    # Load configuration - check multiple possible locations
    config_files = [
        "config/config.json",
        "config/poe_tokens.json"
    ]
    
    config = None
    config_path = None
    
    for file_path in config_files:
        if os.path.exists(file_path):
            config_path = file_path
            break
    
    if not config_path:
        print("❌ Configuration file not found.")
        print("💡 Looking for:")
        for file_path in config_files:
            print(f"   - {file_path}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✅ Loaded configuration from: {config_path}")
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        sys.exit(1)
    
    # Get p-b token (handle different key formats)
    p_b_token = config.get('p_b_token') or config.get('p-b')
    
    if not p_b_token:
        print("❌ No p-b token found in configuration.")
        print("💡 Expected keys: 'p_b_token' or 'p-b'")
        print(f"💡 Found keys: {list(config.keys())}")
        sys.exit(1)
    
    print(f"🔑 Using p-b token: {p_b_token[:20]}...")
    
    # Create extractor and run
    extractor = EnhancedPoeExtractor(
        p_b_token=p_b_token,
        headless=True,  # Set to False for debugging
        db_path="storage/conversations.db"
    )
    
    success = extractor.extract_all_conversations()
    
    if success:
        print("✅ Extraction completed successfully!")
        sys.exit(0)
    else:
        print("❌ Extraction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()