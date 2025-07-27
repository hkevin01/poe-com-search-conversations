#!/usr/bin/env python3
"""
Poe.com Conversation Manager - Main GUI Window
Phase 4: GUI & User Experience Implementation
"""

import sys
import os
from typing import List, Optional
from datetime import datetime
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
    QPushButton, QLabel, QComboBox, QStatusBar, QMenuBar, QMenu,
    QMessageBox, QProgressBar, QFrame, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction, QPalette, QColor

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.database import ConversationDatabase, Conversation
except ImportError:
    # Fallback for direct execution
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from database import ConversationDatabase, Conversation


class ConversationListWidget(QListWidget):
    """Custom list widget for displaying conversations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.conversations = []
        
        # Set up styling
        self.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
                margin: 2px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
    
    def load_conversations(self, conversations: List[Conversation]):
        """Load conversations into the list widget."""
        self.clear()
        self.conversations = conversations
        
        for conv in conversations:
            item = QListWidgetItem()
            
            # Format display text
            title = conv.title[:60] + "..." if len(conv.title) > 60 else conv.title
            bot_name = f" [{conv.bot_name}]" if conv.bot_name else ""
            date_str = conv.created_at.strftime("%Y-%m-%d") if conv.created_at else "Unknown"
            message_info = f" ({conv.message_count} msgs)" if conv.message_count > 0 else ""
            
            display_text = f"{title}{bot_name}{message_info}\n📅 {date_str}"
            
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, conv)
            
            self.addItem(item)


class ConversationViewer(QScrollArea):
    """Widget for displaying conversation content."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create main content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.setWidget(self.content_widget)
        
        # Initialize with empty state
        self.show_empty_state()
        
        # Styling
        self.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
        """)
    
    def show_empty_state(self):
        """Show empty state when no conversation is selected."""
        self.clear_content()
        
        empty_label = QLabel("Select a conversation to view its content")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 16px;
                padding: 50px;
            }
        """)
        
        self.content_layout.addWidget(empty_label)
    
    def clear_content(self):
        """Clear all content from the viewer."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def display_conversation(self, conversation: Conversation):
        """Display a conversation's content."""
        self.clear_content()
        
        # Conversation header
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.Box)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title_label = QLabel(conversation.title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        
        # Metadata
        metadata_layout = QHBoxLayout()
        
        if conversation.bot_name:
            bot_label = QLabel(f"🤖 Bot: {conversation.bot_name}")
            metadata_layout.addWidget(bot_label)
        
        if conversation.created_at:
            date_label = QLabel(f"📅 Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}")
            metadata_layout.addWidget(date_label)
        
        msg_label = QLabel(f"💬 Messages: {conversation.message_count}")
        metadata_layout.addWidget(msg_label)
        
        metadata_layout.addStretch()
        header_layout.addLayout(metadata_layout)
        
        # Tags
        if conversation.tags:
            tags_label = QLabel(f"🏷️ Tags: {', '.join(conversation.tags)}")
            tags_label.setStyleSheet("color: #007bff;")
            header_layout.addWidget(tags_label)
        
        self.content_layout.addWidget(header_frame)
        
        # Messages
        if conversation.content:
            try:
                messages = json.loads(conversation.content)
                self.display_messages(messages)
            except json.JSONDecodeError:
                # Fallback for non-JSON content
                text_widget = QTextEdit()
                text_widget.setPlainText(conversation.content)
                text_widget.setReadOnly(True)
                self.content_layout.addWidget(text_widget)
        else:
            no_content_label = QLabel("No message content available")
            no_content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_content_label.setStyleSheet("color: #6c757d; padding: 20px;")
            self.content_layout.addWidget(no_content_label)
        
        # Add stretch to push content to top
        self.content_layout.addStretch()
    
    def display_messages(self, messages: List[dict]):
        """Display individual messages."""
        for i, message in enumerate(messages):
            message_frame = QFrame()
            message_layout = QVBoxLayout(message_frame)
            
            # Determine sender style
            is_user = message.get('sender', '').lower() == 'user'
            
            if is_user:
                message_frame.setStyleSheet("""
                    QFrame {
                        background-color: #e3f2fd;
                        border: 1px solid #2196f3;
                        border-radius: 10px;
                        margin: 5px 50px 5px 5px;
                        padding: 10px;
                    }
                """)
                sender_text = "👤 You"
            else:
                message_frame.setStyleSheet("""
                    QFrame {
                        background-color: #f1f8e9;
                        border: 1px solid #4caf50;
                        border-radius: 10px;
                        margin: 5px 5px 5px 50px;
                        padding: 10px;
                    }
                """)
                sender_text = "🤖 Bot"
            
            # Sender label
            sender_label = QLabel(sender_text)
            sender_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            message_layout.addWidget(sender_label)
            
            # Message content
            content_text = QTextEdit()
            content_text.setPlainText(message.get('content', ''))
            content_text.setReadOnly(True)
            content_text.setMaximumHeight(200)  # Limit height
            content_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            # Style the text area
            content_text.setStyleSheet("""
                QTextEdit {
                    border: none;
                    background-color: transparent;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11px;
                    line-height: 1.4;
                }
            """)
            
            message_layout.addWidget(content_text)
            self.content_layout.addWidget(message_frame)


class SearchWidget(QWidget):
    """Search interface widget."""
    
    search_requested = pyqtSignal(str, dict)  # query, filters
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search conversations...")
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input)
        
        # Bot filter
        self.bot_combo = QComboBox()
        self.bot_combo.addItem("All Bots")
        layout.addWidget(self.bot_combo)
        
        # Search button
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.perform_search)
        layout.addWidget(search_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_search)
        layout.addWidget(clear_btn)
    
    def update_bot_list(self, bots: List[str]):
        """Update the bot filter dropdown."""
        current_selection = self.bot_combo.currentText()
        self.bot_combo.clear()
        self.bot_combo.addItem("All Bots")
        self.bot_combo.addItems(bots)
        
        # Restore selection if possible
        index = self.bot_combo.findText(current_selection)
        if index >= 0:
            self.bot_combo.setCurrentIndex(index)
    
    def perform_search(self):
        """Emit search request signal."""
        query = self.search_input.text().strip()
        
        filters = {}
        bot_selection = self.bot_combo.currentText()
        if bot_selection != "All Bots":
            filters['bot_name'] = bot_selection
        
        self.search_requested.emit(query, filters)
    
    def clear_search(self):
        """Clear search inputs."""
        self.search_input.clear()
        self.bot_combo.setCurrentIndex(0)
        self.search_requested.emit("", {})


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.db = None
        self.current_conversations = []
        
        self.init_ui()
        self.init_database()
        self.load_initial_data()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Poe.com Conversation Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Search widget
        self.search_widget = SearchWidget()
        self.search_widget.search_requested.connect(self.perform_search)
        main_layout.addWidget(self.search_widget)
        
        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Conversation list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        list_label = QLabel("Conversations")
        list_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(list_label)
        
        self.conversation_list = ConversationListWidget()
        self.conversation_list.itemClicked.connect(self.on_conversation_selected)
        left_layout.addWidget(self.conversation_list)
        
        # Right panel - Conversation viewer
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        viewer_label = QLabel("Conversation Details")
        viewer_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(viewer_label)
        
        self.conversation_viewer = ConversationViewer()
        right_layout.addWidget(self.conversation_viewer)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])  # Initial sizes
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Menu bar
        self.create_menus()
        
        # Apply styling
        self.apply_styling()
    
    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_data)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        stats_action = QAction("Statistics", self)
        stats_action.triggered.connect(self.show_statistics)
        view_menu.addAction(stats_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def apply_styling(self):
        """Apply application-wide styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel {
                color: #212529;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
    
    def init_database(self):
        """Initialize database connection."""
        try:
            # Use correct storage directory path (go up from src to project root)
            project_root = os.path.dirname(os.path.dirname(__file__))
            db_path = os.path.join(project_root, "storage", "conversations.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            self.db = ConversationDatabase(db_path)
            self.status_bar.showMessage(f"Database connected: {db_path}")
            print(f"🗄️  Database initialized: {db_path}")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", 
                               f"Failed to connect to database: {e}")
            self.status_bar.showMessage("Database error")
    
    def load_initial_data(self):
        """Load initial data into the interface."""
        if not self.db:
            return
        
        try:
            # Load all conversations
            conversations = self.db.search_conversations("")
            self.current_conversations = conversations
            self.conversation_list.load_conversations(conversations)
            
            # Update bot filter
            bots = self.db.get_all_bots()
            self.search_widget.update_bot_list(bots)
            
            self.status_bar.showMessage(f"Loaded {len(conversations)} conversations")
            
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load data: {e}")
            self.status_bar.showMessage("Load error")
    
    def perform_search(self, query: str, filters: dict):
        """Perform search and update conversation list."""
        if not self.db:
            return
        
        try:
            conversations = self.db.search_conversations(query, filters)
            self.current_conversations = conversations
            self.conversation_list.load_conversations(conversations)
            
            # Clear viewer
            self.conversation_viewer.show_empty_state()
            
            # Update status
            if query or filters:
                self.status_bar.showMessage(f"Found {len(conversations)} conversations matching search")
            else:
                self.status_bar.showMessage(f"Showing all {len(conversations)} conversations")
                
        except Exception as e:
            QMessageBox.warning(self, "Search Error", f"Search failed: {e}")
            self.status_bar.showMessage("Search error")
    
    def on_conversation_selected(self, item: QListWidgetItem):
        """Handle conversation selection."""
        conversation = item.data(Qt.ItemDataRole.UserRole)
        if conversation:
            self.conversation_viewer.display_conversation(conversation)
            self.status_bar.showMessage(f"Viewing: {conversation.title}")
    
    def refresh_data(self):
        """Refresh all data."""
        self.load_initial_data()
    
    def show_statistics(self):
        """Show database statistics."""
        if not self.db:
            return
        
        try:
            stats = self.db.get_stats()
            
            stats_text = f"""
Database Statistics:

Total Conversations: {stats['total_conversations']}
Unique Bots: {stats['unique_bots']}
Total Messages: {stats['total_messages']}
Average Messages per Conversation: {stats['avg_messages_per_conversation']}

Bot Distribution:
"""
            for bot, count in list(stats['bot_distribution'].items())[:10]:
                stats_text += f"  {bot}: {count} conversations\n"
            
            QMessageBox.information(self, "Statistics", stats_text)
            
        except Exception as e:
            QMessageBox.warning(self, "Statistics Error", f"Failed to get statistics: {e}")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
Poe.com Conversation Manager

A tool for extracting, storing, and searching conversations from Poe.com.

Phase 4: GUI & User Experience
Version: 4.0.0-beta

Features:
• Local SQLite database storage
• Full-text search capabilities
• Conversation browsing and viewing
• Bot categorization and filtering
• Export functionality

Privacy-focused • Open Source • Local Processing
        """
        QMessageBox.about(self, "About", about_text.strip())


def run_gui():
    """Run the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Poe.com Conversation Manager")
    app.setApplicationVersion("4.0.0-beta")
    app.setOrganizationName("Poe Search")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())