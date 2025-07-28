#!/usr/bin/env python3
"""
Fixed Enhanced Poe.com Conversation Extractor
Based on working quick_*.py approach with infinite scroll
"""

import json
import time
import logging
import os
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from database import ConversationDatabase, Conversation


class FixedPoeExtractor:
    """Simplified extractor based on working quick_*.py approach."""
    
    def __init__(self, p_b_token: str, p_lat_token: str = None, headless: bool = True):
        self.p_b_token = p_b_token
        self.p_lat_token = p_lat_token
        self.headless = headless
        self.db = ConversationDatabase("storage/conversations.db")
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'total_found': 0,
            'new_conversations': 0,
            'updated_conversations': 0,
            'errors': 0
        }

    def setup_driver(self):
        """Setup Chrome driver - based on working quick_*.py approach."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        return driver

    def login_to_poe(self, driver):
        """Login using cookies - exactly like quick_*.py files."""
        try:
            self.logger.info("🔐 Logging in to Poe.com...")
            
            # Go to Poe.com
            driver.get("https://poe.com")
            time.sleep(3)
            
            # Add p-b cookie
            driver.add_cookie({
                'name': 'p-b',
                'value': self.p_b_token,
                'domain': '.poe.com'
            })
            
            # Add p-lat cookie if available
            if self.p_lat_token:
                driver.add_cookie({
                    'name': 'p-lat',
                    'value': self.p_lat_token,
                    'domain': '.poe.com'
                })
            
            # Refresh to apply cookies
            driver.refresh()
            time.sleep(5)
            
            # Simple check - look for any conversation links
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/chat/']"))
                )
                self.logger.info("✅ Successfully logged in!")
                return True
            except TimeoutException:
                self.logger.error("❌ Login failed - no conversation links found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Login error: {e}")
            return False

    def extract_conversations_from_page(self, driver):
        """Extract conversation data from current page."""
        conversations = []
        
        try:
            # Find all conversation links
            elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/chat/']")
            self.logger.info(f"📝 Found {len(elements)} conversation links on page")
            
            for element in elements:
                try:
                    href = element.get_attribute('href')
                    if not href or '/chat/' not in href:
                        continue
                    
                    # Extract conversation ID
                    conv_id = href.split('/chat/')[-1].split('?')[0]
                    
                    # Get title
                    title = element.text.strip()
                    if not title:
                        title = f"Conversation {conv_id}"
                    
                    # Clean title
                    title = title.replace('\n', ' ').strip()[:200]
                    
                    conversations.append({
                        'id': conv_id,
                        'title': title,
                        'url': href
                    })
                    
                except Exception as e:
                    self.logger.debug(f"Failed to extract conversation: {e}")
                    continue
            
            return conversations
            
        except Exception as e:
            self.logger.error(f"❌ Failed to extract conversations: {e}")
            return []

    def scroll_and_load_all(self, driver):
        """Scroll to load all conversations - targeting the correct scroll container."""
        self.logger.info("📜 Starting scroll to load all conversations...")
        
        all_conversations = []
        scroll_count = 0
        no_new_content_count = 0
        
        # Try to find the main scroll container
        scroll_container = None
        container_selectors = [
            ".MainColumn_scrollSectionOverflow__FbPqw",  # Your specific selector
            "[class*='MainColumn_scrollSectionOverflow']",
            "[class*='scrollSectionOverflow']",
            "[class*='MainColumn']",
            "div[class*='sidebar']",
            "aside",
            "main"
        ]
        
        for selector in container_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    scroll_container = elements[0]
                    self.logger.info(f"✅ Found scroll container: {selector}")
                    break
            except Exception as e:
                self.logger.debug(f"Selector {selector} not found: {e}")
                continue
        
        if not scroll_container:
            self.logger.warning("⚠️ No specific scroll container found, using document body")
        
        while no_new_content_count < 3 and scroll_count < 50:
            scroll_count += 1
            self.logger.info(f"🔄 Scroll iteration {scroll_count}")
            
            # Extract current conversations
            current_conversations = self.extract_conversations_from_page(driver)
            
            # Add new ones
            new_found = 0
            for conv in current_conversations:
                if not any(existing['id'] == conv['id'] for existing in all_conversations):
                    all_conversations.append(conv)
                    new_found += 1
            
            if new_found > 0:
                self.logger.info(f"📝 Found {new_found} new conversations (Total: {len(all_conversations)})")
                no_new_content_count = 0
            else:
                no_new_content_count += 1
                self.logger.info(f"⏳ No new conversations found ({no_new_content_count}/3)")
            
            # Scroll down using different methods
            try:
                if scroll_container:
                    # Method 1: Scroll the specific container
                    driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                        scroll_container
                    )
                    self.logger.debug("📜 Scrolled container element")
                    time.sleep(2)
                    
                    # Method 2: Also scroll page as backup
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    self.logger.debug("📜 Scrolled page body")
                    time.sleep(1)
                else:
                    # Fallback: page scroll only
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                # Method 3: Try keyboard scrolling on the container
                if scroll_container:
                    try:
                        from selenium.webdriver.common.action_chains import ActionChains
                        from selenium.webdriver.common.keys import Keys
                        
                        ActionChains(driver).move_to_element(scroll_container).click().perform()
                        ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
                        time.sleep(1)
                        
                    except Exception as e:
                        self.logger.debug(f"Keyboard scroll failed: {e}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Scroll failed: {e}")
                # Ultimate fallback
                try:
                    driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(2)
                except:
                    break
        
        self.logger.info(f"✅ Scroll complete! Found {len(all_conversations)} total conversations")
        return all_conversations

    def store_conversations(self, conversations):
        """Store conversations in database with proper error handling."""
        self.logger.info(f"💾 Storing {len(conversations)} conversations...")
        
        for conv_data in conversations:
            try:
                # Check if exists using a safer method
                try:
                    existing = self.db.get_conversation_by_id(conv_data['id'])
                except:
                    existing = None
                
                if existing:
                    # Update URL if missing and we have update method
                    if hasattr(self.db, 'update_conversation'):
                        if not hasattr(existing, 'url') or not existing.url or existing.url != conv_data['url']:
                            existing.url = conv_data['url']
                            self.db.update_conversation(existing)
                            self.stats['updated_conversations'] += 1
                    else:
                        # Fallback - just log that we found existing
                        self.logger.info(f"📋 Found existing conversation: {conv_data['title'][:50]}...")
                else:
                    # Create new conversation with error handling
                    try:
                        conversation = Conversation(
                            id=conv_data['id'],
                            title=conv_data['title'],
                            url=conv_data.get('url', ''),  # Safe URL access
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                            message_count=0,
                            content="",
                            bot_name="",
                            tags=[]
                        )
                        
                        self.db.add_conversation(conversation)
                        self.stats['new_conversations'] += 1
                        
                    except Exception as e:
                        # If URL field doesn't exist in schema, try without it
                        self.logger.warning(f"⚠️ Trying without URL field: {e}")
                        try:
                            conversation = Conversation(
                                id=conv_data['id'],
                                title=conv_data['title'],
                                created_at=datetime.now(),
                                updated_at=datetime.now(),
                                message_count=0,
                                content="",
                                bot_name="",
                                tags=[]
                            )
                            
                            self.db.add_conversation(conversation)
                            self.stats['new_conversations'] += 1
                            
                        except Exception as e2:
                            self.logger.error(f"❌ Failed to store conversation {conv_data['id']}: {e2}")
                            self.stats['errors'] += 1
                        
            except Exception as e:
                self.logger.error(f"❌ Failed to process conversation {conv_data['id']}: {e}")
                self.stats['errors'] += 1

    def run_extraction(self):
        """Run the complete extraction process."""
        self.logger.info("🚀 Starting Poe.com conversation extraction...")
        
        driver = None
        try:
            # Setup
            driver = self.setup_driver()
            
            # Login
            if not self.login_to_poe(driver):
                return False
            
            # Extract all conversations
            conversations = self.scroll_and_load_all(driver)
            self.stats['total_found'] = len(conversations)
            
            if not conversations:
                self.logger.error("❌ No conversations found!")
                return False
            
            # Store in database
            self.store_conversations(conversations)
            
            # Print stats
            print("\n" + "="*60)
            print("📊 EXTRACTION COMPLETE!")
            print("="*60)
            print(f"📝 Total found: {self.stats['total_found']}")
            print(f"🆕 New conversations: {self.stats['new_conversations']}")
            print(f"📝 Updated conversations: {self.stats['updated_conversations']}")
            print(f"❌ Errors: {self.stats['errors']}")
            print("="*60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Extraction failed: {e}")
            return False
            
        finally:
            if driver:
                driver.quit()


def main():
    """Main function."""
    # Load tokens
    config_files = ["config/config.json", "config/poe_tokens.json"]
    
    config = None
    for config_file in config_files:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"✅ Loaded config from {config_file}")
            break
    
    if not config:
        print("❌ No config file found!")
        return 1
    
    # Get tokens
    p_b_token = config.get('p_b_token') or config.get('p-b')
    p_lat_token = config.get('p_lat_token') or config.get('p-lat')
    
    if not p_b_token:
        print("❌ No p-b token found!")
        return 1
    
    print(f"🔑 Using p-b token: {p_b_token[:20]}...")
    
    # Run extraction
    extractor = FixedPoeExtractor(
        p_b_token=p_b_token,
        p_lat_token=p_lat_token,
        headless=True
    )
    
    success = extractor.run_extraction()
    
    if success:
        print("✅ Extraction completed successfully!")
        return 0
    else:
        print("❌ Extraction failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())