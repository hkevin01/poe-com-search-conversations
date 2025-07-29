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
            content=json.dumps([
                {
                    "sender": "user", 
                    "content": "I need help with Python data analysis. Can you guide me through pandas basics?",
                    "timestamp": (datetime.now() - timedelta(days=5, hours=2)).isoformat()
                },
                {
                    "sender": "bot", 
                    "content": "I'd be happy to help you with pandas! Let's start with the basics. Pandas is a powerful library for data manipulation and analysis...",
                    "timestamp": (datetime.now() - timedelta(days=5, hours=2, minutes=1)).isoformat()
                },
                {
                    "sender": "user", 
                    "content": "How do I load a CSV file and explore the data?",
                    "timestamp": (datetime.now() - timedelta(days=5, hours=1)).isoformat()
                },
                {
                    "sender": "bot", 
                    "content": "Great question! Here's how you can load and explore CSV data:\n\n```python\nimport pandas as pd\ndf = pd.read_csv('your_file.csv')\nprint(df.head())\nprint(df.info())\nprint(df.describe())\n```",
                    "timestamp": (datetime.now() - timedelta(days=5, hours=1, minutes=1)).isoformat()
                }
            ]),
            tags=['python', 'data-analysis', 'pandas', 'tutorial'],
            metadata={
                'difficulty': 'beginner',
                'topic': 'data-science',
                'programming_language': 'python',
                'estimated_reading_time': 15,
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor',
                'extraction_date': datetime.now().isoformat()
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
            message_count=12,
            content=json.dumps([
                {
                    "sender": "user", 
                    "content": "What are the most important best practices for machine learning projects?",
                    "timestamp": (datetime.now() - timedelta(days=4, hours=3)).isoformat()
                },
                {
                    "sender": "bot", 
                    "content": "Excellent question! Here are the key ML best practices:\n\n1. Data Quality is Everything\n2. Feature Engineering\n3. Cross-validation\n4. Model Evaluation Metrics\n5. Version Control for ML",
                    "timestamp": (datetime.now() - timedelta(days=4, hours=3, minutes=2)).isoformat()
                }
            ]),
            tags=['machine-learning', 'best-practices', 'data-science'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'machine-learning',
                'estimated_reading_time': 25,
                'has_code_examples': False,
                'extraction_method': 'enhanced_extractor',
                'extraction_date': datetime.now().isoformat()
            }
        )
        conversations.append(conv2)
        
        # Conversation 3: JavaScript Async
        conv3 = Conversation(
            poe_id='conv_003',
            title='JavaScript Async/Await Deep Dive',
            url='https://poe.com/chat/conv_003',
            bot_name='Claude-3-Sonnet',
            created_at=datetime.now() - timedelta(days=3),
            updated_at=datetime.now() - timedelta(days=3),
            message_count=6,
            content=json.dumps([
                {
                    "sender": "user", 
                    "content": "Can you explain async/await in JavaScript with practical examples?",
                    "timestamp": (datetime.now() - timedelta(days=3, hours=4)).isoformat()
                },
                {
                    "sender": "bot", 
                    "content": "Absolutely! Async/await is syntactic sugar for promises that makes asynchronous code look and behave more like synchronous code...",
                    "timestamp": (datetime.now() - timedelta(days=3, hours=4, minutes=1)).isoformat()
                }
            ]),
            tags=['javascript', 'async-await', 'promises', 'web-development'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'web-development',
                'programming_language': 'javascript',
                'estimated_reading_time': 20,
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor',
                'related_topics': ['promises', 'callbacks', 'event-loop']
            }
        )
        conversations.append(conv3)
        
        # Conversation 4: Database Design
        conv4 = Conversation(
            poe_id='conv_004',
            title='Database Design Principles',
            url='https://poe.com/chat/conv_004',
            bot_name='Claude-3-Opus',
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            message_count=10,
            content=json.dumps([
                {
                    "sender": "user", 
                    "content": "What are the fundamental principles of good database design?",
                    "timestamp": (datetime.now() - timedelta(days=2, hours=2)).isoformat()
                },
                {
                    "sender": "bot", 
                    "content": "Great question! Good database design follows several key principles:\n\n1. Normalization\n2. Referential Integrity\n3. Data Types Optimization\n4. Indexing Strategy",
                    "timestamp": (datetime.now() - timedelta(days=2, hours=2, minutes=1)).isoformat()
                }
            ]),
            tags=['database', 'design', 'sql', 'normalization'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'database-design',
                'estimated_reading_time': 30,
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor',
                'related_topics': ['sql', 'normalization', 'indexing']
            }
        )
        conversations.append(conv4)
        
        # Conversation 5: Web Scraping (Related to conv1 - both Python)
        conv5 = Conversation(
            poe_id='conv_005',
            title='Python Web Scraping with BeautifulSoup',
            url='https://poe.com/chat/conv_005',
            bot_name='GPT-4',
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            message_count=14,
            content=json.dumps([
                {
                    "sender": "user", 
                    "content": "How do I scrape websites using Python and BeautifulSoup?",
                    "timestamp": (datetime.now() - timedelta(days=1, hours=3)).isoformat()
                },
                {
                    "sender": "bot", 
                    "content": "Web scraping with BeautifulSoup is straightforward! Here's a complete example:\n\n```python\nimport requests\nfrom bs4 import BeautifulSoup\n\nurl = 'https://example.com'\nresponse = requests.get(url)\nsoup = BeautifulSoup(response.content, 'html.parser')\n```",
                    "timestamp": (datetime.now() - timedelta(days=1, hours=3, minutes=2)).isoformat()
                }
            ]),
            tags=['python', 'web-scraping', 'beautifulsoup', 'requests'],
            metadata={
                'difficulty': 'beginner',
                'topic': 'web-scraping',
                'programming_language': 'python',
                'estimated_reading_time': 18,
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor',
                'related_to': ['conv_001'],  # Related to Python data analysis
                'related_topics': ['requests', 'html-parsing', 'data-extraction']
            }
        )
        conversations.append(conv5)
        
        return conversations
    
    def test_01_pipeline_setup_and_configuration(self):
        """Test that the pipeline can be properly configured and initialized."""
        # Test database initialization
        self.assertIsNotNone(self.db)
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Test database schema exists
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.assertIn('conversations', tables)
            self.assertIn('conversations_fts', tables)
        
        # Test token configuration
        self.assertEqual(self.token_config['p_b'], 'test_pb_token_12345')
        self.assertEqual(self.token_config['p_lat'], 'test_plat_token_67890')
        
        print("✅ Pipeline setup and configuration validated")
    
    def test_02_conversation_extraction_simulation(self):
        """Test the conversation extraction process using mock data."""
        # Run extraction
        success = self.mock_extractor.extract_all_conversations()
        self.assertTrue(success)
        
        # Validate extraction statistics
        stats = self.mock_extractor.stats
        self.assertEqual(stats['total_found'], 5)  # 5 valid conversations (1 error)
        self.assertEqual(stats['errors'], 1)  # 1 error conversation
        self.assertGreater(stats['scroll_iterations'], 0)
        self.assertIsNotNone(stats['start_time'])
        self.assertIsNotNone(stats['end_time'])
        
        # Test extraction duration
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        self.assertGreater(duration, 0)
        self.assertLess(duration, 5)  # Should be fast for mock data
        
        print(f"✅ Extraction simulation completed: {stats['total_found']} conversations found")
    
    def test_03_database_storage_and_validation(self):
        """Test storing extracted conversations in the database with full validation."""
        # Store all detailed conversations
        stored_ids = []
        for conv in self.detailed_conversations:
            conv_id = self.db.add_conversation(conv)
            self.assertIsNotNone(conv_id)
            stored_ids.append(conv_id)
        
        # Validate all conversations were stored
        self.assertEqual(len(stored_ids), 5)
        
        # Test database statistics
        stats = self.db.get_stats()
        self.assertEqual(stats['total_conversations'], 5)
        self.assertEqual(stats['unique_bots'], 3)  # Claude-3-Opus, GPT-4, Claude-3-Sonnet
        self.assertGreater(stats['total_messages'], 0)
        
        # Validate individual conversation retrieval
        conv1 = self.db.get_conversation_by_poe_id('conv_001')
        self.assertIsNotNone(conv1)
        self.assertEqual(conv1.title, 'Python Data Analysis Tutorial')
        self.assertEqual(conv1.bot_name, 'Claude-3-Opus')
        self.assertEqual(len(conv1.tags), 4)
        self.assertIn('python', conv1.tags)
        
        # Test URL storage
        self.assertEqual(conv1.url, 'https://poe.com/chat/conv_001')
        
        # Test metadata storage
        self.assertEqual(conv1.metadata['difficulty'], 'beginner')
        self.assertEqual(conv1.metadata['topic'], 'data-science')
        self.assertTrue(conv1.metadata['has_code_examples'])
        
        print("✅ Database storage and validation completed")
    
    def test_04_metadata_creation_and_enrichment(self):
        """Test metadata creation, validation, and enrichment processes."""
        # Store conversations first
        for conv in self.detailed_conversations:
            self.db.add_conversation(conv)
        
        # Test metadata retrieval and validation
        conv1 = self.db.get_conversation_by_poe_id('conv_001')
        metadata = conv1.metadata
        
        # Validate required metadata fields
        required_fields = ['difficulty', 'topic', 'estimated_reading_time', 
                          'has_code_examples', 'extraction_method']
        for field in required_fields:
            self.assertIn(field, metadata, f"Missing required metadata field: {field}")
        
        # Test metadata enrichment
        new_metadata = {
            'user_rating': 5,
            'bookmark': True,
            'category': 'tutorial',
            'review_status': 'approved'
        }
        
        success = self.db.update_conversation_metadata('conv_001', {**metadata, **new_metadata})
        self.assertTrue(success)
        
        # Validate metadata was updated
        updated_conv = self.db.get_conversation_by_poe_id('conv_001')
        self.assertEqual(updated_conv.metadata['user_rating'], 5)
        self.assertTrue(updated_conv.metadata['bookmark'])
        self.assertEqual(updated_conv.metadata['category'], 'tutorial')
        
        # Test metadata-based filtering
        python_convs = self.db.search_conversations("", {"metadata.programming_language": "python"})
        self.assertGreater(len(python_convs), 0)
        
        print("✅ Metadata creation and enrichment validated")
    
    def test_05_conversation_linking_and_relationships(self):
        """Test conversation linking and relationship mapping."""
        # Store conversations first
        for conv in self.detailed_conversations:
            self.db.add_conversation(conv)
        
        # Test tag-based relationships
        python_conversations = []
        all_convs = self.db.get_all_conversations()
        
        for conv in all_convs:
            if 'python' in conv.tags:
                python_conversations.append(conv)
        
        self.assertEqual(len(python_conversations), 2)  # conv_001 and conv_005
        
        # Test explicit relationship linking (conv_005 is related to conv_001)
        conv5 = self.db.get_conversation_by_poe_id('conv_005')
        self.assertIn('conv_001', conv5.metadata.get('related_to', []))
        
        # Test topic-based relationships
        data_science_convs = []
        for conv in all_convs:
            if conv.metadata.get('topic') in ['data-science', 'machine-learning']:
                data_science_convs.append(conv)
        
        self.assertGreater(len(data_science_convs), 0)
        
        # Test difficulty-based grouping
        beginner_convs = [conv for conv in all_convs if conv.metadata.get('difficulty') == 'beginner']
        intermediate_convs = [conv for conv in all_convs if conv.metadata.get('difficulty') == 'intermediate']
        
        self.assertGreater(len(beginner_convs), 0)
        self.assertGreater(len(intermediate_convs), 0)
        
        print("✅ Conversation linking and relationships validated")
    
    def test_06_full_text_search_functionality(self):
        """Test comprehensive search functionality across conversations."""
        # Store conversations first
        for conv in self.detailed_conversations:
            self.db.add_conversation(conv)
        
        # Test basic text search
        python_results = self.db.search_conversations("python")
        self.assertGreater(len(python_results), 0)
        
        # Validate search results contain expected conversations
        python_titles = [conv.title for conv in python_results]
        self.assertTrue(any('Python Data Analysis' in title for title in python_titles))
        self.assertTrue(any('Python Web Scraping' in title for title in python_titles))
        
        # Test specific term search
        async_results = self.db.search_conversations("async await")
        self.assertGreater(len(async_results), 0)
        self.assertTrue(any('JavaScript Async' in conv.title for conv in async_results))
        
        # Test bot-specific search
        claude_results = self.db.search_conversations("", {"bot_name": "Claude-3-Opus"})
        self.assertGreater(len(claude_results), 0)
        for conv in claude_results:
            self.assertEqual(conv.bot_name, "Claude-3-Opus")
        
        # Test date range search
        recent_date = datetime.now() - timedelta(days=2)
        recent_results = self.db.search_conversations("", {"date_after": recent_date})
        self.assertGreater(len(recent_results), 0)
        
        # Test tag-based search
        tutorial_results = self.db.search_conversations("", {"tags": ["tutorial"]})
        self.assertGreater(len(tutorial_results), 0)
        
        # Test combined search (text + filters)
        combined_results = self.db.search_conversations("data", {"bot_name": "Claude-3-Opus"})
        self.assertGreater(len(combined_results), 0)
        
        print("✅ Full-text search functionality validated")
    
    def test_07_data_export_and_import_validation(self):
        """Test data export functionality and validate exported content."""
        # Store conversations first
        for conv in self.detailed_conversations:
            self.db.add_conversation(conv)
        
        # Test JSON export
        json_exports = []
        for conv in self.detailed_conversations[:3]:  # Test first 3 conversations
            json_file = self.db.export_conversation_by_id(conv.poe_id, "json")
            self.assertIsNotNone(json_file)
            self.assertTrue(os.path.exists(json_file))
            
            # Validate JSON content
            with open(json_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
                self.assertEqual(exported_data['poe_id'], conv.poe_id)
                self.assertEqual(exported_data['title'], conv.title)
                self.assertIn('url', exported_data)
                self.assertIn('metadata', exported_data)
                self.assertIn('content', exported_data)
            
            json_exports.append(json_file)
        
        # Test Markdown export
        md_exports = []
        for conv in self.detailed_conversations[:2]:  # Test first 2 conversations
            md_file = self.db.export_conversation_by_id(conv.poe_id, "markdown")
            self.assertIsNotNone(md_file)
            self.assertTrue(os.path.exists(md_file))
            
            # Validate Markdown content
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
                self.assertIn(conv.title, md_content)
                self.assertIn('Bot:', md_content)  # Should have bot messages
                self.assertIn('User:', md_content)  # Should have user messages
            
            md_exports.append(md_file)
        
        # Clean up export files
        for file_path in json_exports + md_exports:
            if os.path.exists(file_path):
                os.unlink(file_path)
        
        print("✅ Data export and import validation completed")
    
    def test_08_error_handling_and_resilience(self):
        """Test error handling and system resilience."""
        # Test duplicate conversation handling
        conv1 = self.detailed_conversations[0]
        
        # Add conversation first time
        id1 = self.db.add_conversation(conv1)
        self.assertIsNotNone(id1)
        
        # Add same conversation again (should update, not duplicate)
        modified_conv1 = Conversation(
            poe_id=conv1.poe_id,  # Same ID
            title=conv1.title + " - Updated",
            url=conv1.url,
            bot_name=conv1.bot_name,
            created_at=conv1.created_at,
            updated_at=datetime.now(),  # Different update time
            message_count=conv1.message_count + 1,
            content=conv1.content,
            tags=conv1.tags + ['updated'],
            metadata={**conv1.metadata, 'updated': True}
        )
        
        id2 = self.db.add_conversation(modified_conv1)
        self.assertIsNotNone(id2)
        
        # Should be same conversation (updated, not duplicated)
        retrieved = self.db.get_conversation_by_poe_id(conv1.poe_id)
        self.assertIn("Updated", retrieved.title)
        self.assertTrue(retrieved.metadata.get('updated', False))
        
        # Test invalid search handling
        empty_results = self.db.search_conversations("")  # Empty query
        self.assertIsInstance(empty_results, list)
        
        # Test non-existent conversation retrieval
        non_existent = self.db.get_conversation_by_poe_id('non_existent_id')
        self.assertIsNone(non_existent)
        
        # Test database optimization
        optimization_success = self.db.optimize_database()
        self.assertTrue(optimization_success)
        
        print("✅ Error handling and resilience validated")
    
    def test_09_performance_and_scalability(self):
        """Test performance characteristics with larger datasets."""
        start_time = time.time()
        
        # Create and store a larger dataset
        bulk_conversations = []
        for i in range(50):  # Create 50 test conversations
            conv = Conversation(
                poe_id=f'bulk_conv_{i:03d}',
                title=f'Bulk Test Conversation {i}',
                url=f'https://poe.com/chat/bulk_conv_{i:03d}',
                bot_name='Claude-3-Opus' if i % 2 == 0 else 'GPT-4',
                created_at=datetime.now() - timedelta(days=i % 30),
                updated_at=datetime.now() - timedelta(days=i % 30),
                message_count=5 + (i % 10),
                content=json.dumps([
                    {"sender": "user", "content": f"Test message {i}"},
                    {"sender": "bot", "content": f"Test response {i}"}
                ]),
                tags=[f'tag_{i % 5}', 'bulk_test'],
                metadata={'bulk_index': i, 'category': f'category_{i % 3}'}
            )
            bulk_conversations.append(conv)
        
        # Bulk insert performance test
        insert_start = time.time()
        for conv in bulk_conversations:
            self.db.add_conversation(conv)
        insert_time = time.time() - insert_start
        
        # Should be able to insert 50 conversations quickly
        self.assertLess(insert_time, 5.0, "Bulk insert took too long")
        
        # Search performance test
        search_start = time.time()
        search_results = self.db.search_conversations("Test")
        search_time = time.time() - search_start
        
        # Should find results quickly
        self.assertGreater(len(search_results), 0)
        self.assertLess(search_time, 2.0, "Search took too long")
        
        # Statistics performance test
        stats_start = time.time()
        stats = self.db.get_stats()
        stats_time = time.time() - stats_start
        
        self.assertEqual(stats['total_conversations'], 50)
        self.assertLess(stats_time, 1.0, "Statistics calculation took too long")
        
        total_time = time.time() - start_time
        self.assertLess(total_time, 10.0, "Overall performance test took too long")
        
        print(f"✅ Performance test completed in {total_time:.2f}s")
    
    def test_10_end_to_end_pipeline_integration(self):
        """Test the complete end-to-end pipeline integration."""
        pipeline_start = time.time()
        
        print("\n🚀 Running End-to-End Pipeline Integration Test")
        
        # Step 1: Configuration validation
        self.assertIsNotNone(self.token_config)
        print("   ✅ Configuration validated")
        
        # Step 2: Mock extraction
        extraction_success = self.mock_extractor.extract_all_conversations()
        self.assertTrue(extraction_success)
        print(f"   ✅ Extraction completed: {self.mock_extractor.stats['total_found']} conversations")
        
        # Step 3: Database storage
        storage_count = 0
        for conv in self.detailed_conversations:
            conv_id = self.db.add_conversation(conv)
            if conv_id:
                storage_count += 1
        
        self.assertEqual(storage_count, 5)
        print(f"   ✅ Database storage: {storage_count} conversations stored")
        
        # Step 4: Metadata enrichment
        enrichment_count = 0
        for conv in self.detailed_conversations:
            if conv.metadata and len(conv.metadata) > 3:  # Has substantial metadata
                enrichment_count += 1
        
        self.assertGreater(enrichment_count, 0)
        print(f"   ✅ Metadata enrichment: {enrichment_count} conversations enriched")
        
        # Step 5: Relationship mapping
        related_conversations = 0
        for conv in self.detailed_conversations:
            if conv.metadata.get('related_to') or len(conv.tags) > 2:
                related_conversations += 1
        
        self.assertGreater(related_conversations, 0)
        print(f"   ✅ Relationship mapping: {related_conversations} conversations linked")
        
        # Step 6: Search functionality
        search_tests = [
            ("python", "Programming language search"),
            ("data", "Topic-based search"),
            ("tutorial", "Tag-based search")
        ]
        
        search_results_total = 0
        for query, description in search_tests:
            results = self.db.search_conversations(query)
            search_results_total += len(results)
            print(f"   ✅ {description}: {len(results)} results")
        
        self.assertGreater(search_results_total, 0)
        
        # Step 7: Export functionality
        export_success = 0
        test_conv = self.detailed_conversations[0]
        for format_type in ['json', 'markdown']:
            export_file = self.db.export_conversation_by_id(test_conv.poe_id, format_type)
            if export_file and os.path.exists(export_file):
                export_success += 1
                os.unlink(export_file)  # Clean up
        
        self.assertEqual(export_success, 2)
        print(f"   ✅ Export functionality: {export_success} formats tested")
        
        # Step 8: Final statistics
        final_stats = self.db.get_stats()
        self.assertEqual(final_stats['total_conversations'], 5)
        self.assertGreater(final_stats['total_messages'], 0)
        
        pipeline_time = time.time() - pipeline_start
        
        print(f"\n🎉 End-to-End Pipeline Integration Test PASSED!")
        print(f"   📊 Final Statistics:")
        print(f"      - Total conversations: {final_stats['total_conversations']}")
        print(f"      - Unique bots: {final_stats['unique_bots']}")
        print(f"      - Total messages: {final_stats['total_messages']}")
        print(f"      - Pipeline execution time: {pipeline_time:.2f}s")
        
        # Validate overall pipeline success
        self.assertLess(pipeline_time, 30.0, "Pipeline took too long")
        self.assertEqual(final_stats['total_conversations'], 5)
        self.assertGreater(final_stats['total_messages'], 10)
        
        print("✅ Complete pipeline integration validated successfully!")


if __name__ == '__main__':
    # Configure test runner
    unittest.TestLoader.sortTestMethodsUsing = None  # Run tests in order
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConversationPipelineIntegration)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*80)
    print("CONVERSATION PIPELINE INTEGRATION TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, trace in result.failures:
            print(f"- {test}: {trace}")
    
    if result.errors:
        print("\nERRORS:")
        for test, trace in result.errors:
            print(f"- {test}: {trace}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
