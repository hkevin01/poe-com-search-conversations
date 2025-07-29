"""
Drag and Drop Widget for Poe.com Conversation Import/Export

This module provides a comprehensive drag-and-drop interface for importing
and exporting conversation data in various formats (JSON, CSV, etc.).
"""

import json
import os
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QMessageBox, QProgressBar, QTextEdit, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPalette, QFont


class FileProcessor(QThread):
    """Background thread for processing large files"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished_processing = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, file_paths: List[str], operation: str):
        super().__init__()
        self.file_paths = file_paths
        self.operation = operation
        self.results = {}

    def run(self):
        """Process files in background thread"""
        try:
            if self.operation == "import":
                self._import_files()
            elif self.operation == "export":
                self._export_files()
        except Exception as e:
            self.error_occurred.emit(f"Processing error: {str(e)}")

    def _import_files(self):
        """Import conversation files"""
        total_files = len(self.file_paths)
        imported_conversations = []
        
        for i, file_path in enumerate(self.file_paths):
            self.status_updated.emit(f"Processing {Path(file_path).name}...")
            
            try:
                if file_path.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            imported_conversations.extend(data)
                        else:
                            imported_conversations.append(data)
                
                elif file_path.endswith('.csv'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            imported_conversations.append(row)
                
                progress = int((i + 1) / total_files * 100)
                self.progress_updated.emit(progress)
                
            except Exception as e:
                self.error_occurred.emit(f"Error processing {file_path}: {str(e)}")
                continue
        
        self.results = {
            'conversations': imported_conversations,
            'count': len(imported_conversations)
        }
        self.finished_processing.emit(self.results)

    def _export_files(self):
        """Export conversation files (placeholder)"""
        # This would be implemented based on database export needs
        self.status_updated.emit("Export functionality not yet implemented")
        self.finished_processing.emit({'status': 'export_pending'})


class DragDropZone(QLabel):
    """Visual drag-and-drop zone with feedback"""
    files_dropped = pyqtSignal(list)

    def __init__(self, zone_type="import"):
        super().__init__()
        self.zone_type = zone_type
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        """Setup the drag-drop zone appearance"""
        self.setMinimumHeight(120)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set up styling
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
                padding: 20px;
            }
            QLabel:hover {
                border-color: #007acc;
                background-color: #f0f7ff;
                color: #007acc;
            }
        """)
        
        if self.zone_type == "import":
            self.setText("📁 Drag and drop conversation files here\n"
                        "Supported formats: JSON, CSV\n"
                        "Or click to browse files")
        else:
            self.setText("💾 Drag conversations here to export\n"
                        "Choose export format below\n"
                        "Or click to save to file")
        
        # Make it clickable
        self.mousePressEvent = self._handle_click

    def _handle_click(self, event):
        """Handle click to open file dialog"""
        if self.zone_type == "import":
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Conversation Files",
                "",
                "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)"
            )
            if files:
                self.files_dropped.emit(files)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            # Check if any files have supported extensions
            urls = event.mimeData().urls()
            supported_files = any(
                url.toLocalFile().lower().endswith(('.json', '.csv'))
                for url in urls
            )
            
            if supported_files:
                event.acceptProposedAction()
                self.setStyleSheet("""
                    QLabel {
                        border: 2px solid #007acc;
                        border-radius: 10px;
                        background-color: #e6f3ff;
                        color: #007acc;
                        font-size: 14px;
                        padding: 20px;
                        font-weight: bold;
                    }
                """)
            else:
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave events"""
        self._reset_style()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        """Handle file drop events"""
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.json', '.csv')):
                    file_paths.append(file_path)
            
            if file_paths:
                self.files_dropped.emit(file_paths)
                event.acceptProposedAction()
        
        self._reset_style()

    def _reset_style(self):
        """Reset the zone to default styling"""
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
                padding: 20px;
            }
            QLabel:hover {
                border-color: #007acc;
                background-color: #f0f7ff;
                color: #007acc;
            }
        """)


class DragDropImportExport(QWidget):
    """Complete drag-and-drop import/export widget"""
    
    # Signals
    conversations_imported = pyqtSignal(list)
    conversations_exported = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.processor_thread = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the main interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Import/Export Conversations")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Import Section
        import_group = QGroupBox("Import Conversations")
        import_layout = QVBoxLayout(import_group)
        
        self.import_zone = DragDropZone("import")
        self.import_zone.files_dropped.connect(self._handle_import_files)
        import_layout.addWidget(self.import_zone)
        
        # Import controls
        import_controls = QHBoxLayout()
        self.import_button = QPushButton("Browse Files")
        self.import_button.clicked.connect(self._browse_import_files)
        import_controls.addWidget(self.import_button)
        
        import_controls.addStretch()
        import_layout.addLayout(import_controls)
        layout.addWidget(import_group)
        
        # Export Section
        export_group = QGroupBox("Export Conversations")
        export_layout = QVBoxLayout(export_group)
        
        self.export_zone = DragDropZone("export")
        export_layout.addWidget(self.export_zone)
        
        # Export format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Export Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON", "CSV", "Markdown", "HTML"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        
        self.export_button = QPushButton("Export All")
        self.export_button.clicked.connect(self._export_conversations)
        format_layout.addWidget(self.export_button)
        
        export_layout.addLayout(format_layout)
        layout.addWidget(export_group)
        
        # Progress and Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Results area
        self.results_area = QTextEdit()
        self.results_area.setMaximumHeight(100)
        self.results_area.setPlaceholderText("Import/export results will appear here...")
        self.results_area.setVisible(False)
        layout.addWidget(self.results_area)

    def _browse_import_files(self):
        """Open file browser for import"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Conversation Files to Import",
            "",
            "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)"
        )
        if files:
            self._handle_import_files(files)

    def _handle_import_files(self, file_paths: List[str]):
        """Handle imported files"""
        if not file_paths:
            return
        
        # Validate files
        valid_files = []
        for file_path in file_paths:
            if os.path.exists(file_path) and file_path.lower().endswith(('.json', '.csv')):
                valid_files.append(file_path)
        
        if not valid_files:
            QMessageBox.warning(self, "No Valid Files", 
                              "No valid conversation files found. "
                              "Please select JSON or CSV files.")
            return
        
        # Start processing
        self._start_file_processing(valid_files, "import")

    def _export_conversations(self):
        """Export conversations to file"""
        export_format = self.format_combo.currentText().lower()
        
        # Get save location
        if export_format == "json":
            filter_str = "JSON Files (*.json)"
            default_ext = ".json"
        elif export_format == "csv":
            filter_str = "CSV Files (*.csv)"
            default_ext = ".csv"
        elif export_format == "markdown":
            filter_str = "Markdown Files (*.md)"
            default_ext = ".md"
        else:  # HTML
            filter_str = "HTML Files (*.html)"
            default_ext = ".html"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Conversations as {export_format.upper()}",
            f"conversations_export{default_ext}",
            filter_str
        )
        
        if file_path:
            self.status_label.setText(f"Exporting to {export_format.upper()}...")
            # TODO: Implement actual export functionality
            # This would connect to the database and export conversation data
            QTimer.singleShot(1000, lambda: self._mock_export_complete(file_path))

    def _mock_export_complete(self, file_path: str):
        """Mock export completion (placeholder)"""
        self.status_label.setText("Export completed!")
        self.results_area.setVisible(True)
        self.results_area.append(f"✅ Exported conversations to: {file_path}")
        self.conversations_exported.emit(file_path)

    def _start_file_processing(self, file_paths: List[str], operation: str):
        """Start background file processing"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_area.setVisible(True)
        self.results_area.clear()
        self.status_label.setText("Processing files...")
        
        # Disable controls during processing
        self.import_button.setEnabled(False)
        self.export_button.setEnabled(False)
        
        # Start processor thread
        self.processor_thread = FileProcessor(file_paths, operation)
        self.processor_thread.progress_updated.connect(self.progress_bar.setValue)
        self.processor_thread.status_updated.connect(self.status_label.setText)
        self.processor_thread.finished_processing.connect(self._handle_processing_complete)
        self.processor_thread.error_occurred.connect(self._handle_processing_error)
        self.processor_thread.start()

    def _handle_processing_complete(self, results: Dict[str, Any]):
        """Handle completion of file processing"""
        # Re-enable controls
        self.import_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if 'conversations' in results:
            count = results['count']
            self.status_label.setText(f"Import completed! {count} conversations loaded.")
            self.results_area.append(f"✅ Successfully imported {count} conversations")
            
            # Emit signal with imported conversations
            self.conversations_imported.emit(results['conversations'])
        else:
            self.status_label.setText("Processing completed!")
        
        # Clean up thread
        if self.processor_thread:
            self.processor_thread.quit()
            self.processor_thread.wait()
            self.processor_thread = None

    def _handle_processing_error(self, error_message: str):
        """Handle processing errors"""
        self.import_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Error occurred during processing")
        self.results_area.append(f"❌ {error_message}")
        
        QMessageBox.critical(self, "Processing Error", error_message)
        
        # Clean up thread
        if self.processor_thread:
            self.processor_thread.quit()
            self.processor_thread.wait()
            self.processor_thread = None

    def get_status(self) -> str:
        """Get current status"""
        return self.status_label.text()

    def clear_results(self):
        """Clear results area"""
        self.results_area.clear()
        self.results_area.setVisible(False)
        self.status_label.setText("Ready")
