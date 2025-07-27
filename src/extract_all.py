#!/usr/bin/env python3
"""
Complete Conversation Extraction Pipeline
Runs database migration, enhanced extraction, and shows results
"""

import sys
import os
import subprocess
import json
from pathlib import Path

# Global variable to store config
global_config = None

def run_command(command, description):
    """Run a command and handle the output."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print(f"⚠️ Warnings/Errors:\n{result.stderr}")
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            return True
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def check_prerequisites():
    """Check if all prerequisites are available."""
    print("🔍 Checking prerequisites...")
    
    # Check for multiple possible config files
    config_files = [
        "config/config.json",
        "config/poe_tokens.json"
    ]
    
    config_path = None
    config = None
    
    for file_path in config_files:
        if os.path.exists(file_path):
            config_path = file_path
            print(f"✅ Found configuration file: {file_path}")
            break
    
    if not config_path:
        print("❌ No configuration file found!")
        print("💡 Looking for:")
        for file_path in config_files:
            print(f"   - {file_path}")
        print("💡 Please create a config file with your p-b token.")
        return False
    
    # Check if p-b token is configured
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Handle different token key formats
        p_b_token = config.get('p_b_token') or config.get('p-b')
        
        if not p_b_token:
            print("❌ No p-b token found in configuration.")
            print("💡 Expected keys: 'p_b_token' or 'p-b'")
            print(f"💡 Found keys: {list(config.keys())}")
            return False
            
        print("✅ Configuration found and valid")
        
        # Store the config for later use
        global global_config
        global_config = config
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False
    
    # Check if required directories exist
    os.makedirs("storage", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print("✅ Prerequisites check passed")
    return True

def main():
    """Run the complete extraction pipeline."""
    print("🎯 POE.COM COMPLETE CONVERSATION EXTRACTION")
    print("This will extract ALL conversations from your Poe.com account")
    print("with infinite scroll and store them with URLs in the database.")
    
    if not check_prerequisites():
        return 1
    
    # Step 1: Run database migration
    if not run_command("python migrate_database.py", "Database Migration"):
        print("❌ Database migration failed. Cannot continue.")
        return 1
    
    # Step 2: Run enhanced extraction
    if not run_command("python fixed_extractor.py", "Fixed Conversation Extraction"):
        print("❌ Conversation extraction failed.")
        return 1
    
    # Step 3: Show results
    if not run_command("python -c \"from database import ConversationDatabase; db = ConversationDatabase('storage/conversations.db'); stats = db.get_stats(); print(f'📊 FINAL RESULTS:\\n📝 Total conversations: {stats[\\\"total_conversations\\\"]}\\n🤖 Unique bots: {stats[\\\"unique_bots\\\"]}\\n💬 Total messages: {stats[\\\"total_messages\\\"]}\\n📈 Avg messages per conversation: {stats[\\\"avg_messages_per_conversation\\\"]}')\"", "Database Statistics"):
        print("⚠️ Could not retrieve final statistics")
    
    print("\n" + "="*60)
    print("🎉 EXTRACTION PIPELINE COMPLETE!")
    print("="*60)
    print("✅ All conversations have been extracted and stored")
    print("🔗 Conversation URLs are now stored in the database")
    print("🚀 You can now launch the GUI to browse your conversations:")
    print("   python main.py launch")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())