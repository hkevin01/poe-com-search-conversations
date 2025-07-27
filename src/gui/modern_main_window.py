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
        self.restore_window_state()
        self.load_conversations()
    
    def setup_windows11_style(self):
        """Apply comprehensive Windows 11 styling."""
        # Windows 11 Fluent Design color palette
        self.colors = {
            'bg_primary': '#F3F3F3',
            'bg_secondary': '#FAFAFA', 
            'bg_card': '#FFFFFF',
            'bg_accent': '#0078D4',
            'bg_accent_hover': '#106EBE',
            'bg_accent_pressed': '#005A9E',
            'text_primary': '#323130',
            'text_secondary': '#605E5C',
            'text_tertiary': '#8A8886',
            'text_white': '#FFFFFF',
            'border': '#E1DFDD',
            'border_focus': '#0078D4',
            'success': '#107C10',
            'warning': '#FF8C00',
            'error': '#D13438',
            'user_bg': '#E3F2FD',
            'bot_bg': '#F5F5F5'
        }
        
        # Apply comprehensive Windows 11 stylesheet
        style = f"""
        /* Main Window */
        QMainWindow {{
            background-color: {self.colors['bg_primary']};
            color: {self.colors['text_primary']};
            font-family: 'Segoe UI', 'San Francisco', system-ui, sans-serif;
            font-size: 14px;
        }}
        
        /* Headers and Titles */
        QLabel#titleLabel {{
            font-size: 28px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            margin: 0px 0px 8px 0px;
        }}
        
        QLabel#subtitleLabel {{
            font-size: 14px;
            color: {self.colors['text_secondary']};
            margin: 0px 0px 16px 0px;
        }}
        
        QLabel#sectionTitle {{
            font-size: 16px;
            font-weight: 600;
            color: {self.colors['text_primary']};
            margin: 8px 0px;
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
            color: {self.colors['text_primary']};
            min-height: 20px;
        }}
        
        QLineEdit:focus {{
            border-color: {self.colors['border_focus']};
            outline: none;
        }}
        
        QLineEdit:hover {{
            border-color: {self.colors['text_secondary']};
        }}
        
        /* Primary Buttons */
        QPushButton {{
            background-color: {self.colors['bg_accent']};
            color: {self.colors['text_white']};
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
        }}
        
        QPushButton:pressed {{
            background-color: {self.colors['bg_accent_pressed']};
        }}
        
        /* Secondary Buttons */
        QPushButton#secondaryButton {{
            background-color: {self.colors['bg_card']};
            color: {self.colors['text_primary']};
            border: 2px solid {self.colors['border']};
        }}
        
        QPushButton#secondaryButton:hover {{
            background-color: {self.colors['bg_primary']};
            border-color: {self.colors['text_secondary']};
        }}
        
        /* Lists */
        QListWidget {{
            background-color: {self.colors['bg_card']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            outline: none;
            padding: 8px;
        }}
        
        QListWidget::item {{
            background-color: transparent;
            border: none;
            border-radius: 8px;
            padding: 16px;
            margin: 4px 0px;
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
            background-color: {self.colors['bg_card']};
            border: 1px solid {self.colors['border']};
            border-radius: 12px;
            padding: 20px;
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: {self.colors['text_primary']};
        }}
        
        /* ComboBox */
        QComboBox {{
            background-color: {self.colors['bg_card']};
            border: 2px solid {self.colors['border']};
            border-radius: 8px;
            padding: 8px 16px;
            min-width: 120px;
            min-height: 20px;
        }}
        
        QComboBox:hover {{
            border-color: {self.colors['text_secondary']};
        }}
        
        QComboBox:focus {{
            border-color: {self.colors['border_focus']};
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
            color: {self.colors['text_primary']};
            border-bottom: 1px solid {self.colors['border']};
            padding: 8px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 16px;
            border-radius: 6px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.colors['bg_accent']};
            color: {self.colors['text_white']};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {self.colors['bg_secondary']};
            border-top: 1px solid {self.colors['border']};
            color: {self.colors['text_secondary']};
            padding: 8px;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {self.colors['text_tertiary']};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self.colors['text_secondary']};
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
    
    # Add placeholder methods that need to be implemented
    def load_conversations(self):
        """Load conversations from database."""
        pass
    
    def search_conversations(self):
        """Search conversations."""
        pass
    
    def filter_conversations(self):
        """Filter conversations by bot."""
        pass
    
    def clear_search(self):
        """Clear search results."""
        pass
    
    def show_conversation_details(self, item):
        """Show conversation details."""
        pass

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