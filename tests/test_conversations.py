import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from quick_list_conversations import load_tokens, setup_browser, extract_conversations

class TestConfig:
    def test_load_tokens_success(self):
        """Test successful token loading"""
        test_tokens = {"p-b": "test_pb_token", "p-lat": "test_lat_token"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_tokens, f)
            config_path = f.name
        
        try:
            tokens = load_tokens(config_path)
            assert tokens["p-b"] == "test_pb_token"
            assert tokens["p-lat"] == "test_lat_token"
        finally:
            os.unlink(config_path)
    
    def test_load_tokens_missing_file(self):
        """Test error when config file doesn't exist"""
        with pytest.raises(FileNotFoundError):
            load_tokens("/nonexistent/path.json")
    
    def test_load_tokens_missing_pb(self):
        """Test error when p-b token is missing"""
        test_tokens = {"p-lat": "test_lat_token"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_tokens, f)
            config_path = f.name
        
        try:
            with pytest.raises(KeyError):
                load_tokens(config_path)
        finally:
            os.unlink(config_path)

class TestBrowser:
    @patch('quick_list_conversations.webdriver.Chrome')
    def test_setup_browser_headless(self, mock_chrome):
        """Test browser setup in headless mode"""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver = setup_browser(headless=True)
        
        # Check that Chrome was called with options
        mock_chrome.assert_called_once()
        # Check that implicitly_wait was called
        mock_driver.implicitly_wait.assert_called_once_with(10)
    
    @patch('quick_list_conversations.webdriver.Chrome')
    def test_setup_browser_visible(self, mock_chrome):
        """Test browser setup in visible mode"""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver = setup_browser(headless=False)
        
        mock_chrome.assert_called_once()
        mock_driver.implicitly_wait.assert_called_once_with(10)

class TestConversationExtraction:
    def test_extract_conversations_empty(self):
        """Test conversation extraction with no results"""
        mock_driver = MagicMock()
        mock_driver.find_elements.return_value = []
        mock_driver.execute_script.side_effect = [1000, 1000]  # For scroll detection
        
        with patch('quick_list_conversations.scroll_to_bottom'):
            conversations = extract_conversations(mock_driver)
            assert conversations == []
    
    def test_extract_conversations_with_links(self):
        """Test conversation extraction with valid links"""
        mock_driver = MagicMock()
        
        # Mock link elements
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://poe.com/chat/12345"
        mock_link.text = "Test Conversation"
        
        mock_driver.find_elements.side_effect = [
            [mock_link],  # First call for links
            []           # Second call for tiles
        ]
        mock_driver.execute_script.side_effect = [1000, 1000]  # For scroll detection
        
        with patch('quick_list_conversations.scroll_to_bottom'):
            conversations = extract_conversations(mock_driver)
            
            assert len(conversations) == 1
            assert conversations[0]["title"] == "Test Conversation"
            assert conversations[0]["url"] == "https://poe.com/chat/12345"
            assert conversations[0]["method"] == "link"