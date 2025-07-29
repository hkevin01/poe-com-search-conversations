import unittest
import os
import json
import subprocess
import sys
from src import quick_list_conversations
from src.database import ConversationDatabase, Conversation


class TestReadmeClaims(unittest.TestCase):
    def setUp(self):
        self.db_path = 'test_conversations.db'
        self.db = ConversationDatabase(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_database_schema_and_local_storage(self):
        info = self.db.get_database_info()
        self.assertIn('conversations', info['tables'])
        self.assertIn('conversations_fts', info['tables'])
        self.assertGreaterEqual(info['database_size_bytes'], 0)

    def test_add_and_search_conversation(self):
        conv = Conversation(
            poe_id='test1',
            title='Test Conversation',
            url='https://poe.com/chat/test1',
            bot_name='TestBot',
            message_count=2,
            tags=['test'],
            content=json.dumps([{"sender": "user", "content": "hi"}]),
            metadata={"difficulty": "easy"}
        )
        self.db.add_conversation(conv)
        results = self.db.search_conversations('Test Conversation')
        self.assertTrue(any(c.poe_id == 'test1' for c in results))

    def test_export_json(self):
        conv = Conversation(
            poe_id='test2',
            title='Export Test',
            url='https://poe.com/chat/test2',
            bot_name='TestBot',
            message_count=1,
            tags=['export'],
            content=json.dumps([{"sender": "user", "content": "hello"}]),
            metadata={}
        )
        self.db.add_conversation(conv)
        fname = self.db.export_conversations(format='json')
        self.assertTrue(os.path.exists(fname))
        with open(fname, encoding='utf-8') as f:
            data = json.load(f)
        self.assertTrue(any(c['poe_id'] == 'test2' for c in data))
        os.remove(fname)

    def test_export_csv_and_markdown(self):
        conv = Conversation(
            poe_id='test3',
            title='CSV Test',
            url='https://poe.com/chat/test3',
            bot_name='TestBot',
            message_count=1,
            tags=['csv'],
            content=json.dumps([{"sender": "user", "content": "csv"}]),
            metadata={}
        )
        self.db.add_conversation(conv)
        fname_csv = self.db.export_conversations(format='csv')
        fname_md = self.db.export_conversations(format='markdown')
        self.assertTrue(os.path.exists(fname_csv))
        self.assertTrue(os.path.exists(fname_md))
        os.remove(fname_csv)
        os.remove(fname_md)

    def test_delete_and_restore(self):
        conv = Conversation(
            poe_id='test4',
            title='Delete Test',
            url='https://poe.com/chat/test4',
            bot_name='TestBot',
            message_count=1,
            tags=['delete'],
            content=json.dumps([{"sender": "user", "content": "bye"}]),
            metadata={}
        )
        self.db.add_conversation(conv)
        backup = self.db.backup_database()
        self.assertTrue(os.path.exists(backup))
        self.assertTrue(self.db.delete_conversation('test4'))
        self.assertIsNone(self.db.get_conversation_by_poe_id('test4'))
        self.assertTrue(self.db.restore_database(backup))
        self.assertIsNotNone(self.db.get_conversation_by_poe_id('test4'))
        os.remove(backup)

    def test_tag_and_metadata_update(self):
        conv = Conversation(
            poe_id='test5',
            title='Tag Test',
            url='https://poe.com/chat/test5',
            bot_name='TestBot',
            message_count=1,
            tags=['tag1'],
            content=json.dumps([{"sender": "user", "content": "tag"}]),
            metadata={"foo": "bar"}
        )
        self.db.add_conversation(conv)
        self.assertTrue(
            self.db.update_conversation_tags('test5', ['tag2', 'tag3'])
        )
        self.assertTrue(
            self.db.update_conversation_metadata('test5', {"foo": "baz"})
        )
        c = self.db.get_conversation_by_poe_id('test5')
        self.assertIn('tag2', c.tags)
        self.assertEqual(c.metadata['foo'], 'baz')

    def test_cli_quick_list(self):
        # Assumes quick_list_conversations.py can be run with --config
        # and a valid config.
        config_path = os.path.join(
            os.path.dirname(__file__), '../config/poe_tokens.json.example'
        )
        if not os.path.exists(config_path):
            self.skipTest('No example config available')
        result = subprocess.run([
            sys.executable,
            'src/quick_list_conversations.py',
            '--config',
            config_path,
            '--no-headless'
        ], capture_output=True, text=True, check=True)
        self.assertIn('Found', result.stdout)
        self.assertIn('Saved to', result.stdout)

    def test_invalid_config(self):
        with self.assertRaises(FileNotFoundError):
            quick_list_conversations.load_tokens('nonexistent.json')
        with self.assertRaises(KeyError):
            # Create a temp config missing p-b
            tmp = 'tmp_invalid.json'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            try:
                quick_list_conversations.load_tokens(tmp)
            finally:
                os.remove(tmp)


if __name__ == '__main__':
    unittest.main()
