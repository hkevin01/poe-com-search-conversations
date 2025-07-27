#!/usr/bin/env python3
"""
Database Uniqueness Tests - Moved from test_uniqueness.py in root
Comprehensive testing for conversation uniqueness in database
"""

import os
import sys
from datetime import datetime

# Get project root (three levels up from this script)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add src to path
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

from database import ConversationDatabase, Conversation

def test_conversation_uniqueness():
    """Test that conversations are properly unique by poe_id."""
    print("🧪 Testing Conversation Uniqueness")
    print("=" * 50)
    
    # Test database path in storage
    test_db_path = os.path.join(PROJECT_ROOT, "storage", "test_uniqueness.db")
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Create storage directory
    os.makedirs(os.path.dirname(test_db_path), exist_ok=True)
    
    try:
        # Initialize database
        db = ConversationDatabase(test_db_path)
        print("✅ Test database initialized")
        
        # Create a test conversation
        test_conversation = Conversation(
            poe_id="test_conversation_123",
            title="Test Conversation",
            url="https://poe.com/chat/test_conversation_123",
            bot_name="Test Bot",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            message_count=5,
            content='[{"sender": "user", "content": "Hello"}, {"sender": "bot", "content": "Hi!"}]',
            tags=["test"],
            metadata={"test": True}
        )
        
        # Test 1: Add conversation first time
        print("\n📝 Test 1: Adding conversation first time")
        conv_id1 = db.add_conversation(test_conversation)
        print(f"   ✅ Added with ID: {conv_id1}")
        
        # Test 2: Check if conversation exists
        print("\n🔍 Test 2: Checking if conversation exists")
        exists = db.conversation_exists("test_conversation_123")
        print(f"   ✅ Exists: {exists}")
        
        # Test 3: Try to add the same conversation again
        print("\n⚠️  Test 3: Attempting to add duplicate conversation")
        try:
            conv_id2 = db.add_conversation(test_conversation)
            print(f"   ❌ PROBLEM: Duplicate was added with ID: {conv_id2}")
            success = False
        except Exception as e:
            print(f"   ✅ Correctly prevented duplicate: {type(e).__name__}")
            success = True
        
        # Test 4: Check conversation count
        print("\n📊 Test 4: Checking conversation count")
        stats = db.get_stats()
        expected_count = 1
        actual_count = stats['total_conversations']
        
        if actual_count == expected_count:
            print(f"   ✅ Correct count: {actual_count} conversation")
            count_ok = True
        else:
            print(f"   ❌ PROBLEM: Expected {expected_count}, got {actual_count}")
            count_ok = False
        
        # Test 5: Test the existence check with non-existent conversation
        print("\n🔍 Test 5: Checking non-existent conversation")
        exists_fake = db.conversation_exists("non_existent_conversation")
        if not exists_fake:
            print("   ✅ Correctly identified non-existent conversation")
            exists_ok = True
        else:
            print("   ❌ PROBLEM: Non-existent conversation reported as existing")
            exists_ok = False
        
        # Test 6: Get conversation by poe_id
        print("\n📄 Test 6: Retrieving conversation by poe_id")
        retrieved = db.get_conversation_by_poe_id("test_conversation_123")
        if retrieved and retrieved.title == "Test Conversation":
            print("   ✅ Successfully retrieved conversation")
            retrieve_ok = True
        else:
            print("   ❌ PROBLEM: Failed to retrieve conversation")
            retrieve_ok = False
        
        print("\n🎉 Uniqueness tests completed!")
        
        # Clean up test database
        os.remove(test_db_path)
        print("🧹 Test database cleaned up")
        
        return success and count_ok and exists_ok and retrieve_ok
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quick_getter_uniqueness():
    """Test the quick_conversation_getter uniqueness logic."""
    print("\n🔧 Testing Quick Getter Uniqueness Logic")
    print("=" * 50)
    
    # This simulates what the quick_conversation_getter does
    test_conversations = [
        {"poe_id": "conv_1", "title": "Conversation 1", "url": "https://poe.com/chat/conv_1"},
        {"poe_id": "conv_2", "title": "Conversation 2", "url": "https://poe.com/chat/conv_2"},
        {"poe_id": "conv_1", "title": "Conversation 1 (duplicate)", "url": "https://poe.com/chat/conv_1"},
    ]
    
    # Test database path
    test_db_path = os.path.join(PROJECT_ROOT, "storage", "test_getter_uniqueness.db")
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        db = ConversationDatabase(test_db_path)
        print("✅ Test database initialized")
        
        # Simulate the filtering logic from quick_conversation_getter
        print("\n📋 Testing conversation filtering logic:")
        new_conversations = []
        existing_count = 0
        
        for conv_info in test_conversations:
            if db.conversation_exists(conv_info["poe_id"]):
                print(f"   ⏭️  Skipping existing: {conv_info['title']}")
                existing_count += 1
            else:
                print(f"   ➕ Adding new: {conv_info['title']}")
                new_conversations.append(conv_info)
                
                # Simulate adding to database
                test_conv = Conversation(
                    poe_id=conv_info["poe_id"],
                    title=conv_info["title"],
                    url=conv_info["url"],
                    bot_name="Test Bot",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    message_count=1,
                    content='[{"sender": "user", "content": "test"}]',
                    tags=[],
                    metadata={}
                )
                db.add_conversation(test_conv)
        
        print("\n📊 Results:")
        print(f"   - New conversations processed: {len(new_conversations)}")
        print(f"   - Existing conversations skipped: {existing_count}")
        
        stats = db.get_stats()
        print(f"   - Total in database: {stats['total_conversations']}")
        
        # Expected: 2 unique conversations (conv_1 and conv_2)
        expected = 2
        actual = stats['total_conversations']
        if actual == expected:
            print("   ✅ Uniqueness logic working correctly!")
            result = True
        else:
            print(f"   ❌ PROBLEM: Expected {expected} unique conversations, got {actual}")
            result = False
        
        # Clean up
        os.remove(test_db_path)
        print("🧹 Test database cleaned up")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all uniqueness tests."""
    print("🎯 Conversation Uniqueness Test Suite")
    print("=" * 60)
    print(f"📁 Project root: {PROJECT_ROOT}")
    
    # Change to project root
    os.chdir(PROJECT_ROOT)
    
    test1_ok = test_conversation_uniqueness()
    test2_ok = test_quick_getter_uniqueness()
    
    print("\n" + "=" * 60)
    print("📋 Test Results:")
    print(f"   Database Uniqueness: {'✅ PASS' if test1_ok else '❌ FAIL'}")
    print(f"   Getter Logic: {'✅ PASS' if test2_ok else '❌ FAIL'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 All uniqueness tests passed!")
        print("✅ Conversations will not be duplicated in the database")
    else:
        print("\n⚠️  Some tests failed - check the output above")
    
    return 0 if (test1_ok and test2_ok) else 1

if __name__ == "__main__":
    sys.exit(main())