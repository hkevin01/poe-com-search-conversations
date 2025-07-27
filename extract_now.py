#!/usr/bin/env python3
"""
Quick Extractor - Uses existing poe_tokens.json file
Simple wrapper to run extraction with your current token setup
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def main():
    """Run extraction using existing token file."""
    print("🚀 QUICK POE.COM CONVERSATION EXTRACTOR")
    print("Using your existing poe_tokens.json configuration")
    print("="*60)
    
    # Check if token file exists
    token_file = "config/poe_tokens.json"
    if not os.path.exists(token_file):
        print(f"❌ Token file not found: {token_file}")
        print("💡 Please ensure your poe_tokens.json file exists")
        return 1
    
    # Load and validate tokens
    try:
        with open(token_file, 'r') as f:
            tokens = json.load(f)
        
        p_b_token = tokens.get('p-b')
        if not p_b_token:
            print("❌ No 'p-b' token found in poe_tokens.json")
            return 1
        
        print(f"✅ Found p-b token: {p_b_token[:20]}...")
        
    except Exception as e:
        print(f"❌ Error reading token file: {e}")
        return 1
    
    # Create directories
    os.makedirs("storage", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Step 1: Database Migration
    print("\n" + "="*60)
    print("🔄 Step 1: Database Migration")
    print("="*60)
    
    try:
        result = subprocess.run([
            sys.executable, "src/migrate_database.py"
        ], cwd=Path.cwd(), capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode != 0:
            print("❌ Migration failed")
            return 1
        
        print("✅ Database migration completed")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return 1
    
    # Step 2: Run Enhanced Extraction
    print("\n" + "="*60)
    print("🔄 Step 2: Enhanced Extraction")
    print("="*60)
    
    try:
        # Import and run extraction directly
        sys.path.append('src')
        from enhanced_extractor import EnhancedPoeExtractor
        
        extractor = EnhancedPoeExtractor(
            p_b_token=p_b_token,
            headless=True,  # Set to False to see browser
            db_path="storage/conversations.db"
        )
        
        success = extractor.extract_all_conversations()
        
        if not success:
            print("❌ Extraction failed")
            return 1
            
        print("✅ Extraction completed successfully!")
        
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return 1
    
    # Step 3: Show Results
    print("\n" + "="*60)
    print("📊 Step 3: Final Results")
    print("="*60)
    
    try:
        from database import ConversationDatabase
        
        db = ConversationDatabase('storage/conversations.db')
        stats = db.get_stats()
        
        print(f"📝 Total conversations: {stats['total_conversations']}")
        print(f"🤖 Unique bots: {stats['unique_bots']}")
        print(f"💬 Total messages: {stats['total_messages']}")
        print(f"📈 Avg messages per conversation: {stats['avg_messages_per_conversation']:.1f}")
        
        # Show top bots
        print(f"\n🏆 Top 5 Bots:")
        for bot, count in list(stats['bot_distribution'].items())[:5]:
            print(f"   {bot}: {count} conversations")
        
    except Exception as e:
        print(f"⚠️ Could not get final statistics: {e}")
    
    # Success!
    print("\n" + "="*60)
    print("🎉 EXTRACTION COMPLETE!")
    print("="*60)
    print("✅ All conversations extracted with URLs")
    print("🚀 Launch GUI to browse: python main.py launch")
    print("🔍 Search CLI: python src/cli.py")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())