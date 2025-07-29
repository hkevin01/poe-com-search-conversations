#!/usr/bin/env python3
"""
Test Extraction Setup
Quick test to verify tokens and login work before full extraction
"""

import os
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_tokens_and_login():
    """Test if our tokens work for login."""
    print("🧪 TESTING POE.COM LOGIN")
    print("="*50)
    
    # Get project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Load tokens
    config_files = [
        os.path.join(project_root, "config/config.json"), 
        os.path.join(project_root, "config/poe_tokens.json")
    ]
    
    config = None
    config_file = None
    for file_path in config_files:
        if os.path.exists(file_path):
            config_file = file_path
            with open(file_path, 'r') as f:
                config = json.load(f)
            break
    
    if not config:
        print("❌ No config file found!")
        return False
    
    print(f"✅ Using config: {config_file}")
    
    # Get tokens
    p_b_token = config.get('p_b_token') or config.get('p-b')
    p_lat_token = config.get('p_lat_token') or config.get('p-lat')
    
    if not p_b_token:
        print("❌ No p-b token found!")
        return False
    
    print(f"🔑 p-b token: {p_b_token[:20]}...")
    if p_lat_token:
        print(f"🔑 p-lat token: {p_lat_token[:20]}...")
    else:
        print("⚠️ No p-lat token (this is optional)")
    
    # Test login
    print("\n🚀 Testing login...")
    
    # Setup driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        
        # Go to Poe
        print("📂 Navigating to Poe.com...")
        driver.get("https://poe.com")
        
        # Add cookies
        print("🍪 Adding authentication cookies...")
        driver.add_cookie({
            'name': 'p-b',
            'value': p_b_token,
            'domain': '.poe.com'
        })
        
        if p_lat_token:
            driver.add_cookie({
                'name': 'p-lat',
                'value': p_lat_token,
                'domain': '.poe.com'
            })
        
        # Refresh
        print("🔄 Refreshing page...")
        driver.refresh()
        
        # Check for conversation links
        print("🔍 Looking for conversation links...")
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/chat/']"))
            )
            
            # Count conversations
            elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/chat/']")
            print(f"✅ SUCCESS! Found {len(elements)} conversation links")
            
            # Show first few
            print("\n📝 Sample conversations:")
            for i, element in enumerate(elements[:5]):
                try:
                    title = element.text.strip()[:50]
                    href = element.get_attribute('href')
                    print(f"  {i+1}. {title}... ({href})")
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"❌ LOGIN FAILED: {e}")
            print("💡 This usually means:")
            print("   - Your p-b token has expired")
            print("   - You need to update your tokens")
            print("   - Network connectivity issues")
            return False
    
    except Exception as e:
        print(f"❌ SETUP FAILED: {e}")
        return False
    
    finally:
        if driver:
            driver.quit()


def main():
    """Run the test."""
    success = test_tokens_and_login()
    
    if success:
        print("\n🎉 TEST PASSED!")
        print("✅ Your tokens work and login is successful")
        print("🚀 You can now run: python main.py extract")
        return 0
    else:
        print("\n❌ TEST FAILED!")
        print("💡 Please update your tokens in config/poe_tokens.json")
        print("💡 Get fresh tokens from your browser's developer tools")
        return 1


if __name__ == "__main__":
    sys.exit(main())
