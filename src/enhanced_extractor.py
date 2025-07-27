#!/usr/bin/env python3
"""
Enhanced Poe.com Conversation Extractor - Phase 2
Builds on quick_list_conversations.py to extract full conversation content.
"""

import time
import json
import os
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from database import ConversationDatabase, Conversation

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('poe_extractor.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

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

def set_cookies(driver, tokens, logger):
    """Navigate to Poe.com and set authentication cookies."""
    logger.info("Setting up authentication cookies...")
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
    for cookie_name in ["p-lat", "formkey"]:
        if tokens.get(cookie_name):
            driver.add_cookie({
                "name": cookie_name,
                "value": tokens[cookie_name],
                "domain": "poe.com",
                "path": "/",
                "secure": True
            })

    # Navigate to chats page
    driver.get("https://poe.com/chats")
    time.sleep(3)
    logger.info("Authentication setup complete")

def extract_conversation_list(driver, logger):
    """Extract conversation list with URLs and metadata."""
    logger.info("Extracting conversation list...")
    
    # Scroll to load all conversations
    last_height = driver.execute_script("return document.body.scrollHeight")
    conversation_count = 0
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Count current conversations
        current_convs = len(driver.find_elements(By.CSS_SELECTOR, "a[href*='/chat/']"))
        if current_convs > conversation_count:
            conversation_count = current_convs
            logger.info(f"Found {conversation_count} conversations so far...")
        
        if new_height == last_height:
            break
        last_height = new_height

    # Extract conversation data
    conversations = []
    conv_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/chat/']")
    
    for idx, link in enumerate(conv_links, 1):
        try:
            href = link.get_attribute("href")
            title = link.text.strip() or f"Conversation {idx}"
            
            # Extract conversation ID from URL
            poe_id = href.split('/chat/')[-1] if '/chat/' in href else f"unknown_{idx}"
            
            conversation = Conversation(
                poe_id=poe_id,
                title=title[:100],  # Limit title length
                url=href,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            conversations.append(conversation)
            
        except Exception as e:
            logger.warning(f"Failed to extract conversation {idx}: {e}")
            continue
    
    logger.info(f"Successfully extracted {len(conversations)} conversations")
    return conversations

def extract_conversation_content(driver, conversation, logger):
    """Extract full content from a single conversation."""
    try:
        logger.info(f"Extracting content for: {conversation.title}")
        driver.get(conversation.url)
        
        # Wait for conversation to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid*='message']"))
        )
        time.sleep(2)
        
        # Scroll to load all messages
        last_height = 0
        while True:
            current_height = driver.execute_script("return document.body.scrollHeight")
            if current_height == last_height:
                break
            driver.execute_script("window.scrollTo(0, 0);")  # Scroll to top
            time.sleep(1)
            last_height = current_height
        
        # Extract messages
        messages = []
        message_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='message']")
        
        for msg_elem in message_elements:
            try:
                # Determine if it's user or bot message
                is_user = "user" in msg_elem.get_attribute("data-testid").lower()
                sender = "user" if is_user else "bot"
                
                # Extract message text
                text = msg_elem.text.strip()
                if text:
                    messages.append({
                        "sender": sender,
                        "content": text,
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.warning(f"Failed to extract message: {e}")
                continue
        
        # Try to detect bot name from page
        bot_name = "Unknown"
        try:
            bot_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid*='bot'], .bot-name, h1")
            for elem in bot_elements:
                text = elem.text.strip()
                if text and len(text) < 50:  # Reasonable bot name length
                    bot_name = text
                    break
        except:
            pass
        
        # Update conversation with extracted content
        conversation.content = json.dumps(messages, ensure_ascii=False)
        conversation.bot_name = bot_name
        conversation.message_count = len(messages)
        conversation.updated_at = datetime.now()
        
        logger.info(f"Extracted {len(messages)} messages from {conversation.title}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to extract content for {conversation.title}: {e}")
        return False

def sync_conversations(driver, db, tokens, logger, full_sync=False):
    """Sync conversations with database (incremental or full)."""
    logger.info(f"Starting {'full' if full_sync else 'incremental'} sync...")
    
    # Set up authentication
    set_cookies(driver, tokens, logger)
    
    # Get conversation list
    conversation_list = extract_conversation_list(driver, logger)
    
    if not conversation_list:
        logger.warning("No conversations found")
        return
    
    # Process conversations
    new_count = 0
    updated_count = 0
    error_count = 0
    
    for conv in conversation_list:
        try:
            # Check if conversation exists in database
            existing = db.search_conversations("", {"poe_id": conv.poe_id})
            
            should_extract = full_sync
            if not existing:
                should_extract = True
                new_count += 1
            elif not full_sync:
                # Skip existing conversations in incremental sync
                continue
            else:
                updated_count += 1
            
            if should_extract:
                # Extract full content
                if extract_conversation_content(driver, conv, logger):
                    db.add_conversation(conv)
                    logger.info(f"Saved: {conv.title}")
                else:
                    error_count += 1
                
                # Small delay between requests
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error processing {conv.title}: {e}")
            error_count += 1
            continue
    
    logger.info(f"Sync complete - New: {new_count}, Updated: {updated_count}, Errors: {error_count}")

def main():
    parser = argparse.ArgumentParser(description="Enhanced Poe Conversation Extractor")
    parser.add_argument(
        "--config", "-c",
        default=os.path.expanduser("~/Projects/poe-search/config/poe_tokens.json"),
        help="Path to your poe_tokens.json"
    )
    parser.add_argument(
        "--database", "-d",
        default="conversations.db",
        help="SQLite database path"
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="Show browser window for debugging"
    )
    parser.add_argument(
        "--full-sync", action="store_true",
        help="Extract content for all conversations (not just new ones)"
    )
    args = parser.parse_args()

    # Set up logging
    logger = setup_logging()
    logger.info("🚀 Enhanced Poe Conversation Extractor - Phase 2")
    
    try:
        # Load configuration
        tokens = load_tokens(args.config)
        logger.info(f"🔑 Loaded tokens, p-b: {tokens['p-b'][:16]}...")
        
        # Set up database
        db = ConversationDatabase(args.database)
        logger.info(f"💾 Database initialized: {args.database}")
        
        # Set up browser
        driver = setup_browser(headless=not args.no_headless)
        logger.info("🌐 Browser initialized")
        
        # Sync conversations
        sync_conversations(driver, db, tokens, logger, args.full_sync)
        
        # Show statistics
        stats = db.get_stats()
        logger.info("📊 Database Statistics:")
        logger.info(f"   Total conversations: {stats['total_conversations']}")
        logger.info(f"   Unique bots: {stats['unique_bots']}")
        logger.info(f"   Total messages: {stats['total_messages']}")
        logger.info(f"   Avg messages per conversation: {stats['avg_messages_per_conversation']}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise
    finally:
        if 'driver' in locals():
            driver.quit()
            logger.info("🔒 Browser closed")

if __name__ == "__main__":
    main()