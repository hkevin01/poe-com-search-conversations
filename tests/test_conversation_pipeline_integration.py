#!/usr/bin/env python3
"""
Comprehensive Integration Test for Poe.com Conversation Pipeline

Tests the complete workflow from extraction to search functionality.
"""

import unittest
import tempfile
import os
import json
import time
import sqlite3
import shutil
import sys
from datetime import datetime, timedelta
from typing import List, Dict

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after path setup
from database import ConversationDatabase, Conversation  # noqa: E402


class MockPoeExtractor:
    """Mock extractor for testing conversation extraction process."""
    
    def __init__(self, test_conversations: List[Dict]):
        self.test_conversations = test_conversations
        self.stats = {
            'total_found': 0,
            'new_conversations': 0,
            'updated_conversations': 0,
            'errors': 0,
            'scroll_iterations': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
    
    def extract_all_conversations(self) -> bool:
        """Mock extraction returning predefined test data."""
        self.stats['start_time'] = datetime.now()
        time.sleep(0.1)  # Simulate extraction time
        
        for i, conv_data in enumerate(self.test_conversations):
            if 'error' in conv_data and conv_data['error']:
                self.stats['errors'] += 1
                continue
                
            self.stats['total_found'] += 1
            if i % 3 == 0:
                self.stats['updated_conversations'] += 1
            else:
                self.stats['new_conversations'] += 1
        
        num_convs = len(self.test_conversations)
        self.stats['scroll_iterations'] = max(1, num_convs // 10)
        self.stats['end_time'] = datetime.now()
        return True


class TestConversationPipelineIntegration(unittest.TestCase):
    """Integration tests for complete conversation processing pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with shared resources."""
        cls.test_dir = tempfile.mkdtemp(prefix='poe_test_')
        cls.config_dir = os.path.join(cls.test_dir, 'config')
        os.makedirs(cls.config_dir, exist_ok=True)
        
        cls.token_config = {
            'p_b': 'test_pb_token_12345',
            'p_lat': 'test_plat_token_67890'
        }
        
        config_file = os.path.join(cls.config_dir, 'poe_tokens.json')
        with open(config_file, 'w') as f:
            json.dump(cls.token_config, f)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test class resources."""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def setUp(self):
        """Set up individual test with fresh database and test data."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = ConversationDatabase(self.temp_db.name)
        
        # Create test conversation data
        base_time = datetime.now()
        self.test_conversations_raw = [
            {
                'id': 'conv_001',
                'title': 'Python Data Analysis Tutorial',
                'url': 'https://poe.com/chat/conv_001',
                'discovered_at': (base_time - timedelta(days=5)).isoformat()
            },
            {
                'id': 'conv_002',
                'title': 'Machine Learning Best Practices',
                'url': 'https://poe.com/chat/conv_002',
                'discovered_at': (base_time - timedelta(days=4)).isoformat()
            },
            {
                'id': 'conv_003',
                'title': 'JavaScript Async/Await Deep Dive',
                'url': 'https://poe.com/chat/conv_003',
                'discovered_at': (base_time - timedelta(days=3)).isoformat()
            },
            {
                'id': 'conv_error',
                'title': 'This should cause an error',
                'url': 'https://poe.com/chat/conv_error',
                'error': True
            }
        ]
        
        self.detailed_conversations = self._create_detailed_conversation_data()
        self.mock_extractor = MockPoeExtractor(self.test_conversations_raw)
        
    def tearDown(self):
        """Clean up individual test resources."""
        if hasattr(self, 'temp_db') and os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def _create_detailed_conversation_data(self) -> List[Conversation]:
        """Create detailed conversation objects with full content."""
        conversations = []
        
        # Conversation 1: Python Data Analysis
        conv1 = Conversation(
            poe_id='conv_001',
            title='Python Data Analysis Tutorial',
            url='https://poe.com/chat/conv_001',
            bot_name='Claude-3-Opus',
            created_at=datetime.now() - timedelta(days=5),
            updated_at=datetime.now() - timedelta(days=5),
            message_count=4,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Help with Python data analysis and pandas",
                    "timestamp": (datetime.now() - timedelta(days=5)).isoformat()
                },
                {
                    "sender": "bot",
                    "content": "I'll help with pandas data analysis...",
                    "timestamp": (datetime.now() - timedelta(days=5)).isoformat()
                }
            ]),
            tags=['python', 'data-analysis', 'pandas', 'tutorial'],
            metadata={
                'difficulty': 'beginner',
                'topic': 'data-science',
                'programming_language': 'python',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv1)
        
        # Conversation 2: Machine Learning
        conv2 = Conversation(
            poe_id='conv_002',
            title='Machine Learning Best Practices',
            url='https://poe.com/chat/conv_002',
            bot_name='GPT-4',
            created_at=datetime.now() - timedelta(days=4),
            updated_at=datetime.now() - timedelta(days=4),
            message_count=6,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Best practices for ML projects?",
                    "timestamp": (datetime.now() - timedelta(days=4)).isoformat()
                },
                {
                    "sender": "bot",
                    "content": "Key ML best practices include...",
                    "timestamp": (datetime.now() - timedelta(days=4)).isoformat()
                }
            ]),
            tags=['machine-learning', 'best-practices', 'data-science'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'machine-learning',
                'has_code_examples': False,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv2)
        
        # Conversation 3: JavaScript Async (related to conv1 via programming)
        conv3 = Conversation(
            poe_id='conv_003',
            title='JavaScript Async/Await Deep Dive',
            url='https://poe.com/chat/conv_003',
            bot_name='Claude-3-Sonnet',
            created_at=datetime.now() - timedelta(days=3),
            updated_at=datetime.now() - timedelta(days=3),
            message_count=8,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Explain async/await in JavaScript",
                    "timestamp": (datetime.now() - timedelta(days=3)).isoformat()
                },
                {
                    "sender": "bot",
                    "content": "Async/await is syntactic sugar for promises...",
                    "timestamp": (datetime.now() - timedelta(days=3)).isoformat()
                }
            ]),
            tags=['javascript', 'async-await', 'promises', 'web-development'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'web-development',
                'programming_language': 'javascript',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor',
                'related_topics': ['promises', 'callbacks']
            }
        )
        conversations.append(conv3)
        
        return conversations
    
    def test_01_pipeline_setup_and_configuration(self):
        """Test pipeline configuration and initialization."""
        self.assertIsNotNone(self.db)
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Test database schema
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn('conversations', tables)
            self.assertIn('conversations_fts', tables)
        
        print("✅ Pipeline setup and configuration validated")
    
    def test_02_conversation_extraction_simulation(self):
        """Test conversation extraction process using mock data."""
        success = self.mock_extractor.extract_all_conversations()
        self.assertTrue(success)
        
        stats = self.mock_extractor.stats
        self.assertEqual(stats['total_found'], 3)  # 3 valid conversations
        self.assertEqual(stats['errors'], 1)  # 1 error conversation
        self.assertGreater(stats['scroll_iterations'], 0)
        
        print(f"✅ Extraction: {stats['total_found']} conversations found")
    
    def test_03_database_storage_and_validation(self):
        """Test storing conversations in database with validation."""
        stored_ids = []
        for conv in self.detailed_conversations:
            conv_id = self.db.add_conversation(conv)
            self.assertIsNotNone(conv_id)
            stored_ids.append(conv_id)
        
        self.assertEqual(len(stored_ids), 3)
        
        # Test individual retrieval
        conv1 = self.db.get_conversation_by_poe_id('conv_001')
        self.assertIsNotNone(conv1)
        self.assertEqual(conv1.title, 'Python Data Analysis Tutorial')
        self.assertEqual(conv1.url, 'https://poe.com/chat/conv_001')
        self.assertIn('python', conv1.tags)
        
        print("✅ Database storage validated")
    
    def test_04_metadata_creation_and_enrichment(self):
        """Test metadata creation and enrichment processes."""
        for conv in self.detailed_conversations:
            self.db.add_conversation(conv)
        
        conv1 = self.db.get_conversation_by_poe_id('conv_001')
        metadata = conv1.metadata
        
        # Validate required metadata
        required_fields = [
            'difficulty', 'topic', 'has_code_examples', 'extraction_method'
        ]
        for field in required_fields:
            self.assertIn(field, metadata)
        
        # Test metadata enrichment
        new_metadata = {**metadata, 'user_rating': 5, 'bookmark': True}
        success = self.db.update_conversation_metadata('conv_001', new_metadata)
        self.assertTrue(success)
        
        updated_conv = self.db.get_conversation_by_poe_id('conv_001')
        self.assertEqual(updated_conv.metadata['user_rating'], 5)
        
        print("✅ Metadata creation and enrichment validated")
    
    def test_05_conversation_linking_and_relationships(self):
        """Test conversation linking and relationship mapping."""
        for conv in self.detailed_conversations:
            self.db.add_conversation(conv)
        
        # Test tag-based relationships
        all_convs = self.db.get_all_conversations()
        programming_conversations = [
            conv for conv in all_convs
            if any(tag in ['python', 'javascript'] for tag in conv.tags)
        ]
        self.assertGreater(len(programming_conversations), 1)
        
        print("✅ Conversation linking validated")
    
    def test_06_full_text_search_functionality(self):
        """Test comprehensive search functionality."""
        for conv in self.detailed_conversations:
            self.db.add_conversation(conv)
        
        # Test basic text search
        python_results = self.db.search_conversations("python")
        self.assertGreater(len(python_results), 0)
        
        # Test bot-specific search
        claude_results = self.db.search_conversations(
            "", {"bot_name": "Claude-3-Opus"}
        )
        self.assertGreater(len(claude_results), 0)
        
        print("✅ Full-text search validated")
    
    def test_07_end_to_end_pipeline_integration(self):
        """Test complete end-to-end pipeline integration."""
        print("\n🚀 Running End-to-End Pipeline Integration Test")
        
        # Step 1: Configuration
        self.assertIsNotNone(self.token_config)
        print("   ✅ Configuration validated")
        
        # Step 2: Extraction
        success = self.mock_extractor.extract_all_conversations()
        self.assertTrue(success)
        print(f"   ✅ Extraction: {self.mock_extractor.stats['total_found']}")
        
        # Step 3: Storage
        storage_count = 0
        for conv in self.detailed_conversations:
            if self.db.add_conversation(conv):
                storage_count += 1
        
        self.assertEqual(storage_count, 3)
        print(f"   ✅ Storage: {storage_count} conversations")
        
        # Step 4: Search
        search_results = self.db.search_conversations("python")
        print(f"   ✅ Search: {len(search_results)} results")
        
        # Step 5: Statistics
        stats = self.db.get_stats()
        self.assertEqual(stats['total_conversations'], 3)
        print(f"   ✅ Statistics: {stats['total_conversations']} total")
        
        print("\n🎉 End-to-End Pipeline Integration Test PASSED!")


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.TestLoader.sortTestMethodsUsing = None
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestConversationPipelineIntegration
    )
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("CONVERSATION PIPELINE INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    success_rate = (result.testsRun - len(result.failures) - len(result.errors))
    success_rate = success_rate / result.testsRun * 100
    print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, trace in result.failures:
            print(f"- {test}: {trace}")
    
    if result.errors:
        print("\nERRORS:")
        for test, trace in result.errors:
            print(f"- {test}: {trace}")
    
    sys.exit(0 if result.wasSuccessful() else 1)
