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
        self.setup_style()
    
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
    
    def setup_style(self):
        """Setup Windows 11 style theme."""
        # Windows 11 color palette
        self.colors = {
            'bg_primary': '#F3F3F3',      # Light gray background
            'bg_secondary': '#FAFAFA',     # Lighter gray for cards
            'bg_accent': '#0078D4',        # Windows 11 blue
            'bg_accent_hover': '#106EBE',  # Darker blue for hover
            'bg_accent_pressed': '#005A9E', # Even darker for pressed
            'text_primary': '#323130',     # Dark gray text
            'text_secondary': '#605E5C',   # Medium gray text
            'text_tertiary': '#8A8886',    # Light gray text
            'text_white': '#FFFFFF',       # White text
            'border': '#E1DFDD',           # Light border
            'border_focus': '#0078D4',     # Blue border for focus
            'success': '#107C10',          # Green
            'warning': '#FF8C00',          # Orange
            'error': '#D13438',            # Red
        }
        
        # Windows 11 style sheet
        style = f"""
        /* Main Window */
        QMainWindow {{
            background-color: {self.colors['bg_primary']};
            color: {self.colors['text_primary']};
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 14px;
        }}
        
        /* Central Widget */
        QWidget#centralWidget {{
            background-color: {self.colors['bg_primary']};
            border: none;
        }}
        
        /* Search Section */
        QFrame#searchFrame {{
            background-color: {self.colors['bg_secondary']};
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 16px;
            margin: 8px;
        }}
        
        /* Search Input */
        QLineEdit {{
            background-color: white;
            border: 2px solid {self.colors['border']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
            color: {self.colors['text_primary']};
        }}
        
        QLineEdit:focus {{
            border-color: {self.colors['border_focus']};
            outline: none;
        }}
        
        QLineEdit:hover {{
            border-color: {self.colors['text_secondary']};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {self.colors['bg_accent']};
            color: {self.colors['text_white']};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {self.colors['bg_accent_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {self.colors['bg_accent_pressed']};
        }}
        
        QPushButton:disabled {{
            background-color: {self.colors['text_tertiary']};
            color: {self.colors['bg_primary']};
        }}
        
        /* Secondary Button */
        QPushButton#secondaryButton {{
            background-color: white;
            color: {self.colors['text_primary']};
            border: 2px solid {self.colors['border']};
        }}
        
        QPushButton#secondaryButton:hover {{
            background-color: {self.colors['bg_primary']};
            border-color: {self.colors['text_secondary']};
        }}
        
        /* List Widgets */
        QListWidget {{
            background-color: white;
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 4px;
            outline: none;
        }}
        
        QListWidget::item {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 12px;
            margin: 2px;
            color: {self.colors['text_primary']};
        }}
        
        QListWidget::item:selected {{
            background-color: {self.colors['bg_accent']};
            color: {self.colors['text_white']};
        }}
        
        QListWidget::item:hover {{
            background-color: {self.colors['bg_primary']};
        }}
        
        /* Text Areas */
        QTextEdit {{
            background-color: white;
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 12px;
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 14px;
            line-height: 1.5;
            color: {self.colors['text_primary']};
        }}
        
        QTextEdit:focus {{
            border-color: {self.colors['border_focus']};
        }}
        
        /* Splitter */
        QSplitter::handle {{
            background-color: {self.colors['border']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {self.colors['bg_secondary']};
            border-top: 1px solid {self.colors['border']};
            color: {self.colors['text_secondary']};
            padding: 4px 8px;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {self.colors['bg_primary']};
            color: {self.colors['text_primary']};
            border-bottom: 1px solid {self.colors['border']};
            padding: 4px 8px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.colors['bg_accent']};
            color: {self.colors['text_white']};
        }}
        
        /* Menus */
        QMenu {{
            background-color: white;
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 4px;
            color: {self.colors['text_primary']};
        }}
        
        QMenu::item {{
            padding: 8px 16px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {self.colors['bg_accent']};
            color: {self.colors['text_white']};
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {self.colors['bg_primary']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {self.colors['text_tertiary']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self.colors['text_secondary']};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        /* Labels */
        QLabel {{
            color: {self.colors['text_primary']};
            font-size: 14px;
        }}
        
        QLabel#titleLabel {{
            font-size: 20px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            margin: 8px 0px;
        }}
        
        QLabel#subtitleLabel {{
            font-size: 12px;
            color: {self.colors['text_secondary']};
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: white;
            border: 2px solid {self.colors['border']};
            border-radius: 6px;
            padding: 6px 12px;
            min-width: 120px;
        }}
        
        QComboBox:hover {{
            border-color: {self.colors['text_secondary']};
        }}
        
        QComboBox:focus {{
            border-color: {self.colors['border_focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: url(down-arrow.png);
            width: 12px;
            height: 12px;
        }}
        """
        
        self.setStyleSheet(style)
    
    def init_database(self):
        """Initialize database connection."""
        try:
            # Get project root by going up TWO levels from src/gui/
            current_dir = os.path.dirname(__file__)  # src/gui/
            src_dir = os.path.dirname(current_dir)   # src/
            project_root = os.path.dirname(src_dir)  # project root
            
            db_path = os.path.join(project_root, "storage", "conversations.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            print(f"🔍 GUI looking for database at: {db_path}")
            print(f"🔍 Database exists: {os.path.exists(db_path)}")
            
            self.db = ConversationDatabase(db_path)
            self.status_bar.showMessage(f"Database connected: {db_path}")
            print(f"🗄️  Database initialized: {db_path}")
            
            # Test database connection and show stats
            try:
                stats = self.db.get_stats()
                print(f"📊 Database stats: {stats['total_conversations']} conversations, {stats['total_messages']} messages")
            except Exception as e:
                print(f"⚠️  Could not get database stats: {e}")
                
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
        """Show about dialog with Windows 11 styling."""
        about_text = """
        <div style="font-family: 'Segoe UI', system-ui, sans-serif; text-align: center;">
            <h2 style="color: #323130; margin-bottom: 16px;">Poe.com Conversation Manager</h2>
            <p style="color: #605E5C; margin-bottom: 12px; font-size: 14px;">
                A modern tool for managing and searching your Poe.com conversations
            </p>
            <p style="color: #8A8886; font-size: 12px;">
                Built with PyQt6 and Windows 11 design principles
            </p>
        </div>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply Windows 11 styling to message box
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: white;
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
            }}
            QMessageBox QPushButton {{
                background-color: {self.colors['bg_accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {self.colors['bg_accent_hover']};
            }}
        """)
        
        msg.exec()
    
    def export_conversations(self):
        """Export conversations with a modern file dialog."""
        from PyQt6.QtWidgets import QFileDialog
        
        # Create file dialog with Windows 11 styling
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Export Conversations")
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setNameFilters([
            "JSON files (*.json)",
            "Markdown files (*.md)", 
            "CSV files (*.csv)",
            "All files (*.*)"
        ])
        file_dialog.setDefaultSuffix("json")
        
        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            filename = file_dialog.selectedFiles()[0]
            format_type = "json"
            
            if filename.endswith('.md'):
                format_type = "markdown"
            elif filename.endswith('.csv'):
                format_type = "csv"
            
            try:
                exported_file = self.db.export_conversations(format_type, filename)
                
                # Show success message
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Export Successful")
                msg.setText(f"Conversations exported successfully to:\n{exported_file}")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                
                self.status_bar.showMessage(f"Exported to {exported_file}", 3000)
                
            except Exception as e:
                # Show error message
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Export Failed")
                msg.setText(f"Failed to export conversations:\n{str(e)}")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Save window geometry for next session
        self.settings = QSettings("PoeCM", "ConversationManager")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        if self.db:
            self.db.close()
        
        event.accept()
    
    def restore_window_state(self):
        """Restore window state from settings."""
        try:
            from PyQt6.QtCore import QSettings
            
            self.settings = QSettings("PoeCM", "ConversationManager") 
            geometry = self.settings.value("geometry")
            window_state = self.settings.value("windowState")
            
            if geometry:
                self.restoreGeometry(geometry)
            else:
                # Default positioning
                self.resize(1400, 900)
                self.center_window()
                
            if window_state:
                self.restoreState(window_state)
                
        except Exception as e:
            print(f"Could not restore window state: {e}")
            self.center_window()
    
    def center_window(self):
        """Center the window on the screen."""
        from PyQt6.QtGui import QGuiApplication
        
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
        
    def apply_windows11_animations(self):
        """Apply subtle animations for Windows 11 feel."""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        # Create fade-in animation for the main window
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def showEvent(self, event):
        """Handle window show event with animation."""
        super().showEvent(event)
        
        # Start fade-in animation
        if hasattr(self, 'fade_animation'):
            self.fade_animation.start()
    
    def update_bot_filter(self):
        """Update the bot filter dropdown with available bots."""
        current_text = self.bot_filter.currentText()
        self.bot_filter.clear()
        self.bot_filter.addItem("All Bots")
        
        if self.db:
            try:
                bots = self.db.get_all_bots()
                for bot in bots:
                    if bot and bot.strip():
                        self.bot_filter.addItem(bot)
                
                # Restore selection if it still exists
                index = self.bot_filter.findText(current_text)
                if index >= 0:
                    self.bot_filter.setCurrentIndex(index)
                    
            except Exception as e:
                print(f"Error updating bot filter: {e}")
    
    def apply_dark_theme(self):
        """Apply dark theme for Windows 11 dark mode."""
        # Update colors for dark theme
        dark_colors = {
            'bg_primary': '#202020',
            'bg_secondary': '#2D2D2D',
            'bg_accent': '#0078D4',
            'bg_accent_hover': '#106EBE',
            'bg_accent_pressed': '#005A9E',
            'text_primary': '#FFFFFF',
            'text_secondary': '#E5E5E5',
            'text_tertiary': '#C0C0C0',
            'text_white': '#FFFFFF',
            'border': '#404040',
            'border_focus': '#0078D4',
            'success': '#107C10',
            'warning': '#FF8C00',
            'error': '#D13438',
        }
        
        # Apply dark theme (this would be called based on system theme detection)
        # Implementation would be similar to setup_style() but with dark colors