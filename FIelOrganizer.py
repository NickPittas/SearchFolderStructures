import sys
import os
import json
import re
import subprocess
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QListWidget, QLabel, QTextEdit, QMessageBox, QHBoxLayout, QComboBox, QLineEdit,
    QSplitter, QTreeView, QFileSystemModel, QMenu, QAction, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QCheckBox, QDialog, QProgressBar,
    QMainWindow, QDockWidget, QInputDialog, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPalette, QColor
from langchain.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM

# Import secure storage
try:
    from secure_storage import SecureStorage
    SECURE_STORAGE_AVAILABLE = True
except ImportError:
    SECURE_STORAGE_AVAILABLE = False
    print("Warning: cryptography package not available. API keys will not be encrypted.")

# Allowed file extensions based on the prompt template
ALLOWED_EXTENSIONS_VFX = {'.exr', '.dpx', '.tif', '.png', '.mov', '.mxf', '.avi', '.psd', '.ai', '.jpg', '.mp4', '.docx', '.pdf', '.xlsx', '.pptx', '.wav', '.mp3', '.aiff', '.nk', '.aep', '.prproj', '.drp', '.xml', '.edl', '.json', '.txt', '.aaf'}
ALLOWED_EXTENSIONS_COMMERCIAL = {'.exr', '.dpx', '.tif', '.png', '.mov', '.mxf', '.avi', '.psd', '.ai', '.jpg', '.mp4', '.docx', '.pdf', '.xlsx', '.pptx', '.wav', '.mp3', '.aiff', '.nk', '.aep', '.prproj', '.drp', '.xml', '.edl', '.json', '.txt', '.aaf'} 

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

class OpenRouterLLM:
    """Simple OpenRouter API wrapper for compatibility with Ollama interface"""
    
    def __init__(self, model, api_key):
        self.model = model
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def invoke(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Optional
            "X-Title": "AI File Organizer"  # Optional
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenRouter API Error: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected response format from OpenRouter: {e}")

# Load prompt templates from Markdown files

def load_prompt_from_md(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Remove markdown header lines (lines starting with # and blank lines)
    prompt_lines = [line for line in lines if not line.strip().startswith('#') or line.strip() == '#']
    return ''.join(prompt_lines)

PROMPT_TEMPLATE_KENT = load_prompt_from_md(os.path.join(os.path.dirname(__file__), 'prompt_kent.md'))
PROMPT_TEMPLATE_SPHERE = load_prompt_from_md(os.path.join(os.path.dirname(__file__), 'prompt_sphere.md'))

# Refactor FileClassifierApp to inherit QMainWindow for dockable panels
class FileClassifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(200, 200, 1000, 600)
        self.setWindowTitle("AI File Organizer")

        # --- Apply dark theme and custom styles ---
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
        # Global style sheet for rounded buttons, panels, and dark look
        QApplication.instance().setStyleSheet('''
            QMainWindow, QDockWidget, QWidget, QTreeView, QTableWidget, QTextEdit, QListWidget, QLineEdit, QComboBox {
                background-color: #23262e;
                color: #e0e0e0;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 11.5pt;
            }
            QPushButton {
                background-color: #3a3f4b;
                color: #e0e0e0;
                border-radius: 12px;
                padding: 6px 16px;
                border: 1px solid #444;
            }
            QPushButton:hover {
                background-color: #50556a;
            }
            QPushButton:pressed {
                background-color: #2d2f3a;
            }
            QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget {
                border-radius: 8px;
                border: 1px solid #444;
                background-color: #23262e;
                color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #2d2f3a;
                color: #e0e0e0;
                border-radius: 8px;
                padding: 4px;
            }
            QDockWidget {
                border-radius: 16px;
                border: 2px solid #444;
            }
            QProgressBar {
                border-radius: 8px;
                background: #23262e;
                color: #e0e0e0;
                border: 1px solid #444;
            }
            QProgressBar::chunk {
                background-color: #3a7bd5;
                border-radius: 8px;
            }
        ''')

        # --- Icons ---
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
        icon_chat = style.standardIcon(QStyle.SP_MessageBoxInformation)

        # File browser dock
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
        # --- Dock widget setup ---
        file_browser_dock = QDockWidget("File Browser", self)
        file_browser_dock.setObjectName("FileBrowserDock")
        file_browser_dock.setWidget(self.file_browser)
        file_browser_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        file_browser_dock.setFloating(True)
        file_browser_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        file_browser_dock.setStyleSheet("QDockWidget { background: #232e2b; border: 2px solid #3a7bd5; }")
        file_browser_dock.setWindowIcon(icon_folder)
        self.addDockWidget(Qt.LeftDockWidgetArea, file_browser_dock)

        # --- Selected Files panel (dockable) ---
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # (Remove the earlier selected_files_dock block to avoid duplicate panel)
        # selected_files_dock = QDockWidget("Selected Files", self)
        # selected_files_dock.setObjectName("SelectedFilesDock")
        # selected_files_dock.setWidget(self.file_list_widget)
        # selected_files_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        # selected_files_dock.setFloating(True)
        # selected_files_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        # selected_files_dock.setStyleSheet("QDockWidget { background: #2e233a; border: 2px solid #d53a7b; }")
        # selected_files_dock.setWindowIcon(icon_add)
        # self.addDockWidget(Qt.LeftDockWidgetArea, selected_files_dock)

        # Right panel dock (controls)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_panel.setLayout(self.right_layout)        # --- AI Provider Setup group ---
        ai_setup_group = QGroupBox("AI Provider Setup")
        ai_setup_layout = QVBoxLayout()
        
        # Provider selection
        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("Provider:"))
        self.provider_dropdown = QComboBox()
        self.provider_dropdown.addItems(["Ollama", "OpenRouter"])
        self.provider_dropdown.currentTextChanged.connect(self.on_provider_changed)
        provider_row.addWidget(self.provider_dropdown)
        ai_setup_layout.addLayout(provider_row)
        
        # Model selection
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_dropdown = QComboBox()
        model_row.addWidget(self.model_dropdown)
        ai_setup_layout.addLayout(model_row)
        
        # Ollama specific settings
        self.ollama_settings = QWidget()
        ollama_layout = QVBoxLayout()
        ollama_layout.addWidget(QLabel("Ollama Server URL:"))
        self.ollama_url_input = QLineEdit("http://localhost:11434")
        ollama_layout.addWidget(self.ollama_url_input)
        self.ollama_settings.setLayout(ollama_layout)
        ai_setup_layout.addWidget(self.ollama_settings)
          # OpenRouter specific settings
        self.openrouter_settings = QWidget()
        openrouter_layout = QVBoxLayout()
        openrouter_layout.addWidget(QLabel("OpenRouter API Key:"))
        
        # API Key input row with load/save buttons
        api_key_row = QHBoxLayout()
        self.openrouter_api_key_input = QLineEdit()
        self.openrouter_api_key_input.setEchoMode(QLineEdit.Password)
        self.openrouter_api_key_input.setPlaceholderText("Enter your OpenRouter API key")
        api_key_row.addWidget(self.openrouter_api_key_input)
        
        if SECURE_STORAGE_AVAILABLE:
            # Load key button
            self.load_key_btn = QPushButton("Load")
            self.load_key_btn.setMaximumWidth(60)
            self.load_key_btn.clicked.connect(self.load_openrouter_key)
            api_key_row.addWidget(self.load_key_btn)
            
            # Save key button
            self.save_key_btn = QPushButton("Save")
            self.save_key_btn.setMaximumWidth(60)
            self.save_key_btn.clicked.connect(self.save_openrouter_key)
            api_key_row.addWidget(self.save_key_btn)
        
        openrouter_layout.addLayout(api_key_row)
        
        if not SECURE_STORAGE_AVAILABLE:
            warning_label = QLabel("⚠️ Install 'cryptography' package for encrypted key storage")
            warning_label.setStyleSheet("color: orange; font-size: 9pt;")
            openrouter_layout.addWidget(warning_label)
        
        self.openrouter_settings.setLayout(openrouter_layout)
        self.openrouter_settings.setVisible(False)  # Initially hidden
        ai_setup_layout.addWidget(self.openrouter_settings)
        
        # Fetch models button
        self.fetch_models_btn = QPushButton("Fetch Models")
        self.fetch_models_btn.clicked.connect(self.fetch_models)
        ai_setup_layout.addWidget(self.fetch_models_btn)
        
        ai_setup_group.setLayout(ai_setup_layout)
        self.right_layout.addWidget(ai_setup_group)

        # --- Chat window ---
        chat_panel = QWidget()
        chat_layout = QVBoxLayout()
        chat_panel.setLayout(chat_layout)
        chat_layout.addWidget(QLabel("Chat with Model:"))
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        chat_layout.addWidget(self.chat_history)
        chat_input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        # Dropdown for mode selection
        self.chat_mode_dropdown = QComboBox()
        self.chat_mode_dropdown.addItems(["Chat", "Refine"])
        self.chat_mode_dropdown.setFixedWidth(70)
        chat_input_row.addWidget(self.chat_mode_dropdown)
        chat_input_row.addWidget(self.chat_input)
        # Arrow send button
        self.send_chat_btn = QPushButton()
        self.send_chat_btn.setText("→")
        self.send_chat_btn.setFixedWidth(32)
        self.send_chat_btn.clicked.connect(self.send_chat_message)
        chat_input_row.addWidget(self.send_chat_btn)
        chat_layout.addLayout(chat_input_row)
        self.right_layout.addWidget(chat_panel)

        # Structure selection dropdown
        self.right_layout.addWidget(QLabel("Select Folder Structure:"))
        self.structure_dropdown = QComboBox()
        self.structure_dropdown.addItems(["KENT", "Sphere"])
        self.structure_dropdown.setEditable(False)
        self.right_layout.addWidget(self.structure_dropdown)

        # Destination project folder input
        self.right_layout.addWidget(QLabel("Destination Project Folder (used as root for AI classification):"))
        self.project_folder_input = QLineEdit("/Files/")
        self.right_layout.addWidget(self.project_folder_input)        # Buttons row
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

        self.classify_btn = QPushButton(icon_classify, "Classify Files")
        self.classify_btn.clicked.connect(self.classify_files)
        btn_layout.addWidget(self.classify_btn)

        self.right_layout.addLayout(btn_layout)
        # Progress bar for folder scanning/import
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.right_layout.addWidget(self.progress_bar)

        # Add results panel for source/destination mapping and actions
        self.results_panel = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_panel.setLayout(self.results_layout)
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Source File", "Destination Path", "Select"])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.MultiSelection)
        # Set column resize modes: Source and Destination user-resizable, Select fixed
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # User can resize Source File
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # User can resize Destination Path
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.results_table.setColumnWidth(2, 60)
        self.results_layout.addWidget(self.results_table)
        # Select All / None buttons
        select_btn_row = QHBoxLayout()
        self.select_all_btn = QPushButton(icon_select_all, "Select All")
        self.select_all_btn.clicked.connect(self.select_all_results)
        select_btn_row.addWidget(self.select_all_btn)
        self.select_none_btn = QPushButton(icon_select_none, "Select None")
        self.select_none_btn.clicked.connect(self.select_none_results)
        select_btn_row.addWidget(self.select_none_btn)
        self.results_layout.addLayout(select_btn_row)
        # Move/Copy buttons
        btn_row = QHBoxLayout()
        self.move_btn = QPushButton(icon_move, "Move Selected")
        self.move_btn.clicked.connect(self.move_selected_files)
        btn_row.addWidget(self.move_btn)
        self.copy_btn = QPushButton(icon_copy, "Copy Selected")
        self.copy_btn.clicked.connect(self.copy_selected_files)
        btn_row.addWidget(self.copy_btn)
        # Add Refine Results button
        self.refine_btn = QPushButton(icon_refine, "Refine Selection with AI")
        self.refine_btn.clicked.connect(self.refine_selected_results)
        btn_row.addWidget(self.refine_btn)
        self.results_layout.addLayout(btn_row)
        # Remove width restrictions on results panel
        # self.results_panel.setMinimumWidth(400)
        # self.results_panel.setMaximumWidth(700)
        # Remove old right_layout.addWidget() calls for file_list_widget and output_box
        # (They are now only in their own dock panels)
        #self.right_layout.addWidget(self.file_list_widget)
        #self.right_layout.addWidget(self.output_box)

        # Use a QMainWindow and QDockWidget for full panel flexibility
        # (This requires refactoring: move FileClassifierApp to inherit QMainWindow)
        # Optionally allow docks to be tabbed or floated
        self.setDockOptions(QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)

        # Fetch models on startup
        self.fetch_models()

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Make all panels moveable in the splitter
        #self.splitter.setChildrenCollapsible(False)
        #self.splitter.setHandleWidth(8)
        # (Panels are already in QSplitter, so user can move them)

        # Add right panel dock (controls)
        right_panel_dock = QDockWidget("Controls", self)
        right_panel_dock.setObjectName("ControlsDock")
        right_panel_dock.setWidget(self.right_panel)
        right_panel_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        right_panel_dock.setFloating(True)
        right_panel_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        # Optionally add style and icon here if desired
        self.addDockWidget(Qt.RightDockWidgetArea, right_panel_dock)
        right_panel_dock.show()

        # Add results panel dock
        results_panel_dock = QDockWidget("Results", self)
        results_panel_dock.setObjectName("ResultsDock")
        results_panel_dock.setWidget(self.results_panel)
        results_panel_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        results_panel_dock.setFloating(True)
        results_panel_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        results_panel_dock.setStyleSheet("QDockWidget { background: #233a23; border: 2px solid #7bd53a; }")
        results_panel_dock.setWindowIcon(icon_move)
        self.addDockWidget(Qt.RightDockWidgetArea, results_panel_dock)

        # Add file list panel dock (Selected Files)
        file_list_dock = QDockWidget("Selected Files", self)
        file_list_dock.setObjectName("SelectedFilesDock")
        file_list_dock.setWidget(self.file_list_widget)
        file_list_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        file_list_dock.setFloating(True)
        file_list_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        file_list_dock.setStyleSheet("QDockWidget { background: #232e2b; border: 2px solid #d5a73a; }")
        file_list_dock.setWindowIcon(icon_add)
        self.addDockWidget(Qt.LeftDockWidgetArea, file_list_dock)

        # --- Output/log panel ---
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        output_dock = QDockWidget("Log / Output", self)
        output_dock.setObjectName("OutputDock")
        output_dock.setWidget(self.output_box)
        output_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        output_dock.setFloating(True)
        output_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        output_dock.setStyleSheet("QDockWidget { background: #232e2b; border: 2px solid #3a7bd5; }")
        output_dock.setWindowIcon(icon_chat)
        self.addDockWidget(Qt.BottomDockWidgetArea, output_dock)

        # --- Restore/Save window and dock state ---
        self.settings_path = os.path.join(os.path.expanduser('~'), 'FIelOrganizer_winstate.dat')
        self.settings_geometry_path = os.path.join(os.path.expanduser('~'), 'FIelOrganizer_geometry.dat')
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'rb') as f:
                state = f.read()
                self.restoreState(state)
        if os.path.exists(self.settings_geometry_path):
            with open(self.settings_geometry_path, 'rb') as f:
                geometry = f.read()
                self.restoreGeometry(geometry)

    def on_provider_changed(self):
        """Handle provider selection change"""
        provider = self.provider_dropdown.currentText()
        if provider == "Ollama":
            self.ollama_settings.setVisible(True)
            self.openrouter_settings.setVisible(False)
        elif provider == "OpenRouter":
            self.ollama_settings.setVisible(False)
            self.openrouter_settings.setVisible(True)
          # Clear model dropdown when provider changes
        self.model_dropdown.clear()

    def fetch_models(self):
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

                # Set gemma3:12b as default if present
                default_model = None
                for i, m in enumerate(models):
                    if m.lower().replace(' ', '') == 'deepseek-coder-v2:latest':
                        default_model = i
                        break
                        
                self.model_dropdown.clear()
                self.model_dropdown.addItems(models)
                self.model_dropdown.setEditable(False)
                if default_model is not None:
                    self.model_dropdown.setCurrentIndex(default_model)

            except Exception as e:
                self.model_dropdown.clear()
                self.model_dropdown.addItem("Error fetching models")
                self.output_box.append(f"Failed to fetch Ollama models: {e}")
                
        elif provider == "OpenRouter":
            try:
                # For OpenRouter, we use the predefined model list
                self.model_dropdown.clear()
                self.model_dropdown.addItems(OPENROUTER_MODELS)
                self.model_dropdown.setEditable(False)
                # Set Claude 3.5 Sonnet as default
                default_index = 0  # First item (Claude 3.5 Sonnet)
                self.model_dropdown.setCurrentIndex(default_index)
                self.output_box.append("OpenRouter models loaded successfully.")
                
            except Exception as e:
                self.model_dropdown.clear()
                self.model_dropdown.addItem("Error loading OpenRouter models")
                self.output_box.append(f"Failed to load OpenRouter models: {e}")

    def get_llm_instance(self):
        """Get the appropriate LLM instance based on selected provider"""
        provider = self.provider_dropdown.currentText()
        model_name = self.model_dropdown.currentText()
        
        if not model_name or model_name.startswith("Error") or model_name == "No models found":
            raise ValueError("No valid model selected")
            
        if provider == "Ollama":
            ollama_url = self.ollama_url_input.text().strip()
            if not ollama_url:
                raise ValueError("Please enter a valid Ollama server URL")
            return OllamaLLM(model=model_name, base_url=ollama_url)
            
        elif provider == "OpenRouter":
            api_key = self.openrouter_api_key_input.text().strip()
            if not api_key:
                raise ValueError("Please enter your OpenRouter API key")
            return OpenRouterLLM(model=model_name, api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        for f in files:
            if f not in self.get_all_files():
                self.file_list_widget.addItem(f)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._add_folder_recursive(folder)

    def _add_folder_recursive(self, folder):
        import re
        from collections import defaultdict, deque
        seq_dict = defaultdict(list)
        visited = set()
        queue = deque([folder])
        total_dirs = 0
        # First pass: count total dirs for progress
        temp_queue = deque([folder])
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
        # Reset for actual scan
        visited.clear()
        queue = deque([folder])
        processed_dirs = 0
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
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
            processed_dirs += 1
            if total_dirs > 0:
                progress = int((processed_dirs / total_dirs) * 100)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()
        # Add only one representative per sequence, and all non-sequence files
        for key, files in seq_dict.items():
            if len(files) > 1 and '####' in key:
                rep = key
            else:
                rep = files[0]
            if rep not in self.get_all_files():
                self.file_list_widget.addItem(rep)
        self.progress_bar.setVisible(False)

    def clear_list(self):
        self.file_list_widget.clear()
        self.output_box.clear()

    def get_all_files(self):
        return [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())]

    def get_folder_structure(self, root_path, max_depth=3, prefix=""):
        """Recursively build a tree-like string of the folder structure up to max_depth."""
        lines = []
        def _walk(path, depth, prefix):
            if depth > max_depth:
                return
            try:
                entries = sorted(os.listdir(path))
            except Exception:
                return
            for i, entry in enumerate(entries):
                full_path = os.path.join(path, entry)
                is_last = (i == len(entries) - 1)
                branch = "└── " if is_last else "├── "
                lines.append(f"{prefix}{branch}{entry}")
                if os.path.isdir(full_path):
                    extension = "    " if is_last else "│   "
                    _walk(full_path, depth + 1, prefix + extension)
        _walk(root_path, 1, "")
        return "\n".join(lines)

    def classify_files(self):
        files = self.get_all_files()
        if not files:
            QMessageBox.warning(self, "No files selected", "Please add files or folders first.")
            return

        # Validate file extensions before processing
        valid_files = []
        for f in files:
            _, ext = os.path.splitext(f)
            ext = ext.lower().strip()
            if ext in ALLOWED_EXTENSIONS_VFX or ext in ALLOWED_EXTENSIONS_COMMERCIAL:
                valid_files.append(os.path.basename(f))
            else:
                self.output_box.append(f"Skipped invalid file: {f} (extension not allowed, detected: '{ext}')")

        if not valid_files:
            QMessageBox.warning(self, "No valid files", "All selected files have invalid extensions.")
            return

        # Format filenames for prompt (one per line, as in examples)
        formatted_filenames = "\n".join(valid_files)
        # Get destination project folder from input
        project_root = self.project_folder_input.text().strip()
        if not project_root.endswith("/"):
            project_root += "/"
        # Get actual project structure
        if os.path.isdir(project_root):
            project_structure = self.get_folder_structure(project_root)
        else:
            project_structure = "(Project folder does not exist or is not accessible)"        # Select prompt template based on structure selection and replace placeholders
        structure_choice = self.structure_dropdown.currentText()
        if structure_choice == "KENT":
            prompt = PROMPT_TEMPLATE_KENT.replace('{file_list}', formatted_filenames).replace('{project_root}', project_root).replace('{project_structure}', project_structure)
        else:
            prompt = PROMPT_TEMPLATE_SPHERE.replace('{file_list}', formatted_filenames).replace('{project_root}', project_root).replace('{project_structure}', project_structure)

        try:
            # Get LLM instance based on selected provider
            llm = self.get_llm_instance()
            provider = self.provider_dropdown.currentText()
            
            # Debug information
            print(f"Debug: Provider: {provider}")
            print(f"Debug: Model Name: {self.model_dropdown.currentText()}")
            print(f"Debug: Structure: {structure_choice}")
            print(f"Debug: Prompt: {prompt}")
            print(f"Debug: Project Folder: {project_root}")

            response = llm.invoke(prompt)
            llm = self.get_llm_instance()
            provider = self.provider_dropdown.currentText()
            
            # Debug information
            print(f"Debug: Provider: {provider}")
            print(f"Debug: Model Name: {self.model_dropdown.currentText()}")
            print(f"Debug: Structure: {structure_choice}")
            print(f"Debug: Prompt: {prompt}")
            print(f"Debug: Project Folder: {project_root}")

            response = llm.invoke(prompt)

            print(f"Debug: Response received: {response}")

            # Try to extract JSON from the response robustly
            import re
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                json_str = match.group(0)
                classification = json.loads(json_str)
                self.output_box.append("Classification Results (filename -> folder):\n")
                self.results_table.setRowCount(0)
                for fname, folder in classification.items():
                    # Prepend the project folder to the classified path
                    full_path = os.path.join(project_root, folder.lstrip('/'))
                    self.output_box.append(f"{fname} -> {full_path}")
                    # Add to results table
                    row = self.results_table.rowCount()
                    self.results_table.insertRow(row)
                    self.results_table.setItem(row, 0, QTableWidgetItem(fname))
                    self.results_table.setItem(row, 1, QTableWidgetItem(full_path))
                    # Add a checkbox for selection
                    checkbox = QCheckBox()
                    self.results_table.setCellWidget(row, 2, checkbox)                # Auto-resize columns to fit content after populating
                self.results_table.resizeColumnsToContents()
            else:
                self.output_box.append("Error: No JSON found in AI response.\nRaw response:\n" + response)

        except ValueError as e:
            # This catches our custom validation errors from get_llm_instance
            self.output_box.append(f"Configuration Error: {e}")
        except subprocess.TimeoutExpired:
            self.output_box.append("Error: The request timed out.")
        except subprocess.CalledProcessError as e:
            print(f"Debug: CalledProcessError: {e}")
            self.output_box.append(f"Error calling AI service: {e}")
        except json.JSONDecodeError as e:
            self.output_box.append(f"Error: Failed to parse the response from AI service.\nRaw response:\n{response}")
        except Exception as e:
            print(f"Debug: General Exception: {e}")
            self.output_box.append(f"Error calling AI service: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    self._add_folder_recursive(path)
                elif os.path.isfile(path):
                    if path not in self.get_all_files():
                        self.file_list_widget.addItem(path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _add_folder_recursive(self, folder):
        import re
        from collections import defaultdict, deque
        seq_dict = defaultdict(list)
        visited = set()
        queue = deque([folder])
        total_dirs = 0
        # First pass: count total dirs for progress
        temp_queue = deque([folder])
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
        # Reset for actual scan
        visited.clear()
        queue = deque([folder])
        processed_dirs = 0
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
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
            processed_dirs += 1
            if total_dirs > 0:
                progress = int((processed_dirs / total_dirs) * 100)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()
        # Add only one representative per sequence, and all non-sequence files
        for key, files in seq_dict.items():
            if len(files) > 1 and '####' in key:
                rep = key  # e.g., shot_v001.####.exr
            else:
                rep = files[0]
            if rep not in self.get_all_files():
                self.file_list_widget.addItem(rep)
        self.progress_bar.setVisible(False)

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

    def set_destination_folder(self, folder_path):
        self.project_folder_input.setText(folder_path)

    def send_selected_to_ai(self, paths):
        for path in paths:
            if os.path.isdir(path):
                self._add_folder_recursive(path)
            elif os.path.isfile(path):
                if path not in self.get_all_files():
                    self.file_list_widget.addItem(path)

    def get_selected_results(self):
        selected = []
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 2)
            if checkbox and checkbox.isChecked():
                src = self.results_table.item(row, 0).text()
                dst = self.results_table.item(row, 1).text()
                selected.append((src, dst))
        return selected

    def move_selected_files(self):
        selected = self.get_selected_results()
        if not selected:
            QMessageBox.warning(self, "No files selected", "Please select files to move.")
            return
        for src, dst in selected:
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                src_full = self.find_full_path(src)
                if src_full and os.path.exists(src_full):
                    os.rename(src_full, dst)
            except Exception as e:
                self.output_box.append(f"Error moving {src}: {e}")
        QMessageBox.information(self, "Move Complete", "Selected files have been moved.")

    def copy_selected_files(self):
        import shutil
        selected = self.get_selected_results()
        if not selected:
            QMessageBox.warning(self, "No files selected", "Please select files to copy.")
            return
        for src, dst in selected:
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                src_full = self.find_full_path(src)
                if src_full and os.path.exists(src_full):
                    shutil.copy2(src_full, dst)
            except Exception as e:
                self.output_box.append(f"Error copying {src}: {e}")
        QMessageBox.information(self, "Copy Complete", "Selected files have been copied.")

    def find_full_path(self, fname):
        # Try to find the full path of the file in the file_list_widget
        for i in range(self.file_list_widget.count()):
            item_text = self.file_list_widget.item(i).text()
            if os.path.basename(item_text) == fname:
                return item_text        # If not found, try current working directory
        if os.path.exists(fname):
            return os.path.abspath(fname)
        return None

    def select_all_results(self):
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 2)
            if checkbox:
                checkbox.setChecked(True)

    def select_none_results(self):
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 2)
            if checkbox:
                checkbox.setChecked(False)

    def closeEvent(self, event):
        # Save window and dock state
        with open(self.settings_path, 'wb') as f:
            f.write(self.saveState())
        with open(self.settings_geometry_path, 'wb') as f:
            f.write(self.saveGeometry())
        event.accept()
    
    def send_chat_message(self):
        user_msg = self.chat_input.text().strip()
        if not user_msg:
            return
        mode = self.chat_mode_dropdown.currentText().lower()
        self.chat_history.append(f"<b>You:</b> {user_msg}")
        self.chat_input.clear()
        
        try:
            # Get LLM instance based on selected provider
            llm = self.get_llm_instance()
        except ValueError as e:
            self.chat_history.append(f"<span style='color:red'>Configuration Error: {e}</span>")
            return
            
        try:
            if mode == "chat":
                response = llm.invoke(user_msg)
                self.chat_history.append(f"<b>Model:</b> {response}")
            elif mode == "refine":
                # Use selected results from results table for context
                selected = self.get_selected_results()
                if not selected:
                    self.chat_history.append("<span style='color:red'>No files selected in results table for refinement.</span>")
                    return
                # Convert absolute paths to relative paths for the prompt
                project_root = self.project_folder_input.text().strip()
                file_lines = []
                for src, dst in selected:
                    # Make destination relative to project root
                    try:
                        rel_dst = os.path.relpath(dst, project_root)
                        file_lines.append(f"{src} -> {rel_dst}")
                    except ValueError:
                        # If relpath fails, use the destination as-is
                        file_lines.append(f"{src} -> {dst}")
                files_str = "\n".join(file_lines)
                
                # Get current project structure
                if os.path.isdir(project_root):
                    project_structure = self.get_folder_structure(project_root, max_depth=3)
                else:
                    project_structure = "(Project folder does not exist or is not accessible)"
                  # Compose prompt_refine with user_msg as feedback and project structure
                with open(os.path.join(os.path.dirname(__file__), 'prompt_refine.md'), 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
                prompt = prompt_template.replace('{selected_files}', files_str).replace('{user_feedback}', user_msg).replace('{project_structure}', project_structure)
                response = llm.invoke(prompt)
                self.chat_history.append(f"<b>Model (Refine):</b> {response}")
                # --- Update results table with new mapping (by filename only) ---
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
                        self.chat_history.append("<span style='color:green'>Results table updated with new destinations.</span>")
                    except Exception as e:
                        self.chat_history.append(f"<span style='color:red'>Error parsing model response as JSON: {e}</span>")
                else:                    self.chat_history.append("<span style='color:orange'>No JSON mapping found in model response. No changes made to results table.</span>")
        except Exception as e:
            self.chat_history.append(f"<span style='color:red'>Error: {e}</span>")

    def refine_selected_results(self):
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
            project_structure = self.get_folder_structure(project_root, max_depth=3)
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

    def load_openrouter_key(self):
        """Load OpenRouter API key from secure storage"""
        if not SECURE_STORAGE_AVAILABLE:
            QMessageBox.warning(self, "Secure Storage Unavailable", 
                              "Please install the 'cryptography' package to use encrypted key storage.")
            return
            
        password, ok = QInputDialog.getText(self, "Load API Key", 
                                          "Enter master password:", 
                                          QLineEdit.Password)
        if not ok or not password:
            return
            
        try:
            storage = SecureStorage()
            api_key = storage.load_api_key("openrouter", password)
            
            if api_key:
                self.openrouter_api_key_input.setText(api_key)
                self.output_box.append("✅ OpenRouter API key loaded successfully.")
            else:
                QMessageBox.information(self, "No Key Found", 
                                      "No stored API key found or incorrect password.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load API key: {e}")
    
    def save_openrouter_key(self):
        """Save OpenRouter API key to secure storage"""
        if not SECURE_STORAGE_AVAILABLE:
            QMessageBox.warning(self, "Secure Storage Unavailable", 
                              "Please install the 'cryptography' package to use encrypted key storage.")
            return
            
        api_key = self.openrouter_api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "No API Key", "Please enter an API key first.")
            return
            
        password, ok = QInputDialog.getText(self, "Save API Key", 
                                          "Enter master password to encrypt the key:", 
                                          QLineEdit.Password)
        if not ok or not password:
            return
            
        # Confirm password
        confirm_password, ok = QInputDialog.getText(self, "Confirm Password", 
                                                  "Confirm master password:", 
                                                  QLineEdit.Password)
        if not ok or password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            return
            
        try:
            storage = SecureStorage()
            success = storage.save_api_key("openrouter", api_key, password)
            
            if success:
                self.output_box.append("✅ OpenRouter API key saved securely.")
                QMessageBox.information(self, "Success", 
                                      "API key has been encrypted and saved securely.")
            else:
                QMessageBox.critical(self, "Error", "Failed to save API key.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save API key: {e}")

def main():
    app = QApplication(sys.argv)
    win = FileClassifierApp()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
