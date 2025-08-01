"""
UI Styles and Themes for the Poe.com Conversation Manager
"""

# Main application stylesheet
MAIN_STYLE = """
QMainWindow {
    background-color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #000000;
}

QLabel {
    color: #000000;
    font-size: 11px;
}

QWidget {
    color: #000000;
}

QPushButton {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
}

QPushButton:hover {
    background-color: #0056b3;
}

QPushButton:pressed {
    background-color: #004085;
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
    font-size: 11px;
    color: #000000;
}

QLineEdit:focus, QComboBox:focus {
    border-color: #007bff;
    outline: none;
    color: #000000;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
    background-color: white;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    color: #000000;
    selection-background-color: #007bff;
    selection-color: #000000;
}

QComboBox QAbstractItemView::item {
    background-color: white;
    color: #000000;
    padding: 8px;
    border: none;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #e3f2fd;
    color: #000000;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #007bff;
    color: #000000;
}

QTextEdit {
    border: 1px solid #dee2e6;
    border-radius: 4px;
    background-color: white;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
    line-height: 1.4;
    color: #000000;
}

QScrollBar:vertical {
    background-color: #f8f9fa;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #ced4da;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #adb5bd;
}

QStatusBar {
    background-color: white;
    border-top: 1px solid #dee2e6;
    font-size: 10px;
    color: #000000;
}

QMenuBar {
    background-color: white;
    border-bottom: 1px solid #dee2e6;
    color: #000000;
}

QMenuBar::item {
    padding: 8px 12px;
    color: #000000;
}

QMenuBar::item:selected {
    background-color: #e9ecef;
    color: #000000;
}

QMenu {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    color: #000000;
}

QMenu::item {
    padding: 8px 16px;
    color: #000000;
    background-color: white;
}

QMenu::item:selected {
    background-color: #007bff;
    color: #000000;
}

QMenu::item:hover {
    background-color: #e3f2fd;
    color: #000000;
}

QMenu::separator {
    height: 1px;
    background-color: #dee2e6;
    margin: 4px 8px;
}
"""

# Conversation list specific styles
CONVERSATION_LIST_STYLE = """
QListWidget {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    padding: 5px;
    font-size: 11px;
}

QListWidget::item {
    padding: 12px;
    border-bottom: 1px solid #e9ecef;
    margin: 2px;
    border-radius: 3px;
    background-color: white;
}

QListWidget::item:selected {
    background-color: #007bff;
    color: #000000;
}

QListWidget::item:hover {
    background-color: #e3f2fd;
    color: #000000;
}
"""

# Message styles for different senders
USER_MESSAGE_STYLE = """
QFrame {
    background-color: #e3f2fd;
    border: 1px solid #2196f3;
    border-radius: 10px;
    margin: 5px 50px 5px 5px;
    padding: 10px;
}
"""

BOT_MESSAGE_STYLE = """
QFrame {
    background-color: #f1f8e9;
    border: 1px solid #4caf50;
    border-radius: 10px;
    margin: 5px 5px 5px 50px;
    padding: 10px;
}
"""

# Search widget styles
SEARCH_WIDGET_STYLE = """
QWidget {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    padding: 10px;
}
"""

# Conversation viewer styles
CONVERSATION_VIEWER_STYLE = """
QScrollArea {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 5px;
}

QFrame {
    margin: 5px;
}
"""

# Header frame style
HEADER_FRAME_STYLE = """
QFrame {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    padding: 15px;
    margin: 5px;
}
"""

# Color scheme - Light theme only
COLORS = {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'light': '#ffffff',
    'white': '#ffffff',
    'border': '#dee2e6',
    'text': '#000000',
    'text_muted': '#666666'
}

# Font configuration
FONTS = {
    'default': ('Segoe UI', 11),
    'header': ('Segoe UI', 14, 'bold'),
    'title': ('Segoe UI', 16, 'bold'),
    'small': ('Segoe UI', 9),
    'code': ('Consolas', 10)
}


def get_message_style(is_user: bool) -> str:
    """Get the appropriate style for a message based on sender."""
    return USER_MESSAGE_STYLE if is_user else BOT_MESSAGE_STYLE


def get_color(color_name: str) -> str:
    """Get a color value by name."""
    return COLORS.get(color_name, COLORS['text'])


def get_font_config(font_name: str) -> tuple:
    """Get font configuration by name."""
    return FONTS.get(font_name, FONTS['default'])