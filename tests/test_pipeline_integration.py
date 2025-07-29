#!/usr/bin/env python3
"""
Comprehensive Integration Test for Poe.com Conversation Pipeline

This test validates the entire workflow from conversation extraction to search
and ensures all components work correctly together.
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
                'discovered_at': (base_time - timedelta(days=10)).isoformat()
            },
            {
                'id': 'conv_002',
                'title': 'Machine Learning Best Practices',
                'url': 'https://poe.com/chat/conv_002',
                'discovered_at': (base_time - timedelta(days=9)).isoformat()
            },
            {
                'id': 'conv_003',
                'title': 'JavaScript Async/Await Deep Dive',
                'url': 'https://poe.com/chat/conv_003',
                'discovered_at': (base_time - timedelta(days=8)).isoformat()
            },
            {
                'id': 'conv_004',
                'title': 'Advanced Python Data Science Techniques',
                'url': 'https://poe.com/chat/conv_004',
                'discovered_at': (base_time - timedelta(days=7)).isoformat()
            },
            {
                'id': 'conv_005',
                'title': 'React Hooks and State Management',
                'url': 'https://poe.com/chat/conv_005',
                'discovered_at': (base_time - timedelta(days=6)).isoformat()
            },
            {
                'id': 'conv_006',
                'title': 'Deep Learning with TensorFlow',
                'url': 'https://poe.com/chat/conv_006',
                'discovered_at': (base_time - timedelta(days=5)).isoformat()
            },
            {
                'id': 'conv_007',
                'title': 'JavaScript ES6+ Features',
                'url': 'https://poe.com/chat/conv_007',
                'discovered_at': (base_time - timedelta(days=4)).isoformat()
            },
            {
                'id': 'conv_008',
                'title': 'Python Web Scraping with BeautifulSoup',
                'url': 'https://poe.com/chat/conv_008',
                'discovered_at': (base_time - timedelta(days=3)).isoformat()
            },
            {
                'id': 'conv_009',
                'title': 'Machine Learning Model Deployment',
                'url': 'https://poe.com/chat/conv_009',
                'discovered_at': (base_time - timedelta(days=2)).isoformat()
            },
            {
                'id': 'conv_010',
                'title': 'Node.js Backend Development',
                'url': 'https://poe.com/chat/conv_010',
                'discovered_at': (base_time - timedelta(days=1)).isoformat()
            },
            {
                'id': 'conv_011',
                'title': 'Data Visualization with Python',
                'url': 'https://poe.com/chat/conv_011',
                'discovered_at': (base_time - timedelta(hours=12)).isoformat()
            },
            {
                'id': 'conv_012',
                'title': 'Advanced JavaScript Patterns',
                'url': 'https://poe.com/chat/conv_012',
                'discovered_at': (base_time - timedelta(hours=6)).isoformat()
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
        base_time = datetime.now()
        
        # Conversation 1: Python Data Analysis
        conv1 = Conversation(
            poe_id='conv_001',
            title='Python Data Analysis Tutorial',
            url='https://poe.com/chat/conv_001',
            bot_name='Claude-3-Opus',
            created_at=base_time - timedelta(days=10),
            updated_at=base_time - timedelta(days=10),
            message_count=4,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Help with Python data analysis and pandas",
                    "timestamp": (base_time - timedelta(days=10)).isoformat()
                },
                {
                    "sender": "bot",
                    "content": "I'll help with pandas data analysis...",
                    "timestamp": (base_time - timedelta(days=10)).isoformat()
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
            created_at=base_time - timedelta(days=9),
            updated_at=base_time - timedelta(days=9),
            message_count=6,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Best practices for ML projects?",
                    "timestamp": (base_time - timedelta(days=9)).isoformat()
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
        
        # Conversation 3: JavaScript Async
        conv3 = Conversation(
            poe_id='conv_003',
            title='JavaScript Async/Await Deep Dive',
            url='https://poe.com/chat/conv_003',
            bot_name='Claude-3-Sonnet',
            created_at=base_time - timedelta(days=8),
            updated_at=base_time - timedelta(days=8),
            message_count=8,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Explain async/await in JavaScript",
                    "timestamp": (base_time - timedelta(days=8)).isoformat()
                }
            ]),
            tags=['javascript', 'async-await', 'web-development'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'web-development',
                'programming_language': 'javascript',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv3)
        
        # Conversation 4: Advanced Python Data Science
        conv4 = Conversation(
            poe_id='conv_004',
            title='Advanced Python Data Science Techniques',
            url='https://poe.com/chat/conv_004',
            bot_name='Claude-3-Opus',
            created_at=base_time - timedelta(days=7),
            updated_at=base_time - timedelta(days=7),
            message_count=12,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Advanced data science techniques in Python",
                    "timestamp": (base_time - timedelta(days=7)).isoformat()
                }
            ]),
            tags=['python', 'data-science', 'advanced', 'statistics'],
            metadata={
                'difficulty': 'advanced',
                'topic': 'data-science',
                'programming_language': 'python',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv4)
        
        # Conversation 5: React Hooks
        conv5 = Conversation(
            poe_id='conv_005',
            title='React Hooks and State Management',
            url='https://poe.com/chat/conv_005',
            bot_name='GPT-4',
            created_at=base_time - timedelta(days=6),
            updated_at=base_time - timedelta(days=6),
            message_count=10,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "How to use React hooks effectively?",
                    "timestamp": (base_time - timedelta(days=6)).isoformat()
                }
            ]),
            tags=['javascript', 'react', 'hooks', 'web-development'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'web-development',
                'programming_language': 'javascript',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor',
                'framework': 'react'
            }
        )
        conversations.append(conv5)
        
        # Conversation 6: Deep Learning
        conv6 = Conversation(
            poe_id='conv_006',
            title='Deep Learning with TensorFlow',
            url='https://poe.com/chat/conv_006',
            bot_name='Claude-3-Haiku',
            created_at=base_time - timedelta(days=5),
            updated_at=base_time - timedelta(days=5),
            message_count=15,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Deep learning tutorial with TensorFlow",
                    "timestamp": (base_time - timedelta(days=5)).isoformat()
                }
            ]),
            tags=['python', 'deep-learning', 'tensorflow', 'machine-learning'],
            metadata={
                'difficulty': 'advanced',
                'topic': 'machine-learning',
                'programming_language': 'python',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor',
                'framework': 'tensorflow'
            }
        )
        conversations.append(conv6)
        
        # Conversation 7: JavaScript ES6+
        conv7 = Conversation(
            poe_id='conv_007',
            title='JavaScript ES6+ Features',
            url='https://poe.com/chat/conv_007',
            bot_name='Claude-3-Sonnet',
            created_at=base_time - timedelta(days=4),
            updated_at=base_time - timedelta(days=4),
            message_count=7,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Modern JavaScript ES6+ features",
                    "timestamp": (base_time - timedelta(days=4)).isoformat()
                }
            ]),
            tags=['javascript', 'es6', 'modern-js', 'web-development'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'web-development',
                'programming_language': 'javascript',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv7)
        
        # Conversation 8: Python Web Scraping
        conv8 = Conversation(
            poe_id='conv_008',
            title='Python Web Scraping with BeautifulSoup',
            url='https://poe.com/chat/conv_008',
            bot_name='GPT-4',
            created_at=base_time - timedelta(days=3),
            updated_at=base_time - timedelta(days=3),
            message_count=9,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Web scraping tutorial with Python",
                    "timestamp": (base_time - timedelta(days=3)).isoformat()
                }
            ]),
            tags=['python', 'web-scraping', 'beautifulsoup', 'tutorial'],
            metadata={
                'difficulty': 'beginner',
                'topic': 'web-scraping',
                'programming_language': 'python',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv8)
        
        # Conversation 9: ML Deployment
        conv9 = Conversation(
            poe_id='conv_009',
            title='Machine Learning Model Deployment',
            url='https://poe.com/chat/conv_009',
            bot_name='Claude-3-Opus',
            created_at=base_time - timedelta(days=2),
            updated_at=base_time - timedelta(days=2),
            message_count=11,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "How to deploy ML models to production?",
                    "timestamp": (base_time - timedelta(days=2)).isoformat()
                }
            ]),
            tags=['machine-learning', 'deployment', 'production', 'devops'],
            metadata={
                'difficulty': 'advanced',
                'topic': 'machine-learning',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv9)
        
        # Conversation 10: Node.js Backend
        conv10 = Conversation(
            poe_id='conv_010',
            title='Node.js Backend Development',
            url='https://poe.com/chat/conv_010',
            bot_name='GPT-4-Turbo',
            created_at=base_time - timedelta(days=1),
            updated_at=base_time - timedelta(days=1),
            message_count=13,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Building backend APIs with Node.js",
                    "timestamp": (base_time - timedelta(days=1)).isoformat()
                }
            ]),
            tags=['javascript', 'nodejs', 'backend', 'api', 'web-development'],
            metadata={
                'difficulty': 'intermediate',
                'topic': 'web-development',
                'programming_language': 'javascript',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor',
                'framework': 'nodejs'
            }
        )
        conversations.append(conv10)
        
        # Conversation 11: Data Visualization
        conv11 = Conversation(
            poe_id='conv_011',
            title='Data Visualization with Python',
            url='https://poe.com/chat/conv_011',
            bot_name='Claude-3-Haiku',
            created_at=base_time - timedelta(hours=12),
            updated_at=base_time - timedelta(hours=12),
            message_count=8,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Creating charts and graphs with Python",
                    "timestamp": (base_time - timedelta(hours=12)).isoformat()
                }
            ]),
            tags=['python', 'data-visualization', 'matplotlib',
                  'data-science'],
            metadata={
                'difficulty': 'beginner',
                'topic': 'data-science',
                'programming_language': 'python',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv11)
        
        # Conversation 12: Advanced JavaScript
        conv12 = Conversation(
            poe_id='conv_012',
            title='Advanced JavaScript Patterns',
            url='https://poe.com/chat/conv_012',
            bot_name='Claude-3-Sonnet',
            created_at=base_time - timedelta(hours=6),
            updated_at=base_time - timedelta(hours=6),
            message_count=14,
            content=json.dumps([
                {
                    "sender": "user",
                    "content": "Advanced JavaScript design patterns",
                    "timestamp": (base_time - timedelta(hours=6)).isoformat()
                }
            ]),
            tags=['javascript', 'design-patterns', 'advanced',
                  'web-development'],
            metadata={
                'difficulty': 'advanced',
                'topic': 'web-development',
                'programming_language': 'javascript',
                'has_code_examples': True,
                'extraction_method': 'enhanced_extractor'
            }
        )
        conversations.append(conv12)
        
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
        self.assertEqual(stats['total_found'], 12)  # 12 valid conversations
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
        
        self.assertEqual(len(stored_ids), 12)
        
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
        success = self.db.update_conversation_metadata('conv_001',
                                                       new_metadata)
        self.assertTrue(success)
        
        updated_conv = self.db.get_conversation_by_poe_id('conv_001')
        self.assertEqual(updated_conv.metadata['user_rating'], 5)
        
        print("✅ Metadata creation and enrichment validated")
    
    def test_05_conversation_linking_and_relationships(self):
        """Test conversation linking and relationship mapping."""
        for conv in self.detailed_conversations:
            self.db.add_conversation(conv)
        
        # Test tag-based relationships
        all_convs = self.db.get_recent_conversations(limit=100)
        programming_conversations = [
            conv for conv in all_convs
            if any(tag in ['python', 'javascript'] for tag in conv.tags)
        ]
        self.assertGreater(len(programming_conversations), 1)
        
        # Test specific tag searches
        python_convs = self.db.get_tagged_conversations('python')
        self.assertGreater(len(python_convs), 0)
        
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
        extraction_count = self.mock_extractor.stats['total_found']
        print(f"   ✅ Extraction: {extraction_count}")
        
        # Step 3: Storage
        storage_count = 0
        for conv in self.detailed_conversations:
            if self.db.add_conversation(conv):
                storage_count += 1
        
        self.assertEqual(storage_count, 12)
        print(f"   ✅ Storage: {storage_count} conversations")
        
        # Step 4: Search
        search_results = self.db.search_conversations("python")
        print(f"   ✅ Search: {len(search_results)} results")
        
        # Step 5: Statistics
        stats = self.db.get_stats()
        self.assertEqual(stats['total_conversations'], 12)
        print(f"   ✅ Statistics: {stats['total_conversations']} total")
        
        # Step 6: Detailed Analysis
        self._print_detailed_pipeline_analysis()
        
        print("\n🎉 End-to-End Pipeline Integration Test PASSED!")
    
    def _print_detailed_pipeline_analysis(self):
        """Print comprehensive analysis of pipeline results."""
        print("\n" + "="*70)
        print("📊 DETAILED PIPELINE ANALYSIS")
        print("="*70)
        
        # Conversation Analysis
        print("\n📚 CONVERSATION ANALYSIS:")
        all_conversations = self.db.get_recent_conversations(limit=100)
        print(f"   Total conversations stored: {len(all_conversations)}")
        
        # Bot distribution
        bot_counts = {}
        for conv in all_conversations:
            bot_counts[conv.bot_name] = bot_counts.get(conv.bot_name, 0) + 1
        
        print("   Bot distribution:")
        for bot, count in sorted(bot_counts.items()):
            print(f"     • {bot}: {count} conversations")
        
        # Message count analysis
        total_messages = sum(conv.message_count for conv in all_conversations)
        if all_conversations:
            avg_messages = total_messages / len(all_conversations)
        else:
            avg_messages = 0
        print(f"   Total messages across all conversations: {total_messages}")
        print(f"   Average messages per conversation: {avg_messages:.1f}")
        
        # Metadata Analysis
        print("\n🏷️  METADATA ANALYSIS:")
        metadata_fields = set()
        metadata_values = {}
        
        for conv in all_conversations:
            for key, value in conv.metadata.items():
                metadata_fields.add(key)
                if key not in metadata_values:
                    metadata_values[key] = set()
                metadata_values[key].add(str(value))
        
        print(f"   Total unique metadata fields: {len(metadata_fields)}")
        print("   Metadata field distribution:")
        for field in sorted(metadata_fields):
            unique_values = len(metadata_values[field])
            print(f"     • {field}: {unique_values} unique values")
        
        # Detailed metadata breakdown
        print("\n   Metadata field details:")
        for field, values in sorted(metadata_values.items()):
            print(f"     • {field}:")
            for value in sorted(values):
                count = sum(1 for conv in all_conversations
                            if (conv.metadata.get(field) == value or
                                str(conv.metadata.get(field)) == value))
                print(f"       - {value}: {count} conversations")
        
        # Tag Analysis
        print("\n🔗 TAG ANALYSIS & RELATIONSHIP MAPPING:")
        all_tags = set()
        tag_counts = {}
        
        for conv in all_conversations:
            for tag in conv.tags:
                all_tags.add(tag)
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        print(f"   Total unique tags: {len(all_tags)}")
        print("   Tag distribution:")
        sorted_tags = sorted(tag_counts.items(),
                             key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags:
            print(f"     • {tag}: {count} conversations")
        
        # Relationship Analysis
        print("\n🔄 CONVERSATION RELATIONSHIPS:")
        
        # Find conversations with shared tags
        relationships = []
        conversations_list = list(all_conversations)
        
        for i, conv1 in enumerate(conversations_list):
            for j, conv2 in enumerate(conversations_list[i+1:], i+1):
                shared_tags = set(conv1.tags) & set(conv2.tags)
                if shared_tags:
                    title1 = (conv1.title[:30] + "..."
                              if len(conv1.title) > 30 else conv1.title)
                    title2 = (conv2.title[:30] + "..."
                              if len(conv2.title) > 30 else conv2.title)
                    total_tags = len(set(conv1.tags) | set(conv2.tags))
                    similarity = len(shared_tags) / total_tags
                    
                    relationships.append({
                        'conv1': title1,
                        'conv2': title2,
                        'shared_tags': list(shared_tags),
                        'similarity_score': similarity
                    })
        
        rel_count = len(relationships)
        print(f"   Total conversation relationships found: {rel_count}")
        if relationships:
            print("   Relationship details:")
            sorted_rels = sorted(relationships,
                                 key=lambda x: x['similarity_score'],
                                 reverse=True)
            for rel in sorted_rels:
                print(f"     • '{rel['conv1']}' ↔ '{rel['conv2']}'")
                shared = ', '.join(rel['shared_tags'])
                print(f"       Shared tags: {shared}")
                score = rel['similarity_score']
                print(f"       Similarity score: {score:.2f}")
        
        # Topic clustering
        print("\n📋 TOPIC CLUSTERING:")
        topic_groups = {}
        for conv in all_conversations:
            topic = conv.metadata.get('topic', 'unknown')
            if topic not in topic_groups:
                topic_groups[topic] = []
            topic_groups[topic].append(conv)
        
        print(f"   Total topic clusters: {len(topic_groups)}")
        for topic, convs in sorted(topic_groups.items()):
            print(f"     • {topic}: {len(convs)} conversations")
            for conv in convs:
                title = (conv.title[:40] + "..."
                         if len(conv.title) > 40 else conv.title)
                print(f"       - {title}")
        
        # Search Capability Analysis
        print("\n🔍 SEARCH CAPABILITY ANALYSIS:")
        
        search_terms = ['python', 'javascript', 'machine learning',
                        'data', 'async']
        for term in search_terms:
            results = self.db.search_conversations(term)
            print(f"   Search '{term}': {len(results)} results")
        
        # Programming language distribution
        print("\n💻 PROGRAMMING LANGUAGE DISTRIBUTION:")
        lang_counts = {}
        for conv in all_conversations:
            lang = conv.metadata.get('programming_language')
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
        
        if lang_counts:
            for lang, count in sorted(lang_counts.items()):
                print(f"   • {lang}: {count} conversations")
        else:
            print("   No programming language metadata found")
        
        # Difficulty distribution
        print("\n📈 DIFFICULTY DISTRIBUTION:")
        difficulty_counts = {}
        for conv in all_conversations:
            difficulty = conv.metadata.get('difficulty')
            if difficulty:
                current_count = difficulty_counts.get(difficulty, 0)
                difficulty_counts[difficulty] = current_count + 1
        
        if difficulty_counts:
            for difficulty, count in sorted(difficulty_counts.items()):
                print(f"   • {difficulty}: {count} conversations")
        
        print("\n" + "="*70)


if __name__ == '__main__':
    print("🚀 Starting Poe.com Conversation Pipeline Integration Test\n")
    
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
    
    if result.testsRun > 0:
        success_count = (result.testsRun - len(result.failures) -
                         len(result.errors))
        success_rate = success_count / result.testsRun * 100
        print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, trace in result.failures:
            print(f"- {test}: {trace}")
    
    if result.errors:
        print("\nERRORS:")
        for test, trace in result.errors:
            print(f"- {test}: {trace}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED - Pipeline integration validated!")
    else:
        print("\n❌ Some tests failed - check output above for details")
    
    sys.exit(0 if result.wasSuccessful() else 1)
