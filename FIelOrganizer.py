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
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPalette, QColor
from langchain_core.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM

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

# LM Studio API wrapper
class LMStudioLLM:
    """LM Studio API wrapper for compatibility with Ollama/OpenRouter interface"""

    def __init__(self, model, base_url="http://localhost:1234/v1"):
        self.model = model
        self.base_url = base_url.rstrip('/') + '/chat/completions'

    def invoke(self, prompt):
        headers = {
            "Content-Type": "application/json"
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
            raise Exception(f"LM Studio API Error: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected response format from LM Studio: {e}")

# Mistral models for dropdown selection
class MistralLLM:
    """Simple Mistral API wrapper for compatibility with Ollama/OpenRouter interface"""
    def __init__(self, model, api_key):
        self.model = model
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1/chat/completions"

    def invoke(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        # Mistral returns choices[0]['message']['content']
        return result['choices'][0]['message']['content']

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
    BATCH_SIZE = 15

    def __init__(self):
        super().__init__()  # Ensure the QMainWindow base class is initialized first
        self.setGeometry(200, 200, 1000, 600)
        self.setWindowTitle("AI File Organizer")

        # --- Apply dark orange theme and custom styles globally ---
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
        # Set file_list_widget to allow multi-selection
        self.file_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list_widget.customContextMenuRequested.connect(self.on_selected_files_context_menu)
        # --- Dock widget setup ---
        selected_files_dock = QDockWidget("Selected Files", self)
        selected_files_dock.setObjectName("SelectedFilesDock")
        selected_files_dock.setWidget(self.file_list_widget)
        selected_files_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        selected_files_dock.setFloating(True)
        selected_files_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        selected_files_dock.setStyleSheet("QDockWidget { background: #2e233a; border: 2px solid #d53a7b; }")
        selected_files_dock.setWindowIcon(icon_add)
        self.addDockWidget(Qt.LeftDockWidgetArea, selected_files_dock)

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
        self.provider_dropdown.addItems(["Ollama", "OpenRouter", "Mistral", "LM Studio"])
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
        
        # Mistral specific settings
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

        # LM Studio specific settings
        self.lmstudio_settings = QWidget()
        lmstudio_layout = QVBoxLayout()
        lmstudio_layout.addWidget(QLabel("LM Studio Server URL:"))
        self.lmstudio_url_input = QLineEdit("http://localhost:1234/v1")
        lmstudio_layout.addWidget(self.lmstudio_url_input)
        self.lmstudio_settings.setLayout(lmstudio_layout)
        self.lmstudio_settings.setVisible(False)  # Initially hidden
        ai_setup_layout.addWidget(self.lmstudio_settings)

        # Fetch models button
        self.fetch_models_btn = QPushButton("Fetch Models")
        self.fetch_models_btn.clicked.connect(self.fetch_models)
        ai_setup_layout.addWidget(self.fetch_models_btn)
        
        # Add batch size control
        batch_row = QHBoxLayout()
        batch_row.addWidget(QLabel("Batch Size:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(100)
        self.batch_size_spin.setValue(15)
        self.batch_size_spin.setToolTip("Number of files to send to the AI per batch")
        batch_row.addWidget(self.batch_size_spin)
        ai_setup_layout.addLayout(batch_row)

        # Add folder structure depth control
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

        # Add Remove Selected button
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.remove_selected_btn.clicked.connect(self.remove_selected_files)
        btn_layout.addWidget(self.remove_selected_btn)

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
        self.results_table.setSortingEnabled(True)  # Enable sorting
        # Connect row click to toggle checkbox
        self.results_table.itemClicked.connect(self.on_results_table_item_clicked)
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

        # Info label for status updates
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: orange; font-size: 11pt; font-weight: bold; padding: 4px;")
        self.right_layout.addWidget(self.info_label)

        # Store OpenRouter password in memory for session
        self._openrouter_password = None
        # Store Mistral password in memory for session
        self._mistral_password = None
        # Path for persistent Mistral key storage
        self.mistral_key_path = os.path.join(os.path.expanduser('~'), 'FIelOrganizer_mistral_key.dat')

        # Connect Mistral API key input to update in-memory key and save
        self.mistral_api_key_input.textChanged.connect(self.on_mistral_api_key_changed)

        # Add Load/Save buttons for Mistral key
        mistral_api_key_row = QHBoxLayout()
        mistral_api_key_row.addWidget(self.mistral_api_key_input)
        self.load_mistral_key_btn = QPushButton("Load")
        self.load_mistral_key_btn.setMaximumWidth(60)
        self.load_mistral_key_btn.clicked.connect(self.load_mistral_key)
        mistral_api_key_row.addWidget(self.load_mistral_key_btn)
        self.save_mistral_key_btn = QPushButton("Save")
        self.save_mistral_key_btn.setMaximumWidth(60)
        self.save_mistral_key_btn.clicked.connect(self.save_mistral_key)
        mistral_api_key_row.addWidget(self.save_mistral_key_btn)
        # Insert the row into the Mistral settings layout
        mistral_layout = self.mistral_settings.layout()
        mistral_layout.addLayout(mistral_api_key_row)

        # Load Mistral key on startup if available
        self.load_mistral_key()

    def on_provider_changed(self):
        """Handle provider selection change"""
        provider = self.provider_dropdown.currentText()
        if provider == "Ollama":
            self.ollama_settings.setVisible(True)
            self.openrouter_settings.setVisible(False)
            self.mistral_settings.setVisible(False)
            self.lmstudio_settings.setVisible(False)
        elif provider == "OpenRouter":
            self.ollama_settings.setVisible(False)
            self.openrouter_settings.setVisible(True)
            self.mistral_settings.setVisible(False)
            self.lmstudio_settings.setVisible(False)
        elif provider == "Mistral":
            self.ollama_settings.setVisible(False)
            self.openrouter_settings.setVisible(False)
            self.mistral_settings.setVisible(True)
            self.lmstudio_settings.setVisible(False)
            # Restore Mistral API key from memory if available
            if self._mistral_password is not None:
                self.mistral_api_key_input.setText(self._mistral_password)
        elif provider == "LM Studio":
            self.ollama_settings.setVisible(False)
            self.openrouter_settings.setVisible(False)
            self.mistral_settings.setVisible(False)
            self.lmstudio_settings.setVisible(True)
        # Clear model dropdown when provider changes
        self.model_dropdown.clear()

    def on_mistral_api_key_changed(self, text):
        self._mistral_password = text
        # Save key on change
        self.save_mistral_key()

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
        elif provider == "Mistral":
            try:
                self.model_dropdown.clear()
                self.model_dropdown.addItems(MISTRAL_MODELS)
                self.model_dropdown.setEditable(False)
                self.model_dropdown.setCurrentIndex(0)
                self.output_box.append("Mistral models loaded successfully.")
            except Exception as e:
                self.model_dropdown.clear()
                self.model_dropdown.addItem("Error loading Mistral models")
                self.output_box.append(f"Failed to load Mistral models: {e}")
        elif provider == "LM Studio":
            try:
                lmstudio_url = self.lmstudio_url_input.text().strip()
                if not lmstudio_url:
                    raise ValueError("Please enter a valid LM Studio server URL")

                # Fetch models from LM Studio API
                models_url = lmstudio_url.rstrip('/') + '/models'
                response = requests.get(models_url, timeout=5)
                response.raise_for_status()
                result = response.json()

                # Extract model IDs from the response
                models = [model['id'] for model in result.get('data', [])]

                if not models:
                    models = ["No models found"]

                self.model_dropdown.clear()
                self.model_dropdown.addItems(models)
                self.model_dropdown.setEditable(False)
                if models and models[0] != "No models found":
                    self.model_dropdown.setCurrentIndex(0)
                self.output_box.append(f"LM Studio models loaded successfully. Found {len(models)} model(s).")

            except Exception as e:
                self.model_dropdown.clear()
                self.model_dropdown.addItem("Error fetching models")
                self.output_box.append(f"Failed to fetch LM Studio models: {e}")

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
            # Store in-memory for session
            self._openrouter_password = api_key
            return OpenRouterLLM(model=model_name, api_key=api_key)
        elif provider == "Mistral":
            # Use in-memory key if available
            api_key = self._mistral_password if self._mistral_password is not None else self.mistral_api_key_input.text().strip()
            if not api_key:
                raise ValueError("Please enter your Mistral API key")
            self._mistral_password = api_key
            return MistralLLM(model=model_name, api_key=api_key)
        elif provider == "LM Studio":
            lmstudio_url = self.lmstudio_url_input.text().strip()
            if not lmstudio_url:
                raise ValueError("Please enter a valid LM Studio server URL")
            return LMStudioLLM(model=model_name, base_url=lmstudio_url)
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
        self.set_info("Counting dirs...")
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
            processed_dirs += 1
            if total_dirs > 0:
                progress = int((processed_dirs / total_dirs) * 100)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()
                self.set_info(f"Scanning: {current}")
        # Add only one representative per sequence, and all non-sequence files
        for key, files in seq_dict.items():
            if len(files) > 1 and '####' in key:
                rep = key
            else:
                rep = files[0]
            if rep not in self.get_all_files():
                self.file_list_widget.addItem(rep)
        self.progress_bar.setVisible(False)
        self.set_info("Folder scan complete.")

    def clear_list(self):
        self.file_list_widget.clear()
        self.output_box.clear()

    def get_all_files(self):
        return [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())]

    def get_folder_structure(self, root_path, max_depth=6, prefix=""):
        """Recursively build a tree-like string of the folder structure up to max_depth, including only folders (no files)."""
        lines = []
        def _walk(path, depth, prefix):
            if depth > max_depth:
                return
            try:
                entries = sorted(os.listdir(path))
            except Exception:
                return
            # Only include directories
            dirs = [entry for entry in entries if os.path.isdir(os.path.join(path, entry))]
            for i, entry in enumerate(dirs):
                full_path = os.path.join(path, entry)
                is_last = (i == len(dirs) - 1)
                branch = "└── " if is_last else "├── "
                lines.append(f"{prefix}{branch}{entry}")
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
        self.set_info("Validating selected files...")
        for f in files:
            _, ext = os.path.splitext(f)
            ext = ext.lower().strip()
            if ext in ALLOWED_EXTENSIONS_VFX or ext in ALLOWED_EXTENSIONS_COMMERCIAL:
                valid_files.append(f)  # Use full path, not just basename
            else:
                self.output_box.append(f"Skipped invalid file: {f} (extension not allowed, detected: '{ext}')")

        if not valid_files:
            self.set_info("")
            QMessageBox.warning(self, "No valid files", "All selected files have invalid extensions.")
            return

        # --- Batching logic ---
        batch_size = self.batch_size_spin.value() if hasattr(self, 'batch_size_spin') else self.BATCH_SIZE
        total_files = len(valid_files)
        num_batches = (total_files + batch_size - 1) // batch_size
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        processed_files = 0
        self.results_table.setRowCount(0)  # Clear previous results

        all_results = []  # Collect (src, dst) tuples for all batches
        for batch_idx in range(num_batches):
            batch_files = valid_files[batch_idx * batch_size : (batch_idx + 1) * batch_size]
            formatted_filenames = "\n".join([os.path.basename(f) for f in batch_files])
            self.set_info(f"Sending batch {batch_idx+1}/{num_batches} to AI for classification...")
            self.progress_bar.setValue(int((processed_files / total_files) * 100))
            QApplication.processEvents()

            # Get destination project folder from input
            project_root = self.project_folder_input.text().strip()
            if not project_root.endswith("/"):
                project_root += "/"
            # Get actual project structure
            folder_depth = self.folder_depth_spin.value()
            if os.path.isdir(project_root):
                project_structure = self.get_folder_structure(project_root, max_depth=folder_depth)
            else:
                project_structure = "(Project folder does not exist or is not accessible)"
            structure_choice = self.structure_dropdown.currentText()
            if structure_choice == "KENT":
                prompt = PROMPT_TEMPLATE_KENT.replace('{file_list}', formatted_filenames).replace('{project_root}', project_root).replace('{project_structure}', project_structure)
            else:
                prompt = PROMPT_TEMPLATE_SPHERE.replace('{file_list}', formatted_filenames).replace('{project_root}', project_root).replace('{project_structure}', project_structure)

            try:
                llm = self.get_llm_instance()
                self.set_info(f"Waiting for AI response for batch {batch_idx+1}/{num_batches}...")
                response = llm.invoke(prompt)
                self.set_info(f"Processing AI response for batch {batch_idx+1}/{num_batches}...")
                self.output_box.append(f"Raw AI response for batch {batch_idx+1}:\n{response}")
                match = re.search(r'\{{[\s\S]*\}}', response)
                classification = None
                json_str = None
                if match:
                    json_str = match.group(0)
                    self.output_box.append(f"[DEBUG] Extracted JSON string:\n{json_str}")
                    try:
                        classification = json.loads(json_str)
                    except Exception as e:
                        self.output_box.append(f"[DEBUG] Exception in json.loads (regex-extracted): {e}\nJSON string was:\n{json_str}")
                else:
                    self.output_box.append(f"[DEBUG] Regex failed to match JSON. Attempting to extract JSON code block.")
                    cleaned_response = response.strip()
                    json_block = None
                    lines = cleaned_response.splitlines()
                    start_idx = None
                    end_idx = None
                    # Find code block with ```json or ```
                    for i, line in enumerate(lines):
                        if line.strip().startswith('```json') or line.strip() == '```':
                            start_idx = i
                            break
                    if start_idx is not None:
                        # Find the next ``` after start_idx
                        for j in range(start_idx + 1, len(lines)):
                            if lines[j].strip() == '```':
                                end_idx = j
                                break
                        if end_idx is not None:
                            json_block = '\n'.join(lines[start_idx + 1:end_idx]).strip()
                    # Fallback: try to extract from first { to last }
                    if not json_block:
                        json_start = cleaned_response.find('{')
                        json_end = cleaned_response.rfind('}')
                        if json_start != -1 and json_end != -1 and json_end > json_start:
                            json_block = cleaned_response[json_start:json_end+1]
                    if json_block:
                        try:
                            classification = json.loads(json_block)
                            json_str = json_block
                            self.output_box.append(f"[DEBUG] Successfully parsed extracted JSON block.")
                        except Exception as e:
                            self.output_box.append(f"[DEBUG] Exception in json.loads (extracted block): {e}\nExtracted block was:\n{json_block}")
                    else:
                        self.output_box.append(f"[DEBUG] Could not find a JSON block in the response.")
                if classification and isinstance(classification, dict):
                    for fname, folder in classification.items():
                        # Try to find the full path for the file in this batch
                        full_src_path = None
                        for f in batch_files:
                            if os.path.basename(f) == fname:
                                full_src_path = f
                                break
                        # If not found in batch, try all files in the list
                        if not full_src_path:
                            for f in self.get_all_files():
                                if os.path.basename(f) == fname:
                                    full_src_path = f
                                    break
                        # If still not found, just use the filename (AI may hallucinate extra files)
                        if not full_src_path:
                            full_src_path = fname
                        full_path = os.path.join(project_root, folder.lstrip('/'))
                        full_destination = os.path.join(full_path, fname)
                        full_destination = os.path.normpath(full_destination).replace('\\', '/')
                        self.output_box.append(f"{full_src_path} -> {full_destination}")
                        all_results.append((full_src_path, full_destination))
                        QApplication.processEvents()  # Update UI after each row
                elif classification is not None:
                    self.output_box.append(f"[DEBUG] JSON loaded but not a dict. Type: {type(classification)}. Value: {classification}")
            except Exception as e:
                self.set_info("")
                self.output_box.append(f"Error in batch {batch_idx+1}: {e}")
                continue

        # Now populate the table in one go
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        self.results_table.setRowCount(len(all_results))
        for row, (src, dst) in enumerate(all_results):
            self.results_table.setItem(row, 0, QTableWidgetItem(src))
            self.results_table.setItem(row, 1, QTableWidgetItem(dst))
            checkbox = QCheckBox()
            self.results_table.setCellWidget(row, 2, checkbox)
        self.results_table.setSortingEnabled(True)
        self.results_table.resizeColumnsToContents()
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.set_info("Classification complete.")

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
                progress = int((i / total_files) + 0.5 * 100)  # Slightly faster completion
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
                    project_structure = self.get_folder_structure(project_root, max_depth=6)
                else:
                    project_structure = "(Project folder does not exist or is not accessible)"
                  # Compose prompt_refine with user_msg as feedback and project structure
                with open(os.path.join(os.path.dirname(__file__), 'prompt_refine.md'), 'r', encoding='utf-8') as f:
                    prompt_template = f.read()
                prompt = prompt_template.replace('{selected_files}', files_str).replace('{user_feedback}', user_msg).replace('{project_structure}', project_structure)
                # Log the full prompt for debugging
                self.chat_history.append("<b>Debug: Full prompt sent to LLM:</b>")
                self.chat_history.append(f"<pre>{prompt}</pre>")
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
                else:
                    self.chat_history.append("<span style='color:orange'>No JSON mapping found in model response. No changes made to results table.</span>")
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

    def save_mistral_key(self):
        key = self.mistral_api_key_input.text().strip()
        try:
            with open(self.mistral_key_path, 'w', encoding='utf-8') as f:
                f.write(key)
        except Exception as e:
            self.output_box.append(f"[DEBUG] Failed to save Mistral API key: {e}")

    def load_mistral_key(self):
        try:
            if os.path.exists(self.mistral_key_path):
                with open(self.mistral_key_path, 'r', encoding='utf-8') as f:
                    key = f.read().strip()
                    self._mistral_password = key
                    self.mistral_api_key_input.setText(key)
        except Exception as e:
            self.output_box.append(f"[DEBUG] Failed to load Mistral API key: {e}")

    def remove_selected_files(self):
        """Remove selected files from the file_list_widget."""
        selected_items = self.file_list_widget.selectedItems()
        for item in selected_items:
            self.file_list_widget.takeItem(self.file_list_widget.row(item))

    def set_info(self, msg):
        """Set the info label text."""
        self.info_label.setText(msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileClassifierApp()
    window.show()
    sys.exit(app.exec_())
