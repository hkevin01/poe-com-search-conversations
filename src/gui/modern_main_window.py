#!/usr/bin/env python3
"""
Modern Windows 11 GUI for Poe.com Conversation Manager
Enhanced with proper Windows 11 design guidelines and styling
"""

import json
import os
import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
    QLabel, QComboBox, QFrame, QMessageBox, QApplication, QFileDialog
)
from PyQt6.QtCore import Qt, QSize, QSettings, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QAction, QGuiApplication

# Add parent directory to path for database import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import ConversationDatabase

class ModernMainWindow(QMainWindow):
    """Main application window with Windows 11 design."""
    
    def __init__(self):
        super().__init__()
        self.conversations = []
        self.settings = None
        self.db = None
        
        # Initialize components
        self.init_database()
        self.setup_windows11_style()
        self.init_modern_ui()
        self.load_conversations()
    
    def setup_windows11_style(self):
        """Apply comprehensive light theme styling."""
        # Light theme color palette only
        self.colors = {
            'bg_primary': '#FFFFFF',
            'bg_secondary': '#FFFFFF', 
            'bg_card': '#FFFFFF',
            'bg_accent': '#0078D4',
            'bg_accent_hover': '#106EBE',
            'bg_accent_pressed': '#005A9E',
            'border': '#E1DFDD',
            'border_focus': '#0078D4',
            'success': '#107C10',
            'warning': '#FF8C00',
            'error': '#D13438',
        }
        
        # Apply comprehensive Windows 11 stylesheet
        style = f"""
        /* Main Window */
        QMainWindow {{
            background-color: {self.colors['bg_primary']};
            color: #000000;
            font-family: 'Segoe UI', 'San Francisco', system-ui, sans-serif;
            font-size: 14px;
        }}
        
        /* Headers and Titles */
        QLabel#titleLabel {{
            font-size: 28px;
            font-weight: 600;
            color: #000000;
            margin: 0px 0px 8px 0px;
        }}
        
        QLabel#subtitleLabel {{
            font-size: 14px;
            color: #333333;
            margin: 0px 0px 16px 0px;
        }}
        
        QLabel#sectionTitle {{
            font-size: 16px;
            font-weight: 600;
            color: #000000;
            margin: 8px 0px;
        }}
        
        /* All Labels Default */
        QLabel {{
            color: #000000;
        }}
        
        /* All Widgets Default */
        QWidget {{
            color: #000000;
        }}
        
        /* Cards and Frames */
        QFrame#cardFrame {{
            background-color: {self.colors['bg_card']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            padding: 20px;
            margin: 8px;
        }}
        
        /* Search Input */
        QLineEdit {{
            background-color: {self.colors['bg_card']};
            border: 2px solid {self.colors['border']};
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            color: #000000;
            min-height: 20px;
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
        
        /* Primary Buttons */
        QPushButton {{
            background-color: {self.colors['bg_accent']};
            color: #000000;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            min-width: 100px;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {self.colors['bg_accent_hover']};
            color: #000000;
        }}
        
        QPushButton:pressed {{
            background-color: {self.colors['bg_accent_pressed']};
            color: #000000;
        }}
        
        /* Secondary Buttons */
        QPushButton#secondaryButton {{
            background-color: {self.colors['bg_card']};
            color: #000000;
            border: 2px solid {self.colors['border']};
        }}
        
        QPushButton#secondaryButton:hover {{
            background-color: {self.colors['bg_primary']};
            border-color: #999999;
            color: #000000;
        }}
        
        /* Lists */
        QListWidget {{
            background-color: {self.colors['bg_card']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            outline: none;
            padding: 8px;
            color: #000000;
        }}
        
        QListWidget::item {{
            background-color: transparent;
            border: none;
            border-radius: 8px;
            padding: 16px;
            margin: 4px 0px;
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
            background-color: {self.colors['bg_card']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            padding: 20px;
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #000000;
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {self.colors['bg_card']};
            border: 2px solid {self.colors['border']};
            border-radius: 8px;
            padding: 8px 16px;
            min-width: 120px;
            min-height: 20px;
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
        
        /* Splitter */
        QSplitter::handle {{
            background-color: {self.colors['border']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 1px;
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {self.colors['bg_primary']};
            color: #000000;
            border-bottom: 1px solid {self.colors['border']};
            padding: 8px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 16px;
            border-radius: 6px;
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
        
        /* Status Bar */
        QStatusBar {{
            background-color: {self.colors['bg_secondary']};
            border-top: 1px solid {self.colors['border']};
            color: #333333;
            padding: 8px;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: #CCCCCC;
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: #999999;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
        """
        
        self.setStyleSheet(style)
    
    def init_modern_ui(self):
        """Initialize modern UI with Windows 11 design patterns."""
        # Window setup
        self.setWindowTitle("Poe.com Conversation Manager")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with proper spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Add header
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Add search section
        search_widget = self.create_search_section()
        main_layout.addWidget(search_widget)
        
        # Add main content
        content_widget = self.create_content_section()
        main_layout.addWidget(content_widget, 1)
        
        # Create menu and status bars
        self.create_menu_bar()
        self.create_status_bar()
    
    def create_header(self):
        """Create the modern header section."""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        # Main title
        title = QLabel("Conversation Manager")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Search and browse your Poe.com conversations")
        subtitle.setObjectName("subtitleLabel")
        header_layout.addWidget(subtitle)
        
        return header_frame
    
    def create_search_section(self):
        """Create the search section with modern styling."""
        search_frame = QFrame()
        search_frame.setObjectName("cardFrame")
        
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(16)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search conversations...")
        self.search_input.returnPressed.connect(self.search_conversations)
        search_layout.addWidget(self.search_input, 1)
        
        # Bot filter
        bot_label = QLabel("Bot:")
        search_layout.addWidget(bot_label)
        
        self.bot_filter = QComboBox()
        self.bot_filter.addItem("All Bots")
        self.bot_filter.currentTextChanged.connect(self.filter_conversations)
        search_layout.addWidget(self.bot_filter)
        
        # Buttons
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_conversations)
        search_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_btn)
        
        return search_frame
    
    def create_content_section(self):
        """Create the main content area."""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Left panel
        left_panel = self.create_conversation_list()
        splitter.addWidget(left_panel)
        
        # Right panel  
        right_panel = self.create_details_panel()
        splitter.addWidget(right_panel)
        
        # Set proportions
        splitter.setSizes([500, 1100])
        
        return splitter
    
    def create_conversation_list(self):
        """Create the conversation list panel."""
        panel = QFrame()
        panel.setMinimumWidth(400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Section title
        title = QLabel("Conversations")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # List widget
        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(self.show_conversation_details)
        layout.addWidget(self.conversation_list)
        
        return panel
    
    def create_details_panel(self):
        """Create the details panel."""
        panel = QFrame()
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Section title
        title = QLabel("Conversation Details")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Details area
        self.details_area = QTextEdit()
        self.details_area.setReadOnly(True)
        self.details_area.setPlaceholderText("Select a conversation to view details...")
        layout.addWidget(self.details_area)
        
        return panel
    
    # Include all the other necessary methods (init_database, load_conversations, etc.)
    # from the original file here...
    
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
    
    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        export_action = QAction('Export...', self)
        export_action.setShortcut('Ctrl+E')
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        refresh_action = QAction('Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.load_conversations)
        view_menu.addAction(refresh_action)
    
    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def load_conversations(self):
        """Load conversations from database."""
        if not self.db:
            return
        
        try:
            # Load all conversations
            conversations = self.db.search_conversations("")
            self.conversations = conversations
            self.populate_conversation_list(conversations)
            
            # Update bot filter
            bots = self.db.get_all_bots()
            self.update_bot_filter(bots)
            
            self.status_bar.showMessage(f"Loaded {len(conversations)} conversations")
            
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load data: {e}")
            self.status_bar.showMessage("Load error")
    
    def populate_conversation_list(self, conversations):
        """Populate the conversation list."""
        self.conversation_list.clear()
        
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
            
            self.conversation_list.addItem(item)
    
    def update_bot_filter(self, bots):
        """Update bot filter dropdown."""
        self.bot_filter.clear()
        self.bot_filter.addItem("All Bots")
        self.bot_filter.addItems(bots)
    
    def search_conversations(self):
        """Search conversations."""
        if not self.db:
            return
        
        query = self.search_input.text().strip()
        filters = {}
        
        bot_selection = self.bot_filter.currentText()
        if bot_selection != "All Bots":
            filters['bot_name'] = bot_selection
        
        try:
            conversations = self.db.search_conversations(query, filters)
            self.conversations = conversations
            self.populate_conversation_list(conversations)
            
            # Update status
            if query or filters:
                self.status_bar.showMessage(f"Found {len(conversations)} conversations matching search")
            else:
                self.status_bar.showMessage(f"Showing all {len(conversations)} conversations")
                
        except Exception as e:
            QMessageBox.warning(self, "Search Error", f"Search failed: {e}")
            self.status_bar.showMessage("Search error")
    
    def filter_conversations(self):
        """Filter conversations by bot."""
        self.search_conversations()
    
    def clear_search(self):
        """Clear search results."""
        self.search_input.clear()
        self.bot_filter.setCurrentIndex(0)
        self.load_conversations()
    
    def show_conversation_details(self, item):
        """Show conversation details."""
        conv = item.data(Qt.ItemDataRole.UserRole)
        if not conv:
            return
        
        # Create rich HTML content for better formatting
        html_content = f"""
        <div style="font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: #323130;">
            <div style="background-color: #F3F3F3; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="margin: 0 0 12px 0; color: #323130; font-size: 20px; font-weight: 600;">
                    {conv.title}
                </h2>
                <div style="display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 12px;">
                    <span style="color: #605E5C; font-size: 14px;">
                        <strong>Bot:</strong> {conv.bot_name or 'Unknown'}
                    </span>
                    <span style="color: #605E5C; font-size: 14px;">
                        <strong>Messages:</strong> {conv.message_count}
                    </span>
                    <span style="color: #605E5C; font-size: 14px;">
                        <strong>Date:</strong> {self.format_date(conv.created_at)}
                    </span>
                </div>
                <div style="margin-top: 8px;">
                    <a href="{conv.url}" style="color: #0078D4; text-decoration: none; font-size: 14px;">
                        View on Poe.com →
                    </a>
                </div>
            </div>
        """
        
        # Add conversation content
        if conv.content:
            try:
                messages = json.loads(conv.content)
                html_content += '<div style="margin-top: 20px;">'
                
                for i, message in enumerate(messages):
                    sender = message.get('sender', 'unknown')
                    content = message.get('content', '')
                    
                    # Style based on sender
                    if sender == 'user':
                        bg_color = '#E3F2FD'
                        sender_label = 'You'
                        sender_color = '#1976D2'
                    else:
                        bg_color = '#F5F5F5'
                        sender_label = conv.bot_name or 'Bot'
                        sender_color = '#424242'
                    
                    # Format message content
                    formatted_content = content.replace('\n', '<br>')
                    
                    html_content += f"""
                    <div style="margin-bottom: 16px; padding: 16px; background-color: {bg_color}; 
                                border-radius: 8px; border-left: 4px solid {sender_color};">
                        <div style="font-weight: 600; color: {sender_color}; margin-bottom: 8px; font-size: 14px;">
                            {sender_label}
                        </div>
                        <div style="color: #323130; font-size: 14px; line-height: 1.5;">
                            {formatted_content}
                        </div>
                    </div>
                    """
                
                html_content += '</div>'
                
            except json.JSONDecodeError:
                # Fallback for non-JSON content
                html_content += f"""
                <div style="background-color: #F5F5F5; padding: 16px; border-radius: 8px; margin-top: 20px;">
                    <h3 style="margin: 0 0 12px 0; color: #323130;">Content:</h3>
                    <div style="color: #323130; white-space: pre-wrap; font-size: 14px;">
                        {conv.content}
                    </div>
                </div>
                """
        else:
            html_content += """
            <div style="background-color: #FFF4E6; padding: 16px; border-radius: 8px; margin-top: 20px; 
                        border-left: 4px solid #FF8C00;">
                <div style="color: #8A8886; font-style: italic;">
                    No conversation content available.
                </div>
            </div>
            """
        
        html_content += '</div>'
        self.details_area.setHtml(html_content)
    
    def format_date(self, date_obj):
        """Format date in a user-friendly way."""
        if not date_obj:
            return "Unknown date"
        
        try:
            if isinstance(date_obj, str):
                date_obj = datetime.fromisoformat(date_obj.replace('Z', ''))
            
            now = datetime.now()
            diff = now - date_obj
            
            if diff.days == 0:
                return date_obj.strftime("Today at %I:%M %p")
            elif diff.days == 1:
                return date_obj.strftime("Yesterday at %I:%M %p")
            elif diff.days <= 7:
                return date_obj.strftime("%A at %I:%M %p")
            else:
                return date_obj.strftime("%B %d, %Y at %I:%M %p")
        except:
            return str(date_obj)[:16] if date_obj else "Unknown date"

def run_modern_gui():
    """Run the modern GUI application."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Poe.com Conversation Manager")
    app.setApplicationDisplayName("Conversation Manager")
    app.setApplicationVersion("2.0")
    
    # Create and show main window
    window = ModernMainWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(run_modern_gui())