"""
One-Click Setup and Token Detection System

This module provides automated token detection and setup wizard functionality
for Poe.com authentication, making the setup process seamless for users.
"""

import os
import json
import sqlite3
import tempfile
import subprocess
import platform
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QTextEdit, QMessageBox, QGroupBox, QRadioButton, QFileDialog,
    QLineEdit, QComboBox, QTabWidget, QWidget, QFormLayout, QCheckBox,
    QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon


class BrowserDetector:
    """Detect and extract cookies from popular browsers"""
    
    def __init__(self):
        self.system = platform.system()
        self.browsers_info = self._get_browser_paths()

    def _get_browser_paths(self) -> Dict[str, Dict[str, str]]:
        """Get browser cookie database paths for different OS"""
        if self.system == "Windows":
            return {
                "chrome": {
                    "name": "Google Chrome",
                    "cookie_path": os.path.expanduser(
                        "~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cookies"
                    ),
                    "login_data": os.path.expanduser(
                        "~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Login Data"
                    )
                },
                "edge": {
                    "name": "Microsoft Edge",
                    "cookie_path": os.path.expanduser(
                        "~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cookies"
                    ),
                    "login_data": os.path.expanduser(
                        "~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Login Data"
                    )
                },
                "firefox": {
                    "name": "Mozilla Firefox",
                    "cookie_path": self._find_firefox_profile_path("windows"),
                    "login_data": None
                }
            }
        elif self.system == "Darwin":  # macOS
            return {
                "chrome": {
                    "name": "Google Chrome",
                    "cookie_path": os.path.expanduser(
                        "~/Library/Application Support/Google/Chrome/Default/Cookies"
                    ),
                    "login_data": os.path.expanduser(
                        "~/Library/Application Support/Google/Chrome/Default/Login Data"
                    )
                },
                "safari": {
                    "name": "Safari",
                    "cookie_path": os.path.expanduser(
                        "~/Library/Cookies/Cookies.binarycookies"
                    ),
                    "login_data": None
                },
                "firefox": {
                    "name": "Mozilla Firefox",
                    "cookie_path": self._find_firefox_profile_path("macos"),
                    "login_data": None
                }
            }
        else:  # Linux
            return {
                "chrome": {
                    "name": "Google Chrome",
                    "cookie_path": os.path.expanduser(
                        "~/.config/google-chrome/Default/Cookies"
                    ),
                    "login_data": os.path.expanduser(
                        "~/.config/google-chrome/Default/Login Data"
                    )
                },
                "firefox": {
                    "name": "Mozilla Firefox", 
                    "cookie_path": self._find_firefox_profile_path("linux"),
                    "login_data": None
                }
            }

    def _find_firefox_profile_path(self, os_type: str) -> Optional[str]:
        """Find Firefox profile path with cookies"""
        if os_type == "windows":
            base_path = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")
        elif os_type == "macos":
            base_path = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
        else:  # Linux
            base_path = os.path.expanduser("~/.mozilla/firefox")
        
        if not os.path.exists(base_path):
            return None
        
        # Find the default profile (usually ends with .default or .default-release)
        try:
            for profile in os.listdir(base_path):
                if "default" in profile.lower():
                    cookie_file = os.path.join(base_path, profile, "cookies.sqlite")
                    if os.path.exists(cookie_file):
                        return cookie_file
        except (OSError, PermissionError):
            pass
        
        return None

    def get_available_browsers(self) -> List[Dict[str, str]]:
        """Get list of browsers with accessible cookie databases"""
        available = []
        
        for browser_id, info in self.browsers_info.items():
            if info["cookie_path"] and os.path.exists(info["cookie_path"]):
                available.append({
                    "id": browser_id,
                    "name": info["name"],
                    "path": info["cookie_path"]
                })
        
        return available

    def extract_poe_cookies(self, browser_id: str) -> Optional[Dict[str, str]]:
        """Extract Poe.com cookies from specified browser"""
        if browser_id not in self.browsers_info:
            return None
        
        browser_info = self.browsers_info[browser_id]
        cookie_path = browser_info["cookie_path"]
        
        if not cookie_path or not os.path.exists(cookie_path):
            return None
        
        try:
            # Create temporary copy of cookie database (browsers lock the file)
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Copy cookie database
            import shutil
            shutil.copy2(cookie_path, temp_path)
            
            # Extract cookies from database
            cookies = self._extract_cookies_from_db(temp_path, browser_id)
            
            # Clean up
            os.unlink(temp_path)
            
            return cookies
            
        except Exception as e:
            print(f"Error extracting cookies from {browser_id}: {e}")
            return None

    def _extract_cookies_from_db(self, db_path: str, browser_id: str) -> Dict[str, str]:
        """Extract Poe.com cookies from SQLite database"""
        cookies = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if browser_id == "firefox":
                # Firefox cookie schema
                query = """
                SELECT name, value FROM moz_cookies 
                WHERE host LIKE '%poe.com%' OR host LIKE '%.poe.com%'
                """
            else:
                # Chrome/Edge cookie schema  
                query = """
                SELECT name, value FROM cookies 
                WHERE host_key LIKE '%poe.com%' OR host_key LIKE '%.poe.com%'
                """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            for name, value in results:
                cookies[name] = value
            
            conn.close()
            
        except Exception as e:
            print(f"Database query error: {e}")
        
        return cookies


class TokenDetectionWorker(QThread):
    """Background worker for token detection"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    browser_found = pyqtSignal(str, dict)
    detection_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.detector = BrowserDetector()
        self.results = {}

    def run(self):
        """Run token detection process"""
        try:
            self.status_updated.emit("Detecting installed browsers...")
            available_browsers = self.detector.get_available_browsers()
            
            if not available_browsers:
                self.error_occurred.emit("No supported browsers found with accessible cookies")
                return
            
            total_browsers = len(available_browsers)
            
            for i, browser in enumerate(available_browsers):
                self.status_updated.emit(f"Checking {browser['name']}...")
                
                cookies = self.detector.extract_poe_cookies(browser['id'])
                
                if cookies and 'p-b' in cookies:
                    self.browser_found.emit(browser['name'], cookies)
                    self.results[browser['id']] = {
                        'name': browser['name'],
                        'cookies': cookies,
                        'token': cookies.get('p-b', ''),
                        'has_valid_token': bool(cookies.get('p-b'))
                    }
                
                progress = int((i + 1) / total_browsers * 100)
                self.progress_updated.emit(progress)
            
            self.detection_completed.emit(self.results)
            
        except Exception as e:
            self.error_occurred.emit(f"Detection failed: {str(e)}")


class SetupWizard(QDialog):
    """One-click setup wizard dialog"""
    
    setup_completed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Poe.com Conversation Manager - Setup Wizard")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.detected_tokens = {}
        self.selected_config = {}
        
        self.setup_ui()

    def setup_ui(self):
        """Setup wizard interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Setup Wizard")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #0078D4; margin: 20px 0px;")
        layout.addWidget(header)
        
        # Tab widget for wizard steps
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Step 1: Welcome & Introduction
        self.create_welcome_tab()
        
        # Step 2: Token Detection
        self.create_detection_tab()
        
        # Step 3: Configuration
        self.create_config_tab()
        
        # Step 4: Completion
        self.create_completion_tab()
        
        # Navigation buttons
        button_layout = QHBoxLayout()
        
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        button_layout.addWidget(self.back_button)
        
        button_layout.addStretch()
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.go_next)
        button_layout.addWidget(self.next_button)
        
        self.finish_button = QPushButton("Finish")
        self.finish_button.clicked.connect(self.finish_setup)
        self.finish_button.setVisible(False)
        button_layout.addWidget(self.finish_button)
        
        layout.addLayout(button_layout)

    def create_welcome_tab(self):
        """Create welcome/intro tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Welcome message
        welcome_text = """
        <h2>Welcome to Poe.com Conversation Manager!</h2>
        
        <p>This setup wizard will help you get started quickly by:</p>
        <ul>
        <li>🔍 <b>Automatically detecting</b> your Poe.com login tokens from supported browsers</li>
        <li>⚙️ <b>Configuring</b> your preferences and database settings</li>  
        <li>🚀 <b>Setting up</b> everything needed to start extracting conversations</li>
        </ul>
        
        <p>The setup process is completely automated and secure. Your credentials 
        never leave your computer.</p>
        
        <h3>Supported Browsers:</h3>
        <ul>
        <li>Google Chrome</li>
        <li>Microsoft Edge</li>
        <li>Mozilla Firefox</li>
        <li>Safari (macOS)</li>
        </ul>
        
        <p><b>Note:</b> Make sure you're logged in to Poe.com in at least one of these browsers.</p>
        """
        
        welcome_label = QLabel(welcome_text)
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet("padding: 20px; line-height: 1.6;")
        layout.addWidget(welcome_label)
        
        layout.addStretch()
        self.tabs.addTab(widget, "Welcome")

    def create_detection_tab(self):
        """Create token detection tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Detection info
        info_label = QLabel("🔍 Automatic Token Detection")
        info_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        info_label.setStyleSheet("color: #0078D4; margin-bottom: 15px;")
        layout.addWidget(info_label)
        
        desc_label = QLabel(
            "We'll now scan your browsers for Poe.com login tokens. "
            "This process is secure and happens entirely on your computer."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("margin-bottom: 20px;")
        layout.addWidget(desc_label)
        
        # Progress section
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to scan...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Start detection button
        self.detect_button = QPushButton("🔍 Start Automatic Detection")
        self.detect_button.clicked.connect(self.start_detection)
        self.detect_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 12px 24px; 
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
        """)
        layout.addWidget(self.detect_button)
        
        # Results area
        self.results_area = QTextEdit()
        self.results_area.setMaximumHeight(200)
        self.results_area.setPlaceholderText("Detection results will appear here...")
        self.results_area.setVisible(False)
        layout.addWidget(self.results_area)
        
        # Manual token entry (fallback)
        manual_group = QGroupBox("Manual Token Entry (Optional)")
        manual_layout = QFormLayout(manual_group)
        
        manual_info = QLabel(
            "If automatic detection fails, you can manually enter your p-b token from browser cookies."
        )
        manual_info.setWordWrap(True)
        manual_info.setStyleSheet("color: #666; margin-bottom: 10px;")
        manual_layout.addRow(manual_info)
        
        self.manual_token_input = QLineEdit()
        self.manual_token_input.setPlaceholderText("Enter p-b token here...")
        manual_layout.addRow("p-b Token:", self.manual_token_input)
        
        layout.addWidget(manual_group)
        layout.addStretch()
        
        self.tabs.addTab(widget, "Token Detection")

    def create_config_tab(self):
        """Create configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Config header
        config_label = QLabel("⚙️ Configuration")
        config_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        config_label.setStyleSheet("color: #0078D4; margin-bottom: 15px;")
        layout.addWidget(config_label)
        
        # Database settings
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout(db_group)
        
        self.db_path_input = QLineEdit()
        self.db_path_input.setText(
            os.path.join(os.getcwd(), "storage", "conversations.db")
        )
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_database_path)
        
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_input)
        db_path_layout.addWidget(browse_button)
        
        db_layout.addRow("Database Path:", db_path_layout)
        layout.addWidget(db_group)
        
        # Extraction settings
        extract_group = QGroupBox("Extraction Settings")
        extract_layout = QFormLayout(extract_group)
        
        self.auto_extract_checkbox = QCheckBox("Enable automatic extraction")
        self.auto_extract_checkbox.setChecked(True)
        extract_layout.addRow(self.auto_extract_checkbox)
        
        self.extract_interval = QComboBox()
        self.extract_interval.addItems(["15 minutes", "30 minutes", "1 hour", "6 hours", "12 hours", "24 hours"])
        self.extract_interval.setCurrentText("1 hour")
        extract_layout.addRow("Extraction Interval:", self.extract_interval)
        
        layout.addWidget(extract_group)
        
        layout.addStretch()
        self.tabs.addTab(widget, "Configuration")

    def create_completion_tab(self):
        """Create completion tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Completion header
        complete_label = QLabel("✅ Setup Complete!")
        complete_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        complete_label.setStyleSheet("color: #107C10; margin-bottom: 20px;")
        complete_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(complete_label)
        
        # Summary area
        self.summary_area = QTextEdit()
        self.summary_area.setReadOnly(True)
        self.summary_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        layout.addWidget(self.summary_area)
        
        # Next steps
        next_steps = QLabel("""
        <h3>What's Next?</h3>
        <ul>
        <li>🚀 <b>Start extracting</b> conversations using the main interface</li>
        <li>🔍 <b>Search and explore</b> your conversation history</li>
        <li>📊 <b>View statistics</b> and analytics about your conversations</li>
        <li>⚙️ <b>Adjust settings</b> anytime through the Tools menu</li>
        </ul>
        """)
        next_steps.setWordWrap(True)
        next_steps.setStyleSheet("padding: 20px; line-height: 1.6;")
        layout.addWidget(next_steps)
        
        self.tabs.addTab(widget, "Complete")

    def start_detection(self):
        """Start the token detection process"""
        self.detect_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Initializing detection...")
        
        # Start detection worker
        self.detection_worker = TokenDetectionWorker()
        self.detection_worker.progress_updated.connect(self.progress_bar.setValue)
        self.detection_worker.status_updated.connect(self.status_label.setText)
        self.detection_worker.browser_found.connect(self.on_browser_found)
        self.detection_worker.detection_completed.connect(self.on_detection_completed)
        self.detection_worker.error_occurred.connect(self.on_detection_error)
        self.detection_worker.start()

    def on_browser_found(self, browser_name: str, cookies: Dict[str, str]):
        """Handle browser with valid token found"""
        if not self.results_area.isVisible():
            self.results_area.setVisible(True)
        
        token = cookies.get('p-b', '')
        masked_token = token[:8] + "..." + token[-8:] if len(token) > 16 else token
        
        self.results_area.append(f"✅ Found valid token in {browser_name}")
        self.results_area.append(f"   Token: {masked_token}")
        self.results_area.append("")

    def on_detection_completed(self, results: Dict[str, Any]):
        """Handle detection completion"""
        self.detected_tokens = results
        self.detect_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if results:
            self.status_label.setText(f"✅ Detection complete! Found {len(results)} browser(s) with valid tokens.")
            self.next_button.setEnabled(True)
        else:
            self.status_label.setText("❌ No valid tokens found. Please use manual entry or ensure you're logged in to Poe.com.")

    def on_detection_error(self, error_message: str):
        """Handle detection errors"""
        self.detect_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ Detection failed: {error_message}")
        
        QMessageBox.warning(self, "Detection Error", f"Token detection failed:\n\n{error_message}")

    def browse_database_path(self):
        """Browse for database path"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Database Location",
            self.db_path_input.text(),
            "SQLite Database (*.db);;All Files (*)"
        )
        
        if file_path:
            self.db_path_input.setText(file_path)

    def go_back(self):
        """Go to previous tab"""
        current = self.tabs.currentIndex()
        if current > 0:
            self.tabs.setCurrentIndex(current - 1)
            self.update_navigation_buttons()

    def go_next(self):
        """Go to next tab"""
        current = self.tabs.currentIndex()
        
        # Validation before proceeding
        if current == 1:  # Token detection tab
            if not self.detected_tokens and not self.manual_token_input.text().strip():
                QMessageBox.warning(
                    self,
                    "No Token Found",
                    "Please run automatic detection or enter a token manually before proceeding."
                )
                return
        
        if current < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(current + 1)
            
            # Generate summary when reaching completion tab
            if current + 1 == self.tabs.count() - 1:
                self.generate_summary()
            
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Update navigation button states"""
        current = self.tabs.currentIndex()
        total_tabs = self.tabs.count()
        
        self.back_button.setEnabled(current > 0)
        self.next_button.setVisible(current < total_tabs - 1)
        self.finish_button.setVisible(current == total_tabs - 1)

    def generate_summary(self):
        """Generate setup summary"""
        summary = "<h3>Setup Summary</h3><ul>"
        
        # Token summary
        if self.detected_tokens:
            summary += f"<li><b>Tokens Found:</b> {len(self.detected_tokens)} browser(s)</li>"
            for browser_id, info in self.detected_tokens.items():
                summary += f"<li>  • {info['name']}: Valid token detected</li>"
        elif self.manual_token_input.text().strip():
            summary += "<li><b>Token:</b> Manually entered</li>"
        
        # Configuration summary
        summary += f"<li><b>Database:</b> {self.db_path_input.text()}</li>"
        summary += f"<li><b>Auto-extraction:</b> {'Enabled' if self.auto_extract_checkbox.isChecked() else 'Disabled'}</li>"
        
        if self.auto_extract_checkbox.isChecked():
            summary += f"<li><b>Extraction Interval:</b> {self.extract_interval.currentText()}</li>"
        
        summary += "</ul>"
        
        self.summary_area.setHtml(summary)

    def finish_setup(self):
        """Complete the setup process"""
        # Compile configuration
        config = {
            "tokens": self.detected_tokens,
            "manual_token": self.manual_token_input.text().strip(),
            "database_path": self.db_path_input.text(),
            "auto_extraction": self.auto_extract_checkbox.isChecked(),
            "extraction_interval": self.extract_interval.currentText(),
            "setup_completed": True
        }
        
        self.selected_config = config
        self.setup_completed.emit(config)
        self.accept()

    def get_setup_config(self) -> Dict[str, Any]:
        """Get the final setup configuration"""
        return self.selected_config


def show_setup_wizard(parent=None) -> Optional[Dict[str, Any]]:
    """Show setup wizard and return configuration"""
    wizard = SetupWizard(parent)
    
    if wizard.exec() == QDialog.DialogCode.Accepted:
        return wizard.get_setup_config()
    
    return None
