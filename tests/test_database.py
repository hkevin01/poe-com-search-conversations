#!/usr/bin/env python3
"""
Test suite for database.py - Comprehensive testing of all database functionality
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
import sys

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import ConversationDatabase, Conversation


class TestConversationDatabase(unittest.TestCase):
    """Test cases for ConversationDatabase class."""
    
    def setUp(self):
        """Set up test database for each test."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = ConversationDatabase(self.temp_db.name)
        
        # Create sample conversations for testing
        self.sample_conversations = [
            Conversation(
                poe_id="conv_1",
                title="Python Programming Help",
                url="https://poe.com/chat/conv_1",
                bot_name="Claude",
                content=json.dumps([
                    {"sender": "user", "content": "How do I use Python lists?"},
                    {"sender": "bot", "content": "Python lists are ordered collections..."}
                ]),
                message_count=2,
                tags=["python", "programming"],
                metadata={"difficulty": "beginner"}
            ),
            Conversation(
                poe_id="conv_2",
                title="JavaScript Async/Await",
                url="https://poe.com/chat/conv_2",
                bot_name="GPT-4",
                content=json.dumps([
                    {"sender": "user", "content": "Explain async/await in JavaScript"},
                    {"sender": "bot", "content": "Async/await is syntactic sugar for promises..."}
                ]),
                message_count=2,
                tags=["javascript", "async"],
                metadata={"difficulty": "intermediate"}
            ),
            Conversation(
                poe_id="conv_3",
                title="Database Design Principles",
                url="https://poe.com/chat/conv_3",
                bot_name="Claude",
                content=json.dumps([
                    {"sender": "user", "content": "What are ACID properties?"},
                    {"sender": "bot", "content": "ACID stands for Atomicity, Consistency..."}
                ]),
                message_count=2,
                tags=["database", "design"],
                metadata={"difficulty": "advanced"}
            )
        ]
    
    def tearDown(self):
        """Clean up test database after each test."""
        self.db.close()
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test that database initializes correctly."""
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Check database info
        info = self.db.get_database_info()
        self.assertIn('conversations', info['tables'])
        self.assertIn('conversations_fts', info['tables'])
        self.assertEqual(info['database_path'], self.temp_db.name)
    
    def test_add_conversation(self):
        """Test adding conversations to database."""
        conv = self.sample_conversations[0]
        conv_id = self.db.add_conversation(conv)
        
        self.assertIsInstance(conv_id, int)
        self.assertTrue(self.db.conversation_exists(conv.poe_id))
        
        # Retrieve and verify
        retrieved = self.db.get_conversation_by_poe_id(conv.poe_id)
        self.assertEqual(retrieved.title, conv.title)
        self.assertEqual(retrieved.bot_name, conv.bot_name)
        self.assertEqual(retrieved.message_count, conv.message_count)
    
    def test_search_conversations(self):
        """Test conversation search functionality."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        # Test basic search
        results = self.db.search_conversations("Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Python Programming Help")
        
        # Test search with no query (get all)
        all_results = self.db.search_conversations("")
        self.assertEqual(len(all_results), 3)
        
        # Test bot filter
        claude_results = self.db.search_conversations("", {"bot_name": "Claude"})
        self.assertEqual(len(claude_results), 2)
    
    def test_conversation_statistics(self):
        """Test database statistics functionality."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        stats = self.db.get_stats()
        self.assertEqual(stats['total_conversations'], 3)
        self.assertEqual(stats['unique_bots'], 2)
        self.assertEqual(stats['total_messages'], 6)
        self.assertEqual(stats['avg_messages_per_conversation'], 2.0)
        
        # Check bot distribution
        self.assertEqual(stats['bot_distribution']['Claude'], 2)
        self.assertEqual(stats['bot_distribution']['GPT-4'], 1)
    
    def test_export_functionality(self):
        """Test export to different formats."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        # Test JSON export
        json_file = self.db.export_conversations("json")
        self.assertTrue(os.path.exists(json_file))
        
        with open(json_file, 'r') as f:
            exported_data = json.load(f)
        self.assertEqual(len(exported_data), 3)
        
        # Test CSV export
        csv_file = self.db.export_conversations("csv")
        self.assertTrue(os.path.exists(csv_file))
        
        # Test Markdown export
        md_file = self.db.export_conversations("markdown")
        self.assertTrue(os.path.exists(md_file))
        
        # Cleanup
        for file in [json_file, csv_file, md_file]:
            if os.path.exists(file):
                os.unlink(file)
    
    def test_tag_management(self):
        """Test tag-related functionality."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        # Test getting all tags
        all_tags = self.db.get_all_tags()
        expected_tags = {"python", "programming", "javascript", "async", "database", "design"}
        self.assertEqual(set(all_tags), expected_tags)
        
        # Test tagged conversations
        python_convs = self.db.get_tagged_conversations("python")
        self.assertEqual(len(python_convs), 1)
        self.assertEqual(python_convs[0].title, "Python Programming Help")
        
        # Test updating tags
        success = self.db.update_conversation_tags("conv_1", ["python", "beginner", "help"])
        self.assertTrue(success)
        
        updated_conv = self.db.get_conversation_by_poe_id("conv_1")
        self.assertIn("beginner", updated_conv.tags)
        self.assertIn("help", updated_conv.tags)
    
    def test_bot_management(self):
        """Test bot-related functionality."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        # Test getting all bots
        all_bots = self.db.get_all_bots()
        self.assertEqual(set(all_bots), {"Claude", "GPT-4"})
        
        # Test conversations by bot
        claude_convs = self.db.get_conversations_by_bot("Claude")
        self.assertEqual(len(claude_convs), 2)
        
        # Test conversation count by bot
        bot_counts = self.db.get_conversation_count_by_bot()
        self.assertEqual(bot_counts["Claude"], 2)
        self.assertEqual(bot_counts["GPT-4"], 1)
        
        # Test bulk bot name update
        updated_count = self.db.bulk_update_bot_names({"Claude": "Claude-3"})
        self.assertEqual(updated_count, 2)
        
        updated_bots = self.db.get_all_bots()
        self.assertIn("Claude-3", updated_bots)
        self.assertNotIn("Claude", updated_bots)
    
    def test_backup_restore(self):
        """Test backup and restore functionality."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        # Create backup
        backup_path = self.db.backup_database()
        self.assertTrue(os.path.exists(backup_path))
        
        # Clear database
        for conv in self.sample_conversations:
            self.db.delete_conversation(conv.poe_id)
        
        stats = self.db.get_stats()
        self.assertEqual(stats['total_conversations'], 0)
        
        # Restore from backup
        success = self.db.restore_database(backup_path)
        self.assertTrue(success)
        
        # Verify restoration
        stats = self.db.get_stats()
        self.assertEqual(stats['total_conversations'], 3)
        
        # Cleanup
        os.unlink(backup_path)
    
    def test_duplicate_detection(self):
        """Test duplicate conversation detection."""
        # Add conversations with similar titles
        conv1 = Conversation(poe_id="dup1", title="Python Help", url="url1")
        conv2 = Conversation(poe_id="dup2", title="python help", url="url2")  # Similar title
        conv3 = Conversation(poe_id="dup3", title="JavaScript Guide", url="url3")
        
        for conv in [conv1, conv2, conv3]:
            self.db.add_conversation(conv)
        
        duplicates = self.db.get_duplicate_conversations()
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]['count'], 2)
        self.assertEqual(set(duplicates[0]['poe_ids']), {"dup1", "dup2"})
    
    def test_content_search(self):
        """Test searching within conversation content."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        # Search for specific content
        matches = self.db.search_conversation_content("ACID")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['conversation_title'], "Database Design Principles")
        
        # Test context retrieval
        self.assertIn('context', matches[0])
        self.assertIn('matching_message', matches[0])
    
    def test_metadata_management(self):
        """Test metadata update functionality."""
        conv = self.sample_conversations[0]
        self.db.add_conversation(conv)
        
        # Update metadata
        new_metadata = {"difficulty": "expert", "category": "tutorial"}
        success = self.db.update_conversation_metadata(conv.poe_id, new_metadata)
        self.assertTrue(success)
        
        # Verify update
        updated_conv = self.db.get_conversation_by_poe_id(conv.poe_id)
        self.assertEqual(updated_conv.metadata["difficulty"], "expert")
        self.assertEqual(updated_conv.metadata["category"], "tutorial")
    
    def test_database_optimization(self):
        """Test database optimization functionality."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        # Run optimization
        success = self.db.optimize_database()
        self.assertTrue(success)
    
    def test_search_suggestions(self):
        """Test search suggestion functionality."""
        # Add sample conversations
        for conv in self.sample_conversations:
            self.db.add_conversation(conv)
        
        # Test title suggestions
        suggestions = self.db.get_search_suggestions("Python")
        self.assertIn("Python Programming Help", suggestions)
        
        # Test bot name suggestions
        bot_suggestions = self.db.get_search_suggestions("Clau")
        self.assertIn("Claude", bot_suggestions)
    
    def test_date_range_queries(self):
        """Test date range functionality."""
        # Add conversations with different dates
        conv1 = self.sample_conversations[0]
        conv1.created_at = datetime(2024, 1, 1)
        
        conv2 = self.sample_conversations[1]
        conv2.created_at = datetime(2024, 2, 1)
        
        for conv in [conv1, conv2]:
            self.db.add_conversation(conv)
        
        # Test date-based queries
        date_counts = self.db.get_conversation_count_by_date()
        self.assertIn("2024-01-01", date_counts)
        self.assertIn("2024-02-01", date_counts)
    
    def test_single_conversation_export(self):
        """Test exporting individual conversations."""
        conv = self.sample_conversations[0]
        self.db.add_conversation(conv)
        
        # Export as JSON
        json_file = self.db.export_conversation_by_id(conv.poe_id, "json")
        self.assertIsNotNone(json_file)
        self.assertTrue(os.path.exists(json_file))
        
        # Export as Markdown
        md_file = self.db.export_conversation_by_id(conv.poe_id, "markdown")
        self.assertIsNotNone(md_file)
        self.assertTrue(os.path.exists(md_file))
        
        # Cleanup
        for file in [json_file, md_file]:
            if file and os.path.exists(file):
                os.unlink(file)
    
    def test_conversation_deletion(self):
        """Test conversation deletion functionality."""
        conv = self.sample_conversations[0]
        self.db.add_conversation(conv)
        
        # Verify it exists
        self.assertTrue(self.db.conversation_exists(conv.poe_id))
        
        # Delete it
        success = self.db.delete_conversation(conv.poe_id)
        self.assertTrue(success)
        
        # Verify deletion
        self.assertFalse(self.db.conversation_exists(conv.poe_id))
        
        # Test deleting non-existent conversation
        success = self.db.delete_conversation("nonexistent")
        self.assertFalse(success)


if __name__ == '__main__':
    # Set up logging to reduce noise during testing
    import logging
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # Run the tests
    unittest.main(verbosity=2)