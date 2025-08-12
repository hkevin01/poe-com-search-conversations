#!/usr/bin/env python3
"""
Test script for the Setup Wizard and Token Detection functionality

This script tests the setup wizard components to ensure they work correctly
without requiring the full GUI application.
"""

import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from gui.setup_wizard import BrowserDetector, show_setup_wizard


def test_browser_detection():
    """Test browser detection functionality"""
    print("Testing Browser Detection...")
    print("-" * 40)
    
    detector = BrowserDetector()
    available_browsers = detector.get_available_browsers()
    
    print(f"System: {detector.system}")
    print(f"Available browsers: {len(available_browsers)}")
    
    for browser in available_browsers:
        print(f"  - {browser['name']}: {browser['path']}")
        
        # Try to extract cookies (safely)
        try:
            cookies = detector.extract_poe_cookies(browser['id'])
            if cookies:
                print(f"    Found {len(cookies)} cookies")
                if 'p-b' in cookies:
                    token = cookies['p-b']
                    masked_token = token[:8] + "..." + token[-8:] if len(token) > 16 else token
                    print(f"    ✅ Valid p-b token found: {masked_token}")
                else:
                    print("    ❌ No p-b token found")
            else:
                print("    No cookies extracted")
        except Exception as e:
            print(f"    Error: {e}")
    
    print()


def test_setup_wizard():
    """Test setup wizard dialog"""
    print("Testing Setup Wizard Dialog...")
    print("-" * 40)
    
    app = QApplication(sys.argv)
    
    try:
        config = show_setup_wizard()
        
        if config:
            print("✅ Setup wizard completed successfully!")
            print("Configuration:")
            for key, value in config.items():
                if key == 'tokens' and value:
                    print(f"  {key}: {len(value)} browser token(s)")
                elif key == 'manual_token' and value:
                    masked_token = value[:8] + "..." + value[-8:] if len(value) > 16 else value
                    print(f"  {key}: {masked_token}")
                else:
                    print(f"  {key}: {value}")
        else:
            print("❌ Setup wizard was cancelled")
    
    except Exception as e:
        print(f"❌ Error running setup wizard: {e}")
    
    # Don't call app.exec() in test mode
    print()


def main():
    """Run all tests"""
    print("🚀 Poe.com Conversation Manager - Setup Wizard Tests")
    print("=" * 60)
    print()
    
    # Test 1: Browser Detection
    test_browser_detection()
    
    # Test 2: Setup Wizard (optional - requires GUI)
    response = input("Would you like to test the setup wizard GUI? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        test_setup_wizard()
    else:
        print("Skipping GUI test.")
    
    print("✅ Tests completed!")


if __name__ == "__main__":
    main()
