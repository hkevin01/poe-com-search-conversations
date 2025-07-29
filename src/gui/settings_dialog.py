#!/usr/bin/env python3
"""
Settings Dialog for Poe.com Conversation Manager
Comprehensive preferences and configuration management
"""

import sys
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QSpinBox, QPushButton,
    QFileDialog, QTabWidget, QWidget, QFormLayout, QMessageBox,
    QSlider
)
from PyQt6.QtCore import QSettings, pyqtSignal, Qt


class SettingsManager:
    """Centralized settings management for the application."""
    
    # Widget mapper for automatic synchronization
    WIDGET_MAPPERS = {
        'QCheckBox': ('isChecked', 'setChecked', bool),
        'QLineEdit': ('text', 'setText', str),
        'QSpinBox': ('value', 'setValue', int),
        'QComboBox': ('currentText', 'setCurrentText', str),
        'QSlider': ('value', 'setValue', int),
        'QTextEdit': ('toPlainText', 'setPlainText', str),
    }
    
    def __init__(self):
        self.settings = QSettings("PoeCM", "ConversationManager")
        
        # Default values for all settings
        self.defaults = {
            # Database settings
            'database_path': 'storage/conversations.db',
            'auto_backup': True,
            'backup_interval': 24,
            'max_backups': 5,
            
            # Extraction settings
            'extraction_limit': 10,
            'headless_browser': True,
            'wait_timeout': 30,
            'scroll_delay': 2,
            
            # Export settings
            'default_export_format': 'JSON',
            'export_include_metadata': True,
            'export_include_urls': True,
            'export_pretty_format': True,
            
            # Search settings
            'search_highlight': True,
            'search_case_sensitive': False,
            'search_max_results': 100,
            'search_include_content': True,
            
            # UI settings
            'theme': 'Light',
            'font_size': 14,
            'show_tooltips': True,
            'confirm_deletions': True,
            'window_geometry': '',
            'splitter_sizes': '',
            
            # Advanced settings
            'debug_mode': False,
            'log_level': 'INFO',
            'cache_size': 100,
            'thread_count': 4,
        }
    
    def get_value(self, key: str, default=None):
        """Get a setting value with proper type conversion."""
        if default is None:
            default = self.defaults.get(key)
        
        if key in self.defaults:
            expected_type = type(self.defaults[key])
            return self.settings.value(key, default, type=expected_type)
        return self.settings.value(key, default)
    
    def set_value(self, key: str, value: Any):
        """Set a setting value."""
        self.settings.setValue(key, value)
    
    def update_widgets_from_settings(self, widget_map: Dict[str, Any]):
        """Update widgets from stored settings."""
        for setting_name, widget in widget_map.items():
            widget_class = widget.__class__.__name__
            getter, setter, data_type = self.WIDGET_MAPPERS.get(widget_class, (None, None, None))
            
            if setter:
                value = self.get_value(setting_name)
                if value is not None:
                    try:
                        setter_func = getattr(widget, setter)
                        setter_func(value)
                    except Exception as e:
                        print(f"Error setting {setting_name}: {e}")
    
    def update_settings_from_widgets(self, widget_map: Dict[str, Any]):
        """Update settings from widget values."""
        for setting_name, widget in widget_map.items():
            widget_class = widget.__class__.__name__
            getter, setter, data_type = self.WIDGET_MAPPERS.get(widget_class, (None, None, None))
            
            if getter:
                try:
                    getter_func = getattr(widget, getter)
                    value = getter_func()
                    self.set_value(setting_name, value)
                except Exception as e:
                    print(f"Error getting {setting_name}: {e}")
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        for key, value in self.defaults.items():
            self.set_value(key, value)


# Global settings manager instance
settings_manager = SettingsManager()


class DatabaseSettingsTab(QWidget):
    """Database configuration settings tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Database path
        db_layout = QHBoxLayout()
        self.db_path = QLineEdit()
        self.db_browse = QPushButton("Browse...")
        self.db_browse.clicked.connect(self.browse_database)
        db_layout.addWidget(self.db_path)
        db_layout.addWidget(self.db_browse)
        layout.addRow("Database Path:", db_layout)
        
        # Backup settings
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QFormLayout()
        
        self.auto_backup = QCheckBox("Enable automatic backups")
        backup_layout.addRow(self.auto_backup)
        
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 168)
        self.backup_interval.setSuffix(" hours")
        backup_layout.addRow("Backup Interval:", self.backup_interval)
        
        self.max_backups = QSpinBox()
        self.max_backups.setRange(1, 50)
        self.max_backups.setSuffix(" files")
        backup_layout.addRow("Max Backup Files:", self.max_backups)
        
        backup_group.setLayout(backup_layout)
        layout.addRow(backup_group)
        
        self.setLayout(layout)
    
    def browse_database(self):
        """Browse for database file location."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Database Location", 
            self.db_path.text(), 
            "SQLite Database (*.db);;All Files (*)"
        )
        if file_path:
            self.db_path.setText(file_path)
    
    def get_widget_map(self):
        """Get the widget mapping for settings synchronization."""
        return {
            'database_path': self.db_path,
            'auto_backup': self.auto_backup,
            'backup_interval': self.backup_interval,
            'max_backups': self.max_backups,
        }


class ExtractionSettingsTab(QWidget):
    """Web scraping and extraction settings tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Extraction limits
        self.extraction_limit = QSpinBox()
        self.extraction_limit.setRange(1, 10000)
        self.extraction_limit.setSuffix(" conversations")
        layout.addRow("Default Extraction Limit:", self.extraction_limit)
        
        # Browser settings
        browser_group = QGroupBox("Browser Settings")
        browser_layout = QFormLayout()
        
        self.headless_browser = QCheckBox("Run browser in headless mode")
        browser_layout.addRow(self.headless_browser)
        
        self.wait_timeout = QSpinBox()
        self.wait_timeout.setRange(5, 300)
        self.wait_timeout.setSuffix(" seconds")
        browser_layout.addRow("Page Load Timeout:", self.wait_timeout)
        
        self.scroll_delay = QSpinBox()
        self.scroll_delay.setRange(1, 10)
        self.scroll_delay.setSuffix(" seconds")
        browser_layout.addRow("Scroll Delay:", self.scroll_delay)
        
        browser_group.setLayout(browser_layout)
        layout.addRow(browser_group)
        
        self.setLayout(layout)
    
    def get_widget_map(self):
        """Get the widget mapping for settings synchronization."""
        return {
            'extraction_limit': self.extraction_limit,
            'headless_browser': self.headless_browser,
            'wait_timeout': self.wait_timeout,
            'scroll_delay': self.scroll_delay,
        }


class ExportSettingsTab(QWidget):
    """Export format and options settings tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Default export format
        self.export_format = QComboBox()
        self.export_format.addItems(['JSON', 'CSV', 'Markdown', 'HTML', 'XML'])
        layout.addRow("Default Export Format:", self.export_format)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout()
        
        self.include_metadata = QCheckBox("Include conversation metadata")
        options_layout.addRow(self.include_metadata)
        
        self.include_urls = QCheckBox("Include conversation URLs")
        options_layout.addRow(self.include_urls)
        
        self.pretty_format = QCheckBox("Use pretty formatting (larger files)")
        options_layout.addRow(self.pretty_format)
        
        options_group.setLayout(options_layout)
        layout.addRow(options_group)
        
        self.setLayout(layout)
    
    def get_widget_map(self):
        """Get the widget mapping for settings synchronization."""
        return {
            'default_export_format': self.export_format,
            'export_include_metadata': self.include_metadata,
            'export_include_urls': self.include_urls,
            'export_pretty_format': self.pretty_format,
        }


class SearchSettingsTab(QWidget):
    """Search behavior and preferences settings tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Search behavior
        self.search_highlight = QCheckBox("Highlight search terms")
        layout.addRow(self.search_highlight)
        
        self.case_sensitive = QCheckBox("Case-sensitive search")
        layout.addRow(self.case_sensitive)
        
        self.include_content = QCheckBox("Search within message content")
        layout.addRow(self.include_content)
        
        # Search limits
        self.max_results = QSpinBox()
        self.max_results.setRange(10, 10000)
        self.max_results.setSuffix(" results")
        layout.addRow("Maximum Search Results:", self.max_results)
        
        self.setLayout(layout)
    
    def get_widget_map(self):
        """Get the widget mapping for settings synchronization."""
        return {
            'search_highlight': self.search_highlight,
            'search_case_sensitive': self.case_sensitive,
            'search_include_content': self.include_content,
            'search_max_results': self.max_results,
        }


class UISettingsTab(QWidget):
    """User interface and appearance settings tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Theme selection
        self.theme = QComboBox()
        self.theme.addItems(['Light', 'Dark', 'System'])
        layout.addRow("Theme:", self.theme)
        
        # Font size
        self.font_size = QSlider(Qt.Orientation.Horizontal)
        self.font_size.setRange(8, 24)
        self.font_size.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.font_size_label = QLabel("14px")
        self.font_size.valueChanged.connect(
            lambda v: self.font_size_label.setText(f"{v}px")
        )
        
        font_layout = QHBoxLayout()
        font_layout.addWidget(self.font_size)
        font_layout.addWidget(self.font_size_label)
        layout.addRow("Font Size:", font_layout)
        
        # UI options
        self.show_tooltips = QCheckBox("Show helpful tooltips")
        layout.addRow(self.show_tooltips)
        
        self.confirm_deletions = QCheckBox("Confirm before deleting items")
        layout.addRow(self.confirm_deletions)
        
        self.setLayout(layout)
    
    def get_widget_map(self):
        """Get the widget mapping for settings synchronization."""
        return {
            'theme': self.theme,
            'font_size': self.font_size,
            'show_tooltips': self.show_tooltips,
            'confirm_deletions': self.confirm_deletions,
        }


class AdvancedSettingsTab(QWidget):
    """Advanced and debugging settings tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Debug settings
        debug_group = QGroupBox("Debug Settings")
        debug_layout = QFormLayout()
        
        self.debug_mode = QCheckBox("Enable debug mode")
        debug_layout.addRow(self.debug_mode)
        
        self.log_level = QComboBox()
        self.log_level.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        debug_layout.addRow("Log Level:", self.log_level)
        
        debug_group.setLayout(debug_layout)
        layout.addRow(debug_group)
        
        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout()
        
        self.cache_size = QSpinBox()
        self.cache_size.setRange(10, 1000)
        self.cache_size.setSuffix(" MB")
        perf_layout.addRow("Cache Size:", self.cache_size)
        
        self.thread_count = QSpinBox()
        self.thread_count.setRange(1, 16)
        self.thread_count.setSuffix(" threads")
        perf_layout.addRow("Worker Threads:", self.thread_count)
        
        perf_group.setLayout(perf_layout)
        layout.addRow(perf_group)
        
        self.setLayout(layout)
    
    def get_widget_map(self):
        """Get the widget mapping for settings synchronization."""
        return {
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'cache_size': self.cache_size,
            'thread_count': self.thread_count,
        }


class SettingsDialog(QDialog):
    """Comprehensive settings dialog for the application."""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings - Poe.com Conversation Manager")
        self.setModal(True)
        self.resize(600, 500)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.database_tab = DatabaseSettingsTab()
        self.extraction_tab = ExtractionSettingsTab()
        self.export_tab = ExportSettingsTab()
        self.search_tab = SearchSettingsTab()
        self.ui_tab = UISettingsTab()
        self.advanced_tab = AdvancedSettingsTab()
        
        # Add tabs
        self.tabs.addTab(self.database_tab, "Database")
        self.tabs.addTab(self.extraction_tab, "Extraction")
        self.tabs.addTab(self.export_tab, "Export")
        self.tabs.addTab(self.search_tab, "Search")
        self.tabs.addTab(self.ui_tab, "Interface")
        self.tabs.addTab(self.advanced_tab, "Advanced")
        
        layout.addWidget(self.tabs)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.RestoreDefaults |
            QDialogButtonBox.StandardButton.Apply
        )
        
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def get_all_widget_maps(self):
        """Get all widget maps from all tabs."""
        all_maps = {}
        all_maps.update(self.database_tab.get_widget_map())
        all_maps.update(self.extraction_tab.get_widget_map())
        all_maps.update(self.export_tab.get_widget_map())
        all_maps.update(self.search_tab.get_widget_map())
        all_maps.update(self.ui_tab.get_widget_map())
        all_maps.update(self.advanced_tab.get_widget_map())
        return all_maps
    
    def load_settings(self):
        """Load settings from storage and update widgets."""
        widget_maps = self.get_all_widget_maps()
        settings_manager.update_widgets_from_settings(widget_maps)
    
    def save_settings(self):
        """Save settings from widgets to storage."""
        widget_maps = self.get_all_widget_maps()
        settings_manager.update_settings_from_widgets(widget_maps)
        self.settings_changed.emit()
    
    def apply_settings(self):
        """Apply settings without closing dialog."""
        self.save_settings()
        QMessageBox.information(self, "Settings", "Settings have been applied successfully.")
    
    def accept_settings(self):
        """Accept and save settings."""
        self.save_settings()
        self.accept()
    
    def restore_defaults(self):
        """Restore all settings to default values."""
        reply = QMessageBox.question(
            self, "Restore Defaults", 
            "Are you sure you want to restore all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            settings_manager.reset_to_defaults()
            self.load_settings()
            QMessageBox.information(self, "Settings", "All settings have been restored to defaults.")


def show_settings_dialog(parent=None):
    """Convenience function to show the settings dialog."""
    dialog = SettingsDialog(parent)
    return dialog.exec()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    dialog.show()
    sys.exit(app.exec())
