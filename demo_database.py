#!/usr/bin/env python3
"""
Database Demo - Shows how to use the ConversationDatabase class
"""

import json
from datetime import datetime
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import ConversationDatabase, Conversation


def create_sample_data():
    """Create sample conversations for demonstration."""
    return [
        Conversation(
            poe_id="demo_1",
            title="Getting Started with Python",
            url="https://poe.com/chat/demo_1",
            bot_name="Claude",
            content=json.dumps([
                {"sender": "user", "content": "How do I start learning Python?"},
                {"sender": "bot", "content": "Python is a great language to start with! Here are some steps..."},
                {"sender": "user", "content": "What about data structures?"},
                {"sender": "bot", "content": "Python has several built-in data structures like lists, dictionaries..."}
            ]),
            message_count=4,
            tags=["python", "beginner", "tutorial"],
            metadata={"category": "programming", "difficulty": "beginner"}
        ),
        Conversation(
            poe_id="demo_2",
            title="Advanced JavaScript Patterns",
            url="https://poe.com/chat/demo_2",
            bot_name="GPT-4",
            content=json.dumps([
                {"sender": "user", "content": "Tell me about JavaScript closures"},
                {"sender": "bot", "content": "Closures are a fundamental concept in JavaScript..."},
                {"sender": "user", "content": "Can you show an example?"},
                {"sender": "bot", "content": "Sure! Here's a practical example of a closure..."}
            ]),
            message_count=4,
            tags=["javascript", "advanced", "patterns"],
            metadata={"category": "programming", "difficulty": "advanced"}
        ),
        Conversation(
            poe_id="demo_3",
            title="Database Design Best Practices",
            url="https://poe.com/chat/demo_3",
            bot_name="Claude",
            content=json.dumps([
                {"sender": "user", "content": "What are the principles of good database design?"},
                {"sender": "bot", "content": "Good database design follows several key principles..."},
                {"sender": "user", "content": "How do I normalize my database?"},
                {"sender": "bot", "content": "Database normalization involves organizing data to reduce redundancy..."}
            ]),
            message_count=4,
            tags=["database", "design", "normalization"],
            metadata={"category": "database", "difficulty": "intermediate"}
        )
    ]


def main():
    """Demonstrate database functionality."""
    print("🎯 Poe.com Conversation Database Demo")
    print("=" * 50)
    
    # Initialize database
    db_path = "demo_conversations.db"
    db = ConversationDatabase(db_path)
    print(f"📁 Database initialized: {db_path}")
    
    # Add sample data
    print("\n📝 Adding sample conversations...")
    sample_conversations = create_sample_data()
    
    for conv in sample_conversations:
        conv_id = db.add_conversation(conv)
        print(f"   Added: {conv.title} (ID: {conv_id})")
    
    # Show statistics
    print("\n📊 Database Statistics:")
    stats = db.get_stats()
    print(f"   Total conversations: {stats['total_conversations']}")
    print(f"   Unique bots: {stats['unique_bots']}")
    print(f"   Total messages: {stats['total_messages']}")
    print(f"   Average messages per conversation: {stats['avg_messages_per_conversation']}")
    
    # Show bot distribution
    print(f"\n🤖 Bot Distribution:")
    for bot, count in stats['bot_distribution'].items():
        print(f"   {bot}: {count} conversations")
    
    # Demonstrate search
    print(f"\n🔍 Search Examples:")
    
    # Search for Python-related conversations
    python_results = db.search_conversations("Python")
    print(f"   'Python' search: {len(python_results)} results")
    for result in python_results:
        print(f"      - {result.title}")
    
    # Search by bot
    claude_results = db.search_conversations("", {"bot_name": "Claude"})
    print(f"   Claude conversations: {len(claude_results)} results")
    for result in claude_results:
        print(f"      - {result.title}")
    
    # Show all tags
    print(f"\n🏷️  All Tags:")
    all_tags = db.get_all_tags()
    print(f"   {', '.join(all_tags)}")
    
    # Search by tag
    python_tagged = db.get_tagged_conversations("python")
    print(f"   Conversations tagged 'python': {len(python_tagged)}")
    
    # Demonstrate content search
    print(f"\n📄 Content Search:")
    closure_matches = db.search_conversation_content("closures")
    print(f"   'closures' in content: {len(closure_matches)} matches")
    for match in closure_matches:
        print(f"      - {match['conversation_title']}")
        print(f"        Message: {match['matching_message']['content'][:50]}...")
    
    # Export demonstrations
    print(f"\n💾 Export Examples:")
    
    # Export all to JSON
    json_file = db.export_conversations("json", "demo_export.json")
    print(f"   JSON export: {json_file}")
    
    # Export single conversation to Markdown
    sample_conv = sample_conversations[0]
    md_file = db.export_conversation_by_id(sample_conv.poe_id, "markdown")
    print(f"   Single conversation markdown: {md_file}")
    
    # Show database info
    print(f"\n💽 Database Information:")
    db_info = db.get_database_info()
    print(f"   Database size: {db_info['database_size_mb']} MB")
    print(f"   Tables: {', '.join(db_info['tables'])}")
    print(f"   SQLite version: {db_info['sqlite_version']}")
    
    # Demonstrate tag management
    print(f"\n🏷️  Tag Management:")
    success = db.update_conversation_tags(sample_conv.poe_id, ["python", "beginner", "tutorial", "updated"])
    if success:
        updated_conv = db.get_conversation_by_poe_id(sample_conv.poe_id)
        print(f"   Updated tags for '{updated_conv.title}': {updated_conv.tags}")
    
    # Search suggestions
    print(f"\n💡 Search Suggestions:")
    suggestions = db.get_search_suggestions("Java")
    print(f"   Suggestions for 'Java': {suggestions}")
    
    # Show recent conversations
    print(f"\n📅 Recent Conversations:")
    recent = db.get_recent_conversations(2)
    for conv in recent:
        print(f"   - {conv.title} (Updated: {conv.updated_at.strftime('%Y-%m-%d %H:%M')})")
    
    print(f"\n✅ Demo completed! Database saved as: {db_path}")
    print(f"   You can delete it with: rm {db_path}")
    
    # Show cleanup option
    print(f"\n🧹 Cleanup:")
    response = input("Delete demo database and files? (y/N): ").lower().strip()
    if response == 'y':
        # Clean up files
        files_to_remove = [db_path, json_file]
        if md_file:
            files_to_remove.append(md_file)
        
        for file in files_to_remove:
            if file and os.path.exists(file):
                os.unlink(file)
                print(f"   Deleted: {file}")
        print("   Cleanup complete!")
    else:
        print("   Files preserved for your exploration.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()