#!/usr/bin/env python3
"""
Quick Conversation Getter - Enhanced Phase 2 
Gets first 10 conversations and extracts full content from each.
Stores in SQLite database for immediate GUI access.
"""

import time
import json
import os
import sys
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import get_config_path, get_project_root
    from database import ConversationDatabase, Conversation
    DEFAULT_CONFIG_PATH = get_config_path()
    PROJECT_ROOT = get_project_root()
except ImportError:
    # Fallback paths
    DEFAULT_CONFIG_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "config", "poe_tokens.json"
    )
    PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
    sys.path.append(PROJECT_ROOT)
    from src.database import ConversationDatabase, Conversation


def setup_browser(headless=True):
    """Set up Chrome browser with optimized options."""
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=opts)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.implicitly_wait(10)
    return driver


def load_tokens(config_path):
    """Load authentication tokens from JSON config."""
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        tokens = json.load(f)
    if "p-b" not in tokens or not tokens["p-b"]:
        raise KeyError(f"Missing required token 'p-b' in {config_path}")
    return tokens


def set_cookies(driver, tokens):
    """Set authentication cookies and navigate to chats."""
    print("🍪 Setting authentication cookies...")
    driver.get("https://poe.com")
    time.sleep(2)

    # Set p-b cookie (required)
    driver.add_cookie({
        "name": "p-b",
        "value": tokens["p-b"],
        "domain": "poe.com",
        "path": "/",
        "secure": True
    })
    
    # Set optional cookies
    if tokens.get("p-lat"):
        driver.add_cookie({
            "name": "p-lat",
            "value": tokens["p-lat"],
            "domain": "poe.com",
            "path": "/",
            "secure": True
        })
    
    if tokens.get("formkey"):
        driver.add_cookie({
            "name": "formkey",
            "value": tokens["formkey"],
            "domain": "poe.com",
            "path": "/",
            "secure": True
        })

    # Navigate to chats page
    driver.get("https://poe.com/chats")
    time.sleep(3)
    print("✅ Authentication cookies set")


def get_conversation_list(driver, limit=10):
    """Get the first N conversations from the chats page."""
    print(f"📋 Getting first {limit} conversations...")
    
    # Scroll a bit to load initial conversations
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    
    conversations = []
    
    # Find conversation links
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/chat/']")[:limit]
    
    for idx, link in enumerate(links, 1):
        try:
            href = link.get_attribute("href")
            title = link.text.strip() or f"Conversation {idx}"
            
            # Extract conversation ID from URL
            poe_id = href.split('/chat/')[-1] if '/chat/' in href else f"unknown_{idx}"
            
            conversations.append({
                "poe_id": poe_id,
                "title": title[:100],  # Limit title length
                "url": href,
                "index": idx
            })
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to extract conversation {idx}: {e}")
            continue
    
    print(f"✅ Found {len(conversations)} conversations")
    return conversations


def extract_conversation_content(driver, conversation_info):
    """Extract full content from a single conversation."""
    print(f"📄 Extracting content: {conversation_info['title']}")
    
    try:
        driver.get(conversation_info["url"])
        
        # Wait for conversation to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='Message'], [data-testid*='message'], .ChatMessage"))
        )
        time.sleep(2)
        
        # Scroll to load all messages (scroll up to get older messages)
        print("   📜 Loading all messages...")
        last_height = 0
        scroll_attempts = 0
        max_attempts = 10
        
        while scroll_attempts < max_attempts:
            current_height = driver.execute_script("return document.body.scrollHeight")
            if current_height == last_height:
                break
            
            # Scroll to top to load older messages
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1.5)
            last_height = current_height
            scroll_attempts += 1
        
        # Extract messages using multiple selectors
        messages = []
        
        # Try different message selectors
        message_selectors = [
            "[class*='Message']",
            "[data-testid*='message']", 
            ".ChatMessage",
            "[class*='chat'] [class*='message']",
            "div[class*='Message_messageRow']"
        ]
        
        message_elements = []
        for selector in message_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                message_elements = elements
                print(f"   ✅ Found {len(elements)} messages using selector: {selector}")
                break
        
        if not message_elements:
            print("   ⚠️  No messages found with standard selectors, trying fallback...")
            # Fallback: get all text content
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if body_text.strip():
                messages.append({
                    "sender": "unknown",
                    "content": body_text[:1000] + "..." if len(body_text) > 1000 else body_text,
                    "timestamp": datetime.now().isoformat()
                })
        else:
            # Process found message elements
            for i, msg_elem in enumerate(message_elements):
                try:
                    text_content = msg_elem.text.strip()
                    if not text_content or len(text_content) < 3:
                        continue
                    
                    # Try to determine sender (heuristic approach)
                    is_user = any(keyword in msg_elem.get_attribute("class").lower() 
                                for keyword in ["user", "human", "you"] 
                                if msg_elem.get_attribute("class"))
                    
                    # Alternative detection methods
                    if not is_user:
                        parent_classes = msg_elem.find_element(By.XPATH, "..").get_attribute("class").lower()
                        is_user = "user" in parent_classes or "human" in parent_classes
                    
                    sender = "user" if is_user else "bot"
                    
                    messages.append({
                        "sender": sender,
                        "content": text_content,
                        "timestamp": datetime.now().isoformat(),
                        "message_index": i
                    })
                    
                except Exception as e:
                    print(f"     ⚠️  Warning: Failed to process message {i}: {e}")
                    continue
        
        # Try to detect bot name
        bot_name = "Unknown Bot"
        try:
            # Look for bot indicators in page title or headers
            title_elem = driver.find_element(By.TAG_NAME, "title")
            page_title = title_elem.get_attribute("innerHTML") if title_elem else ""
            
            # Look for common bot names
            bot_indicators = ["claude", "gpt", "chatgpt", "assistant", "ai"]
            for indicator in bot_indicators:
                if indicator.lower() in page_title.lower():
                    bot_name = indicator.title()
                    break
            
            # Try to find bot name in page elements
            bot_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='bot'], [class*='assistant'], h1, h2")
            for elem in bot_elements:
                text = elem.text.strip()
                if text and len(text) < 50 and any(word in text.lower() for word in ["claude", "gpt", "assistant"]):
                    bot_name = text
                    break
                    
        except Exception as e:
            print(f"     ⚠️  Could not detect bot name: {e}")
        
        print(f"   ✅ Extracted {len(messages)} messages, Bot: {bot_name}")
        
        return {
            "messages": messages,
            "bot_name": bot_name,
            "message_count": len(messages)
        }
        
    except TimeoutException:
        print(f"   ❌ Timeout loading conversation: {conversation_info['title']}")
        return None
    except Exception as e:
        print(f"   ❌ Error extracting content: {e}")
        return None


def save_to_database(conversation_info, content_data, db):
    """Save conversation to database, avoiding duplicates."""
    try:
        # Check if conversation already exists
        if db.conversation_exists(conversation_info["poe_id"]):
            print(f"   ⚠️  Conversation already exists in database, skipping: {conversation_info['poe_id']}")
            return None
        
        # Create Conversation object
        conversation = Conversation(
            poe_id=conversation_info["poe_id"],
            title=conversation_info["title"],
            url=conversation_info["url"],
            bot_name=content_data["bot_name"] if content_data else "Unknown",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            message_count=content_data["message_count"] if content_data else 0,
            content=json.dumps(content_data["messages"], ensure_ascii=False) if content_data else "",
            tags=[],  # Will be added later
            metadata={"extraction_method": "quick_getter", "extraction_date": datetime.now().isoformat()}
        )
        
        # Save to database
        conv_id = db.add_conversation(conversation)
        print(f"   💾 Saved to database with ID: {conv_id}")
        return conv_id
        
    except Exception as e:
        print(f"   ❌ Database save error: {e}")
        return None


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Quick Conversation Getter with Database Storage")
    parser.add_argument(
        "--config", "-c",
        default=DEFAULT_CONFIG_PATH,
        help="Path to your poe_tokens.json"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="Number of conversations to extract (default: 10)"
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="Show browser window for debugging"
    )
    parser.add_argument(
        "--database", "-d",
        default=os.path.join(PROJECT_ROOT, "storage", "conversations.db"),
        help="Database file path"
    )
    
    args = parser.parse_args()
    
    print("🚀 Quick Conversation Getter - Enhanced Phase 2")
    print("=" * 60)
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"🔑 Config path: {args.config}")
    print(f"💾 Database path: {args.database}")
    print(f"📊 Limit: {args.limit} conversations")
    
    # Create storage directory
    storage_dir = os.path.dirname(args.database)
    os.makedirs(storage_dir, exist_ok=True)
    
    try:
        # Load tokens
        tokens = load_tokens(args.config)
        print(f"🔑 Loaded tokens, p-b: {tokens['p-b'][:16]}...")
        
        # Initialize database
        db = ConversationDatabase(args.database)
        print("💾 Database initialized")
        
        # Setup browser
        driver = setup_browser(headless=not args.no_headless)
        print("🌐 Browser initialized")
        
        # Authenticate
        set_cookies(driver, tokens)
        
        # Get conversation list
        conversation_list = get_conversation_list(driver, args.limit)
        
        if not conversation_list:
            print("❌ No conversations found")
            return 1
        
        # Filter out conversations that already exist in database
        print(f"🔍 Checking for existing conversations in database...")
        new_conversations = []
        existing_count = 0
        
        for conv_info in conversation_list:
            if db.conversation_exists(conv_info["poe_id"]):
                print(f"   ⏭️  Skipping existing: {conv_info['title'][:50]}...")
                existing_count += 1
            else:
                new_conversations.append(conv_info)
        
        print(f"📊 Found {existing_count} existing, {len(new_conversations)} new conversations")
        
        if not new_conversations:
            print("✅ All conversations already exist in database")
            stats = db.get_stats()
            print(f"📊 Database contains {stats['total_conversations']} total conversations")
            return 0
        
        # Process each NEW conversation only
        successful_extractions = 0
        
        for i, conv_info in enumerate(new_conversations, 1):
            print(f"\n📄 Processing {i}/{len(new_conversations)}: {conv_info['title']}")
            
            # Extract content
            content_data = extract_conversation_content(driver, conv_info)
            
            # Save to database (will skip if already exists)
            if save_to_database(conv_info, content_data, db):
                successful_extractions += 1
            
            # Small delay between requests
            time.sleep(2)
        
        # Show results
        print(f"\n🎉 Processing complete!")
        print(f"✅ Successfully extracted: {successful_extractions}/{len(new_conversations)} new conversations")
        if existing_count > 0:
            print(f"⏭️  Skipped: {existing_count} existing conversations")
        
        # Show database stats
        stats = db.get_stats()
        print(f"📊 Database now contains {stats['total_conversations']} total conversations")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Config file error: {e}")
        print("💡 Create config: cp config/poe_tokens.json.example config/poe_tokens.json")
        return 1
    except KeyError as e:
        print(f"❌ Missing token: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'driver' in locals():
            driver.quit()
            print("🔒 Browser closed")


if __name__ == "__main__":
    sys.exit(main())