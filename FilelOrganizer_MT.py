# Multithreaded version of FIelOrganizer.py
# This file is a direct copy of FIelOrganizer.py, to be refactored for multithreading.

import sys
import os
import json
import re
import subprocess
import requests
import shutil
import glob
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QListWidget, QLabel, QTextEdit, QMessageBox, QHBoxLayout, QComboBox, QLineEdit,
    QSplitter, QTreeView, QFileSystemModel, QMenu, QAction, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QCheckBox, QDialog, QProgressBar,
    QMainWindow, QDockWidget, QInputDialog, QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPalette, QColor
from langchain.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM
from FIelOrganizer import OpenRouterLLM, MistralLLM  # added missing imports for LLM providers

# Import secure storage
try:
    from secure_storage import SecureStorage
    SECURE_STORAGE_AVAILABLE = True
except ImportError:
    SECURE_STORAGE_AVAILABLE = False
    print("Warning: cryptography package not available. API keys will not be encrypted.")

# Allowed file extensions based on the prompt template
ALLOWED_EXTENSIONS_VFX = {'.exr', '.dpx', '.tif', '.png', '.mov', '.mxf', '.avi', '.psd', '.ai', '.jpg', '.mp4', '.docx', '.pdf', '.xlsx', '.pptx', '.wav', '.mp3', '.aiff', '.nk', '.aep', '.prproj', '.drp', '.xml', '.edl', '.json', '.txt', '.aaf',
    '.fbx', '.obj', '.max', '.c4d', '.abc', '.blend', '.ma', '.mb', '.3ds', '.stl', '.ply', '.gltf', '.glb', '.usd', '.usda', '.usdc', '.usdz', '.xsi', '.lwo', '.lws', '.bgeo', '.bgeo.sc', '.vdb', '.prt', '.rib', '.ass', '.ifc', '.dae', '.igs', '.iges', '.step', '.stp', '.x3d', '.wrl', '.vrml', '.dxf', '.dwg', '.skp', '.sldprt', '.sldasm', '.objf', '.fbx7', '.3mf', '.amf', '.c4d', '.max', '.abc'}
ALLOWED_EXTENSIONS_COMMERCIAL = {'.exr', '.dpx', '.tif', '.png', '.mov', '.mxf', '.avi', '.psd', '.ai', '.jpg', '.mp4', '.docx', '.pdf', '.xlsx', '.pptx', '.wav', '.mp3', '.aiff', '.nk', '.aep', '.prproj', '.drp', '.xml', '.edl', '.json', '.txt', '.aaf',
    '.fbx', '.obj', '.max', '.c4d', '.abc', '.blend', '.ma', '.mb', '.3ds', '.stl', '.ply', '.gltf', '.glb', '.usd', '.usda', '.usdc', '.usdz', '.xsi', '.lwo', '.lws', '.bgeo', '.bgeo.sc', '.vdb', '.prt', '.rib', '.ass', '.ifc', '.dae', '.igs', '.iges', '.step', '.stp', '.x3d', '.wrl', '.vrml', '.dxf', '.dwg', '.skp', '.sldprt', '.sldasm', '.objf', '.fbx7', '.3mf', '.amf', '.c4d', '.max', '.abc'}

# OpenRouter popular models
OPENROUTER_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4-turbo",
    "google/gemini-pro-1.5",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-405b-instruct",
    "meta-llama/llama-3.1-70b-instruct",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-large",
    "mistralai/mistral-medium",
    "qwen/qwen-2.5-72b-instruct",
    "deepseek/deepseek-chat"
]

# Mistral models for dropdown selection
MISTRAL_MODELS = [
    "mistral-tiny",
    "mistral-small",
    "mistral-medium",
    "mistral-large-latest"
]

# --- Load prompt templates from Markdown files ---
def load_prompt_from_md(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    prompt_lines = [line for line in lines if not line.strip().startswith('#') or line.strip() == '#']
    return ''.join(prompt_lines)

PROMPT_TEMPLATE_KENT = load_prompt_from_md(os.path.join(os.path.dirname(__file__), 'prompt_kent.md'))
PROMPT_TEMPLATE_SPHERE = load_prompt_from_md(os.path.join(os.path.dirname(__file__), 'prompt_sphere.md'))

class FileClassifierWorker(QThread):
    progress_update = pyqtSignal(int, str)  # percent, message
    batch_result = pyqtSignal(list)  # list of (src, dst)
    log_message = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, valid_files, batch_size, project_root, folder_depth, structure_choice, get_llm_instance, get_folder_structure, prompt_kent, prompt_sphere):
        super().__init__()
        self.valid_files = valid_files
        self.batch_size = batch_size
        self.project_root = project_root
        self.folder_depth = folder_depth
        self.structure_choice = structure_choice
        self.get_llm_instance = get_llm_instance
        self.get_folder_structure = get_folder_structure
        self.prompt_kent = prompt_kent
        self.prompt_sphere = prompt_sphere
        self._is_running = True

    def run(self):
        try:
            total_files = len(self.valid_files)
            num_batches = (total_files + self.batch_size - 1) // self.batch_size
            all_results = []
            for batch_idx in range(num_batches):
                if not self._is_running:
                    break
                batch_files = self.valid_files[batch_idx * self.batch_size : (batch_idx + 1) * self.batch_size]
                formatted_filenames = "\n".join([os.path.basename(f) for f in batch_files])
                percent = int((batch_idx / num_batches) * 100)
                self.progress_update.emit(percent, f"Sending batch {batch_idx+1}/{num_batches} to AI for classification...")
                # Get actual project structure
                if os.path.isdir(self.project_root):
                    project_structure = self.get_folder_structure(self.project_root, max_depth=self.folder_depth)
                else:
                    project_structure = "(Project folder does not exist or is not accessible)"
                if self.structure_choice == "KENT":
                    prompt = self.prompt_kent.replace('{file_list}', formatted_filenames).replace('{project_root}', self.project_root).replace('{project_structure}', project_structure)
                else:
                    prompt = self.prompt_sphere.replace('{file_list}', formatted_filenames).replace('{project_root}', self.project_root).replace('{project_structure}', project_structure)
                try:
                    llm = self.get_llm_instance()
                    self.progress_update.emit(percent, f"Waiting for AI response for batch {batch_idx+1}/{num_batches}...")
                    response = llm.invoke(prompt)
                    self.log_message.emit(f"Raw AI response for batch {batch_idx+1}:\n{response}")
                    match = re.search(r'\{{[\s\S]*\}}', response)
                    classification = None
                    json_str = None
                    if match:
                        json_str = match.group(0)
                        self.log_message.emit(f"[DEBUG] Extracted JSON string:\n{json_str}")
                        try:
                            classification = json.loads(json_str)
                        except Exception as e:
                            self.log_message.emit(f"[DEBUG] Exception in json.loads (regex-extracted): {e}\nJSON string was:\n{json_str}")
                    else:
                        self.log_message.emit(f"[DEBUG] Regex failed to match JSON. Attempting to extract JSON code block.")
                        cleaned_response = response.strip()
                        json_block = None
                        lines = cleaned_response.splitlines()
                        start_idx = None
                        end_idx = None
                        for i, line in enumerate(lines):
                            if line.strip().startswith('```json') or line.strip() == '```':
                                start_idx = i
                                break
                        if start_idx is not None:
                            for j in range(start_idx + 1, len(lines)):
                                if lines[j].strip() == '```':
                                    end_idx = j
                                    break
                            if end_idx is not None:
                                json_block = '\n'.join(lines[start_idx + 1:end_idx]).strip()
                        if not json_block:
                            json_start = cleaned_response.find('{')
                            json_end = cleaned_response.rfind('}')
                            if json_start != -1 and json_end != -1 and json_end > json_start:
                                json_block = cleaned_response[json_start:json_end+1]
                        if json_block:
                            try:
                                classification = json.loads(json_block)
                                json_str = json_block
                                self.log_message.emit(f"[DEBUG] Successfully parsed extracted JSON block.")
                            except Exception as e:
                                self.log_message.emit(f"[DEBUG] Exception in json.loads (extracted block): {e}\nExtracted block was:\n{json_block}")
                        else:
                            self.log_message.emit(f"[DEBUG] Could not find a JSON block in the response.")
                    batch_results = []
                    if classification and isinstance(classification, dict):
                        for fname, folder in classification.items():
                            full_src_path = None
                            for f in batch_files:
                                if os.path.basename(f) == fname:
                                    full_src_path = f
                                    break
                            if not full_src_path:
                                for f in self.valid_files:
                                    if os.path.basename(f) == fname:
                                        full_src_path = f
                                        break
                            if not full_src_path:
                                full_src_path = fname
                            full_path = os.path.join(self.project_root, folder.lstrip('/'))
                            full_destination = os.path.join(full_path, fname)
                            full_destination = os.path.normpath(full_destination).replace('\\', '/')
                            self.log_message.emit(f"{full_src_path} -> {full_destination}")
                            batch_results.append((full_src_path, full_destination))
                    elif classification is not None:
                        self.log_message.emit(f"[DEBUG] JSON loaded but not a dict. Type: {type(classification)}. Value: {classification}")
                    self.batch_result.emit(batch_results)
                except Exception as e:
                    self.error.emit(f"Error in batch {batch_idx+1}: {e}")
                    continue
            self.progress_update.emit(100, "Classification complete.")
        except Exception as e:
            self.error.emit(str(e))
        self.finished.emit()

    def stop(self):
        self._is_running = False

# --- FileClassifierApp class (full implementation, adapted from FIelOrganizer.py) ---
class FileClassifierApp(QMainWindow):
    # --- UI setup (adapted from FIelOrganizer.py) ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("AI File Organizer MT")
        self.setGeometry(200, 200, 1000, 600)
        
        # Apply dark orange theme
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 32, 36))
        dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.Base, QColor(24, 26, 28))
        dark_palette.setColor(QPalette.AlternateBase, QColor(36, 38, 42))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.Button, QColor(40, 44, 52))
        dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Highlight, QColor(60, 120, 200))
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        QApplication.instance().setPalette(dark_palette)
        QApplication.instance().setStyleSheet('''
            QMainWindow {
                background-color: #23272a;
            }
            QWidget {
                background-color: #23272a;
                color: #d6d6d6;
                font-family: "Segoe UI", "Arial", sans-serif;
                font-size: 11pt;
            }
            QDockWidget {
                background: #23272a;
                border: 2px solid #ff9900;
                titlebar-close-icon: url(none);
                titlebar-normal-icon: url(none);
            }
            QDockWidget::title {
                background: #23272a;
                color: #ff9900;
                padding: 4px 10px;
                font-weight: bold;
                border-bottom: 1px solid #ff9900;
            }
            QGroupBox {
                border: 1px solid #ff9900;
                margin-top: 6px;
            }
            QGroupBox::title {
                color: #ff9900;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QLabel {
                color: #ff9900;
                font-weight: bold;
            }
            QPushButton {
                background-color: #23272a;
                color: #ff9900;
                border: 1px solid #ff9900;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff9900;
                color: #23272a;
            }
            QPushButton:pressed {
                background-color: #d17c00;
                color: #23272a;
            }
            QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
                background-color: #181a1b;
                color: #d6d6d6;
                border: 1px solid #ff9900;
                border-radius: 3px;
                selection-background-color: #ff9900;
                selection-color: #23272a;
            }
            QTableWidget, QTableView {
                background-color: #181a1b;
                color: #d6d6d6;
                gridline-color: #ff9900;
                selection-background-color: #ff9900;
                selection-color: #23272a;
                alternate-background-color: #23272a;
            }
            QHeaderView::section {
                background-color: #23272a;
                color: #ff9900;
                border: 1px solid #ff9900;
                font-weight: bold;
                padding: 4px;
            }
            QCheckBox {
                color: #ff9900;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #23272a;
                border: 1px solid #ff9900;
                width: 12px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #ff9900;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
            }
            QMenu {
                background-color: #23272a;
                color: #ff9900;
                border: 1px solid #ff9900;
            }
            QMenu::item:selected {
                background-color: #ff9900;
                color: #23272a;
            }
        ''')

        # Icons
        from PyQt5.QtWidgets import QStyle
        style = QApplication.style()
        icon_add = style.standardIcon(QStyle.SP_FileDialogNewFolder)
        icon_folder = style.standardIcon(QStyle.SP_DirOpenIcon)
        icon_clear = style.standardIcon(QStyle.SP_DialogResetButton)
        icon_classify = style.standardIcon(QStyle.SP_ArrowForward)
        icon_move = style.standardIcon(QStyle.SP_DialogYesButton)
        icon_copy = style.standardIcon(QStyle.SP_DialogOpenButton)
        icon_refine = style.standardIcon(QStyle.SP_BrowserReload)
        icon_select_all = style.standardIcon(QStyle.SP_DialogApplyButton)
        icon_select_none = style.standardIcon(QStyle.SP_DialogCancelButton)
        
        # Central widget and layouts
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        
        # File browser panel (left)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.file_browser = QTreeView()
        self.file_browser.setModel(self.file_model)
        self.file_browser.setRootIndex(self.file_model.index(""))
        self.file_browser.setColumnWidth(0, 250)
        self.file_browser.setHeaderHidden(False)
        self.file_browser.setSelectionMode(QTreeView.ExtendedSelection)
        self.file_browser.doubleClicked.connect(self.on_file_browser_double_click)
        self.file_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_browser.customContextMenuRequested.connect(self.on_file_browser_context_menu)
        
        # File browser dock
        file_browser_dock = QDockWidget("File Browser", self)
        file_browser_dock.setObjectName("FileBrowserDock")
        file_browser_dock.setWidget(self.file_browser)
        file_browser_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        file_browser_dock.setFloating(True)
        file_browser_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.LeftDockWidgetArea, file_browser_dock)
        
        # Selected files panel
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list_widget.customContextMenuRequested.connect(self.on_selected_files_context_menu)
        
        # Selected files dock
        selected_files_dock = QDockWidget("Selected Files", self)
        selected_files_dock.setObjectName("SelectedFilesDock")
        selected_files_dock.setWidget(self.file_list_widget)
        selected_files_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        selected_files_dock.setFloating(True)
        selected_files_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.LeftDockWidgetArea, selected_files_dock)
        
        # Right panel (controls)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        
        # AI Setup panel
        ai_setup_group = QGroupBox("AI Setup")
        ai_setup_layout = QVBoxLayout()
        
        # Provider selection
        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("Provider:"))
        self.provider_dropdown = QComboBox()
        self.provider_dropdown.addItems(["Ollama", "OpenRouter", "Mistral"])
        self.provider_dropdown.currentTextChanged.connect(self.on_provider_changed)
        provider_row.addWidget(self.provider_dropdown)
        ai_setup_layout.addLayout(provider_row)
        
        # Model selection
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_dropdown = QComboBox()
        model_row.addWidget(self.model_dropdown)
        ai_setup_layout.addLayout(model_row)
        
        # Ollama settings
        self.ollama_settings = QWidget()
        ollama_layout = QVBoxLayout()
        ollama_layout.addWidget(QLabel("Ollama Server URL:"))
        self.ollama_url_input = QLineEdit("http://localhost:11434")
        ollama_layout.addWidget(self.ollama_url_input)
        self.ollama_settings.setLayout(ollama_layout)
        ai_setup_layout.addWidget(self.ollama_settings)
        
        # OpenRouter settings
        self.openrouter_settings = QWidget()
        openrouter_layout = QVBoxLayout()
        openrouter_layout.addWidget(QLabel("OpenRouter API Key:"))
        self.openrouter_api_key_input = QLineEdit()
        self.openrouter_api_key_input.setEchoMode(QLineEdit.Password)
        self.openrouter_api_key_input.setPlaceholderText("Enter your OpenRouter API key")
        openrouter_layout.addWidget(self.openrouter_api_key_input)
        self.openrouter_settings.setLayout(openrouter_layout)
        self.openrouter_settings.setVisible(False)
        ai_setup_layout.addWidget(self.openrouter_settings)
        
        # Mistral settings
        self.mistral_settings = QWidget()
        mistral_layout = QVBoxLayout()
        mistral_layout.addWidget(QLabel("Mistral API Key:"))
        self.mistral_api_key_input = QLineEdit()
        self.mistral_api_key_input.setEchoMode(QLineEdit.Password)
        self.mistral_api_key_input.setPlaceholderText("Enter your Mistral API key")
        mistral_layout.addWidget(self.mistral_api_key_input)
        self.mistral_settings.setLayout(mistral_layout)
        self.mistral_settings.setVisible(False)
        ai_setup_layout.addWidget(self.mistral_settings)
        
        # Fetch models button
        self.fetch_models_btn = QPushButton("Fetch Models")
        self.fetch_models_btn.clicked.connect(self.fetch_models)
        ai_setup_layout.addWidget(self.fetch_models_btn)
        
        # Batch size control
        batch_row = QHBoxLayout()
        batch_row.addWidget(QLabel("Batch Size:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(100)
        self.batch_size_spin.setValue(15)
        self.batch_size_spin.setToolTip("Number of files to send to the AI per batch")
        batch_row.addWidget(self.batch_size_spin)
        ai_setup_layout.addLayout(batch_row)
        
        # Folder structure depth control
        depth_row = QHBoxLayout()
        depth_row.addWidget(QLabel("Folder Structure Depth:"))
        self.folder_depth_spin = QSpinBox()
        self.folder_depth_spin.setMinimum(1)
        self.folder_depth_spin.setMaximum(10)
        self.folder_depth_spin.setValue(3)
        self.folder_depth_spin.setToolTip("How many levels deep to show the folder structure to the AI")
        depth_row.addWidget(self.folder_depth_spin)
        ai_setup_layout.addLayout(depth_row)
        
        ai_setup_group.setLayout(ai_setup_layout)
        self.right_layout.addWidget(ai_setup_group)
        
        # Structure selection dropdown
        self.right_layout.addWidget(QLabel("Select Folder Structure:"))
        self.structure_dropdown = QComboBox()
        self.structure_dropdown.addItems(["KENT", "Sphere"])
        self.structure_dropdown.setEditable(False)
        self.right_layout.addWidget(self.structure_dropdown)
        
        # Destination project folder input
        self.right_layout.addWidget(QLabel("Destination Project Folder:"))
        self.project_folder_input = QLineEdit("/Files/")
        self.right_layout.addWidget(self.project_folder_input)
        
        # Buttons row
        btn_layout = QHBoxLayout()
        self.add_files_btn = QPushButton(icon_add, "Add Files")
        self.add_files_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(self.add_files_btn)
        
        self.add_folder_btn = QPushButton(icon_folder, "Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.add_folder_btn)
        
        self.clear_btn = QPushButton(icon_clear, "Clear List")
        self.clear_btn.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.clear_btn)
        
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.remove_selected_btn.clicked.connect(self.remove_selected_files)
        btn_layout.addWidget(self.remove_selected_btn)
        
        self.classify_btn = QPushButton(icon_classify, "Classify Files")
        self.classify_btn.clicked.connect(self.classify_files)
        btn_layout.addWidget(self.classify_btn)
        
        self.right_layout.addLayout(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.right_layout.addWidget(self.progress_bar)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: orange; font-size: 11pt; font-weight: bold; padding: 4px;")
        self.right_layout.addWidget(self.info_label)
        
        # Store API passwords in memory for session
        self._openrouter_password = None
        self._mistral_password = None
        
        # Path for persistent Mistral key storage
        self.mistral_key_path = os.path.join(os.path.expanduser('~'), 'FIelOrganizer_mistral_key.dat')
        
        # Connect Mistral API key input to update in-memory key and save
        self.mistral_api_key_input.textChanged.connect(self.on_mistral_api_key_changed)
        
        # Results panel
        self.results_panel = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_panel.setLayout(self.results_layout)
        
        # Results table
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Source File", "Destination Path", "Select"])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.results_table.setSortingEnabled(True)
        self.results_table.itemClicked.connect(self.on_results_table_item_clicked)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.results_table.setColumnWidth(2, 60)
        self.results_layout.addWidget(self.results_table)
        
        # Select All/None buttons
        select_btn_row = QHBoxLayout()
        self.select_all_btn = QPushButton(icon_select_all, "Select All")
        self.select_all_btn.clicked.connect(self.select_all_results)
        select_btn_row.addWidget(self.select_all_btn)
        self.select_none_btn = QPushButton(icon_select_none, "Select None")
        self.select_none_btn.clicked.connect(self.select_none_results)
        select_btn_row.addWidget(self.select_none_btn)
        self.results_layout.addLayout(select_btn_row)
        
        # Move/Copy/Refine buttons
        btn_row = QHBoxLayout()
        self.move_btn = QPushButton(icon_move, "Move Selected")
        self.move_btn.clicked.connect(self.move_selected_files)
        btn_row.addWidget(self.move_btn)
        self.copy_btn = QPushButton(icon_copy, "Copy Selected")
        self.copy_btn.clicked.connect(self.copy_selected_files)
        btn_row.addWidget(self.copy_btn)
        self.refine_btn = QPushButton(icon_refine, "Refine Selection with AI")
        self.refine_btn.clicked.connect(self.refine_selected_results)
        btn_row.addWidget(self.refine_btn)
        self.results_layout.addLayout(btn_row)
        
        # Output/log panel
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        
        # Add right panel dock (controls)
        right_panel_dock = QDockWidget("Controls", self)
        right_panel_dock.setObjectName("ControlsDock")
        right_panel_dock.setWidget(self.right_panel)
        right_panel_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        right_panel_dock.setFloating(True)
        right_panel_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, right_panel_dock)
        
        # Add results panel dock
        results_panel_dock = QDockWidget("Results", self)
        results_panel_dock.setObjectName("ResultsDock")
        results_panel_dock.setWidget(self.results_panel)
        results_panel_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        results_panel_dock.setFloating(True)
        results_panel_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.RightDockWidgetArea, results_panel_dock)
        
        # Add output/log dock
        output_dock = QDockWidget("Log / Output", self)
        output_dock.setObjectName("OutputDock")
        output_dock.setWidget(self.output_box)
        output_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        output_dock.setFloating(True)
        output_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.BottomDockWidgetArea, output_dock)
        
        # Set dock options
        self.setDockOptions(QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
        
        # Settings paths
        self.settings_path = os.path.join(os.path.expanduser('~'), 'FIelOrganizer_MT_dockstate.bin')
        self.settings_geometry_path = os.path.join(os.path.expanduser('~'), 'FIelOrganizer_MT_geometry.bin')
        
        # Fetch models on startup
        self.fetch_models()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Initialize worker
        self.worker = None
        
        # Initialize batch constant
        self.BATCH_SIZE = 15
        
        # Load settings
        self.load_settings()
        
        # Load Mistral key
        self.load_mistral_key()    # --- File classification logic (refactored for threading) ---
    def classify_files(self):
        files = self.get_all_files()
        if not files:
            QMessageBox.warning(self, "No files selected", "Please add files or folders first.")
            return
        # Validate file extensions before processing
        valid_files = []
        self.set_info("Validating selected files...")
        for f in files:
            _, ext = os.path.splitext(f)
            ext = ext.lower().strip()
            if ext in ALLOWED_EXTENSIONS_VFX or ext in ALLOWED_EXTENSIONS_COMMERCIAL:
                valid_files.append(f)
            else:
                self.output_box.append(f"Skipped invalid file: {f} (extension not allowed, detected: '{ext}')")
        if not valid_files:
            self.set_info("")
            QMessageBox.warning(self, "No valid files", "All selected files have invalid extensions.")
            return
        # Check provider connectivity and API keys
        provider = self.provider_dropdown.currentText()
        if provider == "Ollama":
            # Mirror original connectivity: only ensure URL is provided
            url = self.ollama_url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "Ollama URL Missing", "Please enter the Ollama server URL.")
                return
        elif provider == "OpenRouter":
            if not self.openrouter_api_key_input.text().strip():
                QMessageBox.warning(self, "API Key Missing", "Please enter your OpenRouter API key.")
                return
        elif provider == "Mistral":
            if not self.mistral_api_key_input.text().strip():
                QMessageBox.warning(self, "API Key Missing", "Please enter your Mistral API key.")
                return
        # --- Batching logic ---
        batch_size = self.batch_size_spin.value() if hasattr(self, 'batch_size_spin') else self.BATCH_SIZE
        project_root = self.project_folder_input.text().strip()
        if not project_root.endswith("/"):
            project_root += "/"
        folder_depth = self.folder_depth_spin.value()
        structure_choice = self.structure_dropdown.currentText()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_table.setRowCount(0)
        self._all_results_mt = []        # Start worker thread
        self.worker = FileClassifierWorker(
            valid_files, batch_size, project_root, folder_depth, structure_choice,
            self.get_llm_instance, self.get_folder_structure, PROMPT_TEMPLATE_KENT, PROMPT_TEMPLATE_SPHERE
        )
        self.worker.progress_update.connect(self._on_worker_progress)
        self.worker.batch_result.connect(self._on_worker_batch_result)
        self.worker.log_message.connect(self.output_box.append)
        self.worker.error.connect(self._on_worker_error)
        self.worker.finished.connect(self._on_worker_finished)
        self.classify_btn.setEnabled(False)
        self.worker.start()
        
    def _on_worker_progress(self, percent, message):
        """Update progress bar and status message"""
        self.progress_bar.setValue(percent)
        self.set_info(message)

    def _on_worker_batch_result(self, batch_results):
        """Update results table with batch classification results"""
        self._all_results_mt.extend(batch_results)
        # Update table incrementally
        self.results_table.setSortingEnabled(False)
        current_rows = self.results_table.rowCount()
        self.results_table.setRowCount(current_rows + len(batch_results))
        for i, (src, dst) in enumerate(batch_results):
            row = current_rows + i
            self.results_table.setItem(row, 0, QTableWidgetItem(src))
            self.results_table.setItem(row, 1, QTableWidgetItem(dst))
            checkbox = QCheckBox()
            self.results_table.setCellWidget(row, 2, checkbox)
        self.results_table.setSortingEnabled(True)
        self.results_table.resizeColumnsToContents()

    def _on_worker_error(self, msg):
        """Handle worker thread errors"""
        # If invalid address error, notify user and stop further processing
        if '10049' in msg:
            QMessageBox.critical(self, "Connection Error", "AI provider address is not valid. Please check the endpoint or API provider settings.")
            if self.worker:
                self.worker.stop()
            return
        self.output_box.append(f"<span style='color:red'>Worker error: {msg}</span>")

    def _on_worker_finished(self):
        """Clean up after worker thread completes"""
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.set_info("Classification complete.")
        self.classify_btn.setEnabled(True)

    # --- File Operations ---
    def move_selected_files(self):
        """Move selected files to their destinations"""
        selected = self.get_selected_results()
        if not selected:
            QMessageBox.warning(self, "No files selected", "Please select files to move.")
            return
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Build list of all files to move (expanding sequences)
        all_files_to_move = []
        for src, dst in selected:
            src_files = self.expand_sequence_files(src)
            if src_files:
                dst_dir = os.path.dirname(dst)
                for src_file in src_files:
                    if src_file and os.path.exists(src_file):
                        # For sequences, preserve the original filename in destination
                        dst_file = os.path.join(dst_dir, os.path.basename(src_file))
                        all_files_to_move.append((src_file, dst_file))
            else:
                self.output_box.append(f"Warning: Could not find source file: {src}")
        
        if not all_files_to_move:
            QMessageBox.warning(self, "No files to move", "No valid source files found.")
            self.progress_bar.setVisible(False)
            return
        
        # Perform move operations with progress
        total_files = len(all_files_to_move)
        moved_count = 0
        failed_count = 0
        
        for i, (src_file, dst_file) in enumerate(all_files_to_move):
            try:
                # Update progress
                progress = int((i / total_files) * 100)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()  # Keep UI responsive
                
                # Create destination directory
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                
                # Move file
                shutil.move(src_file, dst_file)
                moved_count += 1
                
                self.output_box.append(f"Moved: {os.path.basename(src_file)} -> {dst_file}")
                
            except Exception as e:
                failed_count += 1
                self.output_box.append(f"Error moving {os.path.basename(src_file)}: {e}")
        
        # Complete progress and hide bar
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        # Show completion message
        message = f"Move operation completed!\nMoved: {moved_count} files"
        if failed_count > 0:
            message += f"\nFailed: {failed_count} files"
        QMessageBox.information(self, "Move Complete", message)
        
    def copy_selected_files(self):
        """Copy selected files to their destinations"""
        import shutil
        selected = self.get_selected_results()
        if not selected:
            QMessageBox.warning(self, "No files selected", "Please select files to copy.")
            return
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Build list of all files to copy (expanding sequences)
        all_files_to_copy = []
        for src, dst in selected:
            src_files = self.expand_sequence_files(src)
            if src_files:
                dst_dir = os.path.dirname(dst)
                for src_file in src_files:
                    if src_file and os.path.exists(src_file):
                        # For sequences, preserve the original filename in destination
                        dst_file = os.path.join(dst_dir, os.path.basename(src_file))
                        all_files_to_copy.append((src_file, dst_file))
            else:
                self.output_box.append(f"Warning: Could not find source file: {src}")
        
        if not all_files_to_copy:
            QMessageBox.warning(self, "No files to copy", "No valid source files found.")
            self.progress_bar.setVisible(False)
            return
        
        # Perform copy operations with progress
        total_files = len(all_files_to_copy)
        copied_count = 0
        failed_count = 0
        
        for i, (src_file, dst_file) in enumerate(all_files_to_copy):
            try:
                # Update progress
                progress = int((i / total_files) + 0.5 * 100) # Slightly faster completion
                self.progress_bar.setValue(progress)
                QApplication.processEvents()  # Keep UI responsive
                
                # Create destination directory
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                
                # Copy file
                shutil.copy2(src_file, dst_file)
                copied_count += 1
                
                self.output_box.append(f"Copied: {os.path.basename(src_file)} -> {dst_file}")
                
            except Exception as e:
                failed_count += 1
                self.output_box.append(f"Error copying {os.path.basename(src_file)}: {e}")
        
        # Complete progress and hide bar
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        # Show completion message
        message = f"Copy operation completed!\nCopied: {copied_count} files"
        if failed_count > 0:
            message += f"\nFailed: {failed_count} files"
        QMessageBox.information(self, "Copy Complete", message)
    
    def find_full_path(self, fname):
        """Find the full path of a file, handling both individual files and sequences"""
        # Handle absolute paths directly
        if os.path.isabs(fname) and os.path.exists(fname):
            return fname
        
        # First, try exact match for individual files
        for i in range(self.file_list_widget.count()):
            item_text = self.file_list_widget.item(i).text()
            if os.path.basename(item_text) == fname:
                return item_text
        
        # If no exact match, try to handle sequences (files with #### pattern)
        if '####' in fname:
            # This is a sequence pattern, find the directory and actual files
            sequence_base = fname.replace('####', '*')
            for i in range(self.file_list_widget.count()):
                item_text = self.file_list_widget.item(i).text()
                item_dir = os.path.dirname(item_text)
                # Look for files matching the sequence pattern in the same directory
                pattern = os.path.join(item_dir, sequence_base)
                matching_files = glob.glob(pattern)
                if matching_files:
                    return matching_files  # Return list of files for sequences
        
        # If not found, try current working directory
        if os.path.exists(fname):
            return os.path.abspath(fname)
        return None
        
    def expand_sequence_files(self, fname):
        """Expand a sequence pattern (####) to actual file list"""
        # Handle direct file paths
        if os.path.isabs(fname) and os.path.exists(fname):
            return [fname]
        if '####' not in fname:
            # Single file
            full_path = self.find_full_path(fname)
            return [full_path] if full_path and isinstance(full_path, str) else []
        
        # Sequence file - find all matching files
        full_path = self.find_full_path(fname)
        if isinstance(full_path, list):
            return full_path
        elif full_path:
            return [full_path]
        return []
    
    # --- Results Handling ---
    def select_all_results(self):
        """Select all items in results table"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 2)
            if checkbox:
                checkbox.setChecked(True)

    def select_none_results(self):
        """Deselect all items in results table"""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 2)
            if checkbox:
                checkbox.setChecked(False)
                
    def on_results_table_item_clicked(self, item):
        """Handle clicks on results table rows to toggle checkboxes"""
        if item is None:
            return
            
        # Get the row of the clicked item
        row = item.row()
        
        # Don't toggle if they clicked directly on the checkbox column
        if item.column() == 2:
            return
            
        # Get the checkbox widget from column 2
        checkbox = self.results_table.cellWidget(row, 2)
        if checkbox:
            # Toggle the checkbox state
            checkbox.setChecked(not checkbox.isChecked())
            
    def refine_selected_results(self):
        """Refine selected results using AI feedback"""
        selected = self.get_selected_results()
        if not selected:
            QMessageBox.warning(self, "No files selected", "Please select files to refine.")
            return
        # Ask user for feedback
        feedback, ok = QInputDialog.getMultiLineText(self, "Refine Results", "Enter your feedback or corrections for the selected files:\n(Example: 'Move shot01.exr to /new/path', 'shot02.mov should be in /assets', etc.)")
        if not ok or not feedback.strip():
            return
            
        # Format selected files for prompt
        project_root = self.project_folder_input.text().strip()
        file_lines = [f"{src} -> {os.path.relpath(dst, project_root)}" for src, dst in selected]
        files_str = "\n".join(file_lines)
        
        # Get current project structure
        if os.path.isdir(project_root):
            project_structure = self.get_folder_structure(project_root, max_depth=6)
        else:
            project_structure = "(Project folder does not exist or is not accessible)"
        
        # Compose prompt
        with open(os.path.join(os.path.dirname(__file__), 'prompt_refine.md'), 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        prompt = prompt_template.replace('{selected_files}', files_str).replace('{user_feedback}', feedback).replace('{project_structure}', project_structure)
        
        try:
            # Get LLM instance based on selected provider
            llm = self.get_llm_instance()
            response = llm.invoke(prompt)
            self.output_box.append("<b>Refined Results:</b>")
            self.output_box.append(response)
            # Try to extract JSON and update results table
            import re, json
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                json_str = match.group(0)
                try:
                    new_mapping = json.loads(json_str)
                    project_root = self.project_folder_input.text().strip()
                    if not project_root.endswith("/"):
                        project_root += "/"
                    # Build a mapping from basename to (key, value) pairs
                    mapping_by_basename = {}
                    for k, v in new_mapping.items():
                        base = os.path.basename(k)
                        mapping_by_basename.setdefault(base, []).append((k, v))
                    for row in range(self.results_table.rowCount()):
                        src = self.results_table.item(row, 0).text()
                        src_base = os.path.basename(src)
                        if src_base in mapping_by_basename:
                            # Use the first mapping for this basename
                            _, rel_dst = mapping_by_basename[src_base][0]
                            rel_dst = rel_dst.lstrip('/\\')
                            # Ensure the filename is present in the destination path
                            if not rel_dst.replace('\\', '/').endswith(src_base):
                                rel_dst = rel_dst.rstrip('/\\') + '/' + src_base
                            rel_dst = rel_dst.replace('\\', '/')
                            new_dst = os.path.join(project_root, rel_dst).replace('\\', '/')
                            self.results_table.setItem(row, 1, QTableWidgetItem(new_dst))
                    self.results_table.resizeColumnsToContents()
                    self.output_box.append("<span style='color:green'>Results table updated with new destinations.</span>")
                except Exception as e:
                    self.output_box.append(f"<span style='color:red'>Error parsing model response as JSON: {e}</span>")
            else:
                self.output_box.append("<span style='color:orange'>No JSON mapping found in model response. No changes made to results table.</span>")
        except Exception as e:
            self.output_box.append(f"Error refining results: {e}")
            
    def remove_selected_files(self):
        """Remove selected files from the file_list_widget."""
        selected_items = self.file_list_widget.selectedItems()
        for item in selected_items:
            self.file_list_widget.takeItem(self.file_list_widget.row(item))

    def set_info(self, msg):
        """Set the info label text."""
        self.info_label.setText(msg)
        
    def closeEvent(self, event):
        # Save window and dock state
        with open(self.settings_path, 'wb') as f:
            f.write(self.saveState())
        with open(self.settings_geometry_path, 'wb') as f:
            f.write(self.saveGeometry())
        event.accept()
        
    def load_settings(self):
        """Load window and dock state"""
        try:
            if os.path.exists(self.settings_path) and os.path.exists(self.settings_geometry_path):
                with open(self.settings_path, 'rb') as f:
                    state = f.read()
                    self.restoreState(state)
                with open(self.settings_geometry_path, 'rb') as f:
                    geometry = f.read()
                    self.restoreGeometry(geometry)
        except Exception as e:
            self.output_box.append(f"Error loading settings: {e}")
            
    def update_ui(self):
        """Update UI state and refresh model list"""
        # Update provider-specific settings visibility
        self.on_provider_changed()
        
    def on_provider_changed(self):
        """Handle provider selection change"""
        provider = self.provider_dropdown.currentText()
        if provider == "Ollama":
            self.ollama_settings.setVisible(True)
            self.openrouter_settings.setVisible(False)
            self.mistral_settings.setVisible(False)
        elif provider == "OpenRouter":
            self.ollama_settings.setVisible(False)
            self.openrouter_settings.setVisible(True)
            self.mistral_settings.setVisible(False)
        elif provider == "Mistral":
            self.ollama_settings.setVisible(False)
            self.openrouter_settings.setVisible(False)
            self.mistral_settings.setVisible(True)
            if getattr(self, '_mistral_password', None) is not None:
                self.mistral_api_key_input.setText(self._mistral_password)
        # Clear model dropdown when provider changes
        self.model_dropdown.clear()
        
    def fetch_models(self):
        """Fetch available models for the selected provider"""
        provider = self.provider_dropdown.currentText()
        if provider == "Ollama":
            try:
                proc = subprocess.run(
                    ['ollama', 'list'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if proc.returncode != 0:
                    raise RuntimeError(proc.stderr.strip())
                lines = proc.stdout.strip().splitlines()
                models = [line.split()[0] for line in lines if line and not line.startswith("NAME")]
                if not models:
                    models = ["No models found"]
                self.model_dropdown.clear()
                self.model_dropdown.addItems(models)
                self.model_dropdown.setEditable(False)
            except Exception as e:
                self.model_dropdown.clear()
                self.model_dropdown.addItem("Error fetching models")
                self.output_box.append(f"Failed to fetch Ollama models: {e}")
        elif provider == "OpenRouter":
            self.model_dropdown.clear()
            self.model_dropdown.addItems(OPENROUTER_MODELS)
            self.model_dropdown.setEditable(False)
        elif provider == "Mistral":
            self.model_dropdown.clear()
            self.model_dropdown.addItems(MISTRAL_MODELS)
            self.model_dropdown.setEditable(False)
    
    def on_file_browser_double_click(self, index):
        path = self.file_model.filePath(index)
        if os.path.isfile(path):
            if path not in self.get_all_files():
                self.file_list_widget.addItem(path)
        elif os.path.isdir(path):
            self._add_folder_recursive(path)
            
    def on_file_browser_context_menu(self, pos):
        indexes = self.file_browser.selectedIndexes()
        if not indexes:
            return
        # Only consider the first column for file/folder selection
        paths = set()
        for idx in indexes:
            if idx.column() == 0:
                paths.add(self.file_model.filePath(idx))
        menu = QMenu(self.file_browser)
        send_action = QAction("Send to AI", self)
        send_action.triggered.connect(lambda: self.send_selected_to_ai(list(paths)))
        menu.addAction(send_action)
        # Add Send to Destination Folder if only one folder is selected
        folder_paths = [p for p in paths if os.path.isdir(p)]
        if len(folder_paths) == 1:
            send_dest_action = QAction("Send to Destination Folder", self)
            send_dest_action.triggered.connect(lambda: self.set_destination_folder(folder_paths[0]))
            menu.addAction(send_dest_action)
        menu.exec_(self.file_browser.viewport().mapToGlobal(pos))
        
    def on_selected_files_context_menu(self, pos):
        menu = QMenu(self.file_list_widget)
        remove_action = QAction("Remove Selected", self)
        remove_action.triggered.connect(self.remove_selected_files)
        menu.addAction(remove_action)
        menu.exec_(self.file_list_widget.viewport().mapToGlobal(pos))

    def add_files(self):
        """Open file dialog and add selected files to list"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        for f in files:
            if f not in self.get_all_files():
                self.file_list_widget.addItem(f)

    def add_folder(self):
        """Open folder dialog and recursively add files"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._add_folder_recursive(folder)

    def _add_folder_recursive(self, root):
        """Recursively add files from a folder with sequence grouping"""
        import re
        from collections import defaultdict, deque
        seq_dict = defaultdict(list)
        visited = set()
        # First pass: count total directories for progress
        temp_queue = deque([root])
        total_dirs = 0
        while temp_queue:
            current = temp_queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            try:
                entries = [os.path.join(current, f) for f in os.listdir(current)]
            except Exception:
                continue
            for entry in entries:
                if os.path.isdir(entry):
                    temp_queue.append(entry)
            total_dirs += 1
        # Reset and scan
        visited.clear()
        queue = deque([root])
        processed = 0
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.set_info("Scanning folder(s)...")
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            try:
                entries = [os.path.join(current, f) for f in os.listdir(current)]
            except Exception:
                continue
            for entry in entries:
                if os.path.isdir(entry):
                    queue.append(entry)
                elif os.path.isfile(entry):
                    fname = os.path.basename(entry)
                    match = re.match(r"(.+?)([._-])?(\d{3,4})(\.[^.]+)$", fname)
                    if match:
                        prefix, sep, frame, ext = match.groups()
                        key = f"{prefix}{sep if sep else ''}####{ext}"
                        seq_dict[key].append(fname)
                    else:
                        seq_dict[fname].append(fname)
            processed += 1
            if total_dirs > 0:
                pct = int((processed/total_dirs)*100)
                self.progress_bar.setValue(pct)
                QApplication.processEvents()
                self.set_info(f"Scanning: {current}")
        # Add representative entries
        for key, files in seq_dict.items():
            if len(files) > 1 and '####' in key:
                rep = key
            else:
                rep = files[0]
            if rep not in self.get_all_files():
                self.file_list_widget.addItem(rep)
        self.progress_bar.setVisible(False)
        self.set_info("Folder scan complete.")
        
    def get_all_files(self):
        """Return list of currently selected files"""
        return [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())]

    def get_folder_structure(self, path, max_depth=3, prefix=""):
        """Build a simple folder structure string up to max_depth"""
        structure = []
        def walk(p, depth):
            if depth > max_depth:
                return
            try:
                entries = sorted(os.listdir(p))
            except Exception:
                return
            for e in entries:
                full = os.path.join(p, e)
                structure.append(f"{prefix * depth}{e}")
                if os.path.isdir(full):
                    walk(full, depth+1)
        walk(path, 0)
        return "\n".join(structure)

    def get_llm_instance(self):
        """Return LLM instance based on selected provider"""
        provider = self.provider_dropdown.currentText()
        model = self.model_dropdown.currentText()
        if provider == "Ollama":
            url = self.ollama_url_input.text().strip()
            if not url:
                raise ValueError("Please enter a valid Ollama server URL")
            return OllamaLLM(model=model, base_url=url)
        elif provider == "OpenRouter":
            api_key = self.openrouter_api_key_input.text().strip()
            return OpenRouterLLM(model, api_key)
        elif provider == "Mistral":
            api_key = self.mistral_api_key_input.text().strip()
            return MistralLLM(model, api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def on_mistral_api_key_changed(self, text):
        self._mistral_password = text
        self.save_mistral_key()

    def save_mistral_key(self):
        """Save Mistral API key to file"""
        try:
            with open(self.mistral_key_path, 'w') as f:
                f.write(self._mistral_password or '')
        except Exception:
            pass

    def load_mistral_key(self):
        """Load Mistral API key from file"""
        try:
            if os.path.exists(self.mistral_key_path):
                with open(self.mistral_key_path, 'r') as f:
                    self._mistral_password = f.read().strip()
        except Exception:
            self._mistral_password = None

    def send_selected_to_ai(self, paths):
        """Add a list of paths to the selected files list"""
        for path in paths:
            if os.path.isdir(path):
                # Recursively add all files from a folder
                self._add_folder_recursive(path)
            elif os.path.isfile(path):
                # Add individual files
                if path not in self.get_all_files():
                    self.file_list_widget.addItem(path)

    def set_destination_folder(self, folder):
        """Set the destination project folder"""
        self.project_folder_input.setText(folder)
        
    def clear_list(self):
        """Clear all items from the selected files list"""
        self.file_list_widget.clear()

    def get_selected_results(self):
        """Return list of (src, dst) for checked rows in results table"""
        results = []
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 2)
            if checkbox and checkbox.isChecked():
                src = self.results_table.item(row, 0).text()
                dst = self.results_table.item(row, 1).text()
                results.append((src, dst))
        return results
