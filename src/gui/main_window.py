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
    QMessageBox, QProgressBar, QFrame, QScrollArea, QGroupBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QAction, QPalette, QColor, QGuiApplication

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
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
                color: #000000;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
                margin: 2px;
                border-radius: 3px;
                color: #000000;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: #000000;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
                color: #000000;
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
                color: #000000;
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
        """Display a conversation's content with enhanced styling."""
        self.clear_content()
        
        # Conversation header with enhanced styling
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.Box)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #0078D4;
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        # Title with enhanced styling
        title_label = QLabel(conversation.title)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        title_label.setStyleSheet("""
            QLabel {
                color: #0078D4;
                margin-bottom: 15px;
                padding: 10px;
                background-color: #F0F8FF;
                border-radius: 8px;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Metadata section with cards
        metadata_frame = QFrame()
        metadata_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-radius: 8px;
                padding: 15px;
                margin: 5px 0px;
            }
        """)
        metadata_layout = QHBoxLayout(metadata_frame)
        
        # Bot info card
        if conversation.bot_name:
            bot_card = QLabel(f"🤖 {conversation.bot_name}")
            bot_card.setStyleSheet("""
                QLabel {
                    background-color: #E8F5E8;
                    color: #2E7D32;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    border: 1px solid #4CAF50;
                }
            """)
            metadata_layout.addWidget(bot_card)
        
        # Date card
        if conversation.created_at:
            date_card = QLabel(f"📅 {conversation.created_at.strftime('%B %d, %Y at %I:%M %p')}")
            date_card.setStyleSheet("""
                QLabel {
                    background-color: #FFF3E0;
                    color: #E65100;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    border: 1px solid #FF9800;
                }
            """)
            metadata_layout.addWidget(date_card)
        
        # Message count card
        msg_card = QLabel(f"💬 {conversation.message_count} messages")
        msg_card.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                color: #0277BD;
                padding: 8px 12px;
                border-radius: 6px;
                font-weight: bold;
                border: 1px solid #2196F3;
            }
        """)
        metadata_layout.addWidget(msg_card)
        
        metadata_layout.addStretch()
        header_layout.addWidget(metadata_frame)
        
        # Tags section
        if conversation.tags:
            tags_frame = QFrame()
            tags_frame.setStyleSheet("""
                QFrame {
                    background-color: #F3E5F5;
                    border-radius: 8px;
                    padding: 10px;
                    margin: 5px 0px;
                }
            """)
            tags_layout = QHBoxLayout(tags_frame)
            tags_label = QLabel("🏷️ Tags:")
            tags_label.setStyleSheet("font-weight: bold; color: #7B1FA2;")
            tags_layout.addWidget(tags_label)
            
            for tag in conversation.tags:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    QLabel {
                        background-color: #9C27B0;
                        color: white;
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        margin: 2px;
                    }
                """)
                tags_layout.addWidget(tag_label)
            
            tags_layout.addStretch()
            header_layout.addWidget(tags_frame)
        
        self.content_layout.addWidget(header_frame)
        
        # Conversation separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("""
            QFrame {
                color: #0078D4;
                background-color: #0078D4;
                height: 3px;
                margin: 20px 10px;
            }
        """)
        self.content_layout.addWidget(separator)
        
        # Messages section with title
        messages_title = QLabel("💬 Conversation Messages")
        messages_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        messages_title.setStyleSheet("""
            QLabel {
                color: #0078D4;
                padding: 15px 10px 10px 10px;
                margin: 10px;
            }
        """)
        self.content_layout.addWidget(messages_title)
        
        # Messages
        if conversation.content:
            try:
                messages = json.loads(conversation.content)
                self.display_enhanced_messages(messages, conversation.bot_name)
            except json.JSONDecodeError:
                # Fallback for non-JSON content with enhanced styling
                fallback_frame = QFrame()
                fallback_frame.setStyleSheet("""
                    QFrame {
                        background-color: #FFF8E1;
                        border: 2px solid #FFB300;
                        border-radius: 12px;
                        padding: 20px;
                        margin: 10px;
                    }
                """)
                fallback_layout = QVBoxLayout(fallback_frame)
                
                warning_label = QLabel("⚠️ Raw Content (Non-structured)")
                warning_label.setStyleSheet("""
                    QLabel {
                        color: #E65100;
                        font-weight: bold;
                        font-size: 14px;
                        margin-bottom: 10px;
                    }
                """)
                fallback_layout.addWidget(warning_label)
                
                text_widget = QTextEdit()
                text_widget.setPlainText(conversation.content)
                text_widget.setReadOnly(True)
                text_widget.setStyleSheet("""
                    QTextEdit {
                        background-color: white;
                        border: 1px solid #FFB300;
                        border-radius: 8px;
                        padding: 15px;
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-size: 12px;
                        line-height: 1.6;
                        color: #000000;
                    }
                """)
                fallback_layout.addWidget(text_widget)
                self.content_layout.addWidget(fallback_frame)
        else:
            # Enhanced no content message
            no_content_frame = QFrame()
            no_content_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFEBEE;
                    border: 2px dashed #E57373;
                    border-radius: 12px;
                    padding: 40px;
                    margin: 20px;
                }
            """)
            no_content_layout = QVBoxLayout(no_content_frame)
            
            no_content_icon = QLabel("📭")
            no_content_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_content_icon.setStyleSheet("font-size: 48px; margin-bottom: 10px;")
            no_content_layout.addWidget(no_content_icon)
            
            no_content_label = QLabel("No conversation content available")
            no_content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_content_label.setStyleSheet("""
                QLabel {
                    color: #C62828;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            no_content_layout.addWidget(no_content_label)
            
            self.content_layout.addWidget(no_content_frame)
        
        # Add stretch to push content to top
        self.content_layout.addStretch()
    
    def display_enhanced_messages(self, messages: List[dict], bot_name: str = None):
        """Display messages with enhanced styling and formatting."""
        for i, message in enumerate(messages):
            # Determine sender info
            sender = message.get('sender', '').lower()
            is_user = sender == 'user'
            content = message.get('content', '').strip()
            
            if not content:
                continue
                
            # Create message container
            message_container = QFrame()
            message_container.setStyleSheet("""
                QFrame {
                    background: transparent;
                    margin: 5px 0px;
                }
            """)
            container_layout = QVBoxLayout(message_container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create message bubble
            bubble_frame = QFrame()
            bubble_layout = QVBoxLayout(bubble_frame)
            bubble_layout.setContentsMargins(15, 12, 15, 12)
            bubble_layout.setSpacing(8)
            
            if is_user:
                # User message styling
                bubble_frame.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #E3F2FD, stop:1 #BBDEFB);
                        border: 2px solid #2196F3;
                        border-radius: 15px;
                        margin: 8px 80px 8px 20px;
                    }
                """)
                
                # User header
                user_header = QLabel("👤 You")
                user_header.setStyleSheet("""
                    QLabel {
                        color: #1565C0;
                        font-weight: bold;
                        font-size: 13px;
                        margin-bottom: 5px;
                        background: transparent;
                    }
                """)
                bubble_layout.addWidget(user_header)
                
            else:
                # Bot message styling
                bot_display_name = bot_name or "Assistant"
                bubble_frame.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #F1F8E9, stop:1 #DCEDC8);
                        border: 2px solid #4CAF50;
                        border-radius: 15px;
                        margin: 8px 20px 8px 80px;
                    }
                """)
                
                # Bot header
                bot_header = QLabel(f"🤖 {bot_display_name}")
                bot_header.setStyleSheet("""
                    QLabel {
                        color: #2E7D32;
                        font-weight: bold;
                        font-size: 13px;
                        margin-bottom: 5px;
                        background: transparent;
                    }
                """)
                bubble_layout.addWidget(bot_header)
            
            # Format and display message content
            formatted_content = self.format_message_content(content)
            content_label = QLabel()
            content_label.setText(formatted_content)
            content_label.setWordWrap(True)
            content_label.setTextFormat(Qt.TextFormat.RichText)
            content_label.setOpenExternalLinks(True)
            content_label.setStyleSheet("""
                QLabel {
                    color: #000000;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 13px;
                    line-height: 1.6;
                    background: transparent;
                    padding: 0px;
                    margin: 0px;
                }
            """)
            bubble_layout.addWidget(content_label)
            
            # Message timestamp (if available)
            timestamp = message.get('timestamp')
            if timestamp:
                time_label = QLabel(f"🕐 {timestamp}")
                time_label.setStyleSheet("""
                    QLabel {
                        color: #666666;
                        font-size: 11px;
                        font-style: italic;
                        margin-top: 5px;
                        background: transparent;
                    }
                """)
                time_label.setAlignment(Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft)
                bubble_layout.addWidget(time_label)
            
            container_layout.addWidget(bubble_frame)
            self.content_layout.addWidget(message_container)
            
            # Add spacing between messages
            if i < len(messages) - 1:
                spacer = QFrame()
                spacer.setFixedHeight(10)
                spacer.setStyleSheet("background: transparent;")
                self.content_layout.addWidget(spacer)
    
    def format_message_content(self, content: str) -> str:
        """Format message content with better typography and structure."""
        import re
        
        # Escape HTML first
        content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Convert line breaks to HTML
        content = content.replace('\n\n', '</p><p>').replace('\n', '<br>')
        
        # Wrap in paragraphs
        if content.strip():
            content = f'<p>{content}</p>'
        
        # Format code blocks (```code```)
        content = re.sub(
            r'```(.*?)```',
            r'<div style="background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 4px; padding: 10px; margin: 8px 0; font-family: Consolas, monospace; font-size: 12px; color: #000;"><pre>\1</pre></div>',
            content,
            flags=re.DOTALL
        )
        
        # Format inline code (`code`)
        content = re.sub(
            r'`([^`]+)`',
            r'<code style="background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: Consolas, monospace; color: #d63384;">\1</code>',
            content
        )
        
        # Format bold text (**text**)
        content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)
        
        # Format italic text (*text*)
        content = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', content)
        
        # Format URLs
        url_pattern = r'https?://[^\s<>"\']*'
        content = re.sub(
            url_pattern,
            r'<a href="\g<0>" style="color: #0078D4; text-decoration: none;">\g<0></a>',
            content
        )
        
        # Format numbered lists
        lines = content.split('<br>')
        formatted_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.\s', line):
                if not in_list:
                    formatted_lines.append('<ol style="margin: 8px 0; padding-left: 20px;">')
                    in_list = True
                item_text = re.sub(r'^\d+\.\s', '', line)
                formatted_lines.append(f'<li style="margin: 4px 0; color: #000;">{item_text}</li>')
            else:
                if in_list:
                    formatted_lines.append('</ol>')
                    in_list = False
                if line:
                    formatted_lines.append(line)
        
        if in_list:
            formatted_lines.append('</ol>')
        
        content = '<br>'.join(formatted_lines)
        
        # Format bullet lists
        content = re.sub(
            r'<br>[-•*]\s([^<]+)',
            r'<br><ul style="margin: 4px 0; padding-left: 20px;"><li style="margin: 2px 0; color: #000;">\1</li></ul>',
            content
        )
        
        # Clean up extra spacing
        content = re.sub(r'<p>\s*</p>', '', content)
        content = re.sub(r'<br>\s*<br>', '<br>', content)
        
        return content


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
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QWidget {
                color: #000000;
            }
            QPushButton {
                background-color: #007bff;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #004085;
                color: #000000;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #000000;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                color: #000000;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #007bff;
                outline: none;
                color: #000000;
            }
        """)
    
    def setup_style(self):
        """Setup clean light theme."""
        # Clean light color palette
        self.colors = {
            'bg_primary': '#FFFFFF',      # Pure white background
            'bg_secondary': '#FFFFFF',    # White for cards
            'bg_accent': '#0078D4',       # Windows 11 blue
            'bg_accent_hover': '#106EBE', # Darker blue for hover
            'bg_accent_pressed': '#005A9E', # Even darker for pressed
            'border': '#E1DFDD',          # Light border
            'border_focus': '#0078D4',    # Blue border for focus
            'success': '#107C10',         # Green
            'warning': '#FF8C00',         # Orange
            'error': '#D13438',           # Red
        }
        
        # Windows 11 style sheet
        style = f"""
        /* Main Window */
        QMainWindow {{
            background-color: {self.colors['bg_primary']};
            color: #000000;
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 14px;
        }}
        
        /* Central Widget */
        QWidget#centralWidget {{
            background-color: {self.colors['bg_primary']};
            border: none;
            color: #000000;
        }}
        
        /* All Widgets Default */
        QWidget {{
            color: #000000;
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
            color: #000000;
        }}
        
        QLineEdit:focus {{
            border-color: {self.colors['border_focus']};
            outline: none;
            color: #000000;
        }}
        
        QLineEdit:hover {{
            border-color: #999999;
            color: #000000;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {self.colors['bg_accent']};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {self.colors['bg_accent_hover']};
            color: white;
        }}
        
        QPushButton:pressed {{
            background-color: {self.colors['bg_accent_pressed']};
            color: white;
        }}
        
        QPushButton:disabled {{
            background-color: #CCCCCC;
            color: #666666;
        }}
        
        /* Secondary Button */
        QPushButton#secondaryButton {{
            background-color: white;
            color: #000000;
            border: 2px solid {self.colors['border']};
        }}
        
        QPushButton#secondaryButton:hover {{
            background-color: {self.colors['bg_primary']};
            border-color: #999999;
            color: #000000;
        }}
        
        /* List Widgets */
        QListWidget {{
            background-color: white;
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 4px;
            outline: none;
            color: #000000;
        }}
        
        QListWidget::item {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 12px;
            margin: 2px;
            color: #000000;
        }}
        
        QListWidget::item:selected {{
            background-color: {self.colors['bg_accent']};
            color: #000000;
        }}
        
        QListWidget::item:hover {{
            background-color: {self.colors['bg_primary']};
            color: #000000;
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
            color: #000000;
        }}
        
        QTextEdit:focus {{
            border-color: {self.colors['border_focus']};
            color: #000000;
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
            color: #333333;
            padding: 4px 8px;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {self.colors['bg_primary']};
            color: #000000;
            border-bottom: 1px solid {self.colors['border']};
            padding: 4px 8px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
            color: #000000;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.colors['bg_accent']};
            color: #000000;
        }}
        
        /* Menus */
        QMenu {{
            background-color: white;
            border: 1px solid {self.colors['border']};
            border-radius: 8px;
            padding: 4px;
            color: #000000;
        }}
        
        QMenu::item {{
            padding: 8px 16px;
            border-radius: 4px;
            color: #000000;
            background-color: white;
        }}
        
        QMenu::item:selected {{
            background-color: {self.colors['bg_accent']};
            color: #000000;
        }}
        
        QMenu::item:hover {{
            background-color: #e3f2fd;
            color: #000000;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {self.colors['border']};
            margin: 4px 8px;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {self.colors['bg_primary']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: #CCCCCC;
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: #999999;
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        
        /* Labels */
        QLabel {{
            color: #000000;
            font-size: 14px;
        }}
        
        QLabel#titleLabel {{
            font-size: 20px;
            font-weight: 600;
            color: #000000;
            margin: 8px 0px;
        }}
        
        QLabel#subtitleLabel {{
            font-size: 12px;
            color: #333333;
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: white;
            border: 2px solid {self.colors['border']};
            border-radius: 6px;
            padding: 6px 12px;
            min-width: 120px;
            color: #000000;
        }}
        
        QComboBox:hover {{
            border-color: #999999;
            color: #000000;
        }}
        
        QComboBox:focus {{
            border-color: {self.colors['border_focus']};
            color: #000000;
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
            background-color: white;
        }}
        
        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: white;
            border: 1px solid {self.colors['border']};
            border-radius: 4px;
            color: #000000;
            selection-background-color: {self.colors['bg_accent']};
            selection-color: #000000;
        }}
        
        QComboBox QAbstractItemView::item {{
            background-color: white;
            color: #000000;
            padding: 8px;
            border: none;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: #e3f2fd;
            color: #000000;
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background-color: {self.colors['bg_accent']};
            color: #000000;
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
                color: #000000;
            }}
            QMessageBox QPushButton {{
                background-color: {self.colors['bg_accent']};
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {self.colors['bg_accent_hover']};
                color: #000000;
            }}
        """)
        
        msg.exec()
    
    def export_conversations(self):
        """Export conversations with a modern file dialog."""
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
        try:
            settings = QSettings("PoeCM", "ConversationManager")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
        except Exception as e:
            print(f"Could not save window state: {e}")
        
        if self.db:
            self.db.close()
        
        event.accept()
    
    def restore_window_state(self):
        """Restore window state from settings."""
        try:
            settings = QSettings("PoeCM", "ConversationManager")
            geometry = settings.value("geometry")
            window_state = settings.value("windowState")
            
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
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
        
    def apply_windows11_animations(self):
        """Apply subtle animations for Windows 11 feel."""
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
    
    
def run_gui():
    """Run the GUI application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Poe.com Conversation Manager")
    app.setApplicationDisplayName("Conversation Manager")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("PoeCM")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())