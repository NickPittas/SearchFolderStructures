import sys
import os
import json
import concurrent.futures
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG

def scan_folder_structure(root_path, log_func=None):
    structure = {}
    try:
        entries = list(os.scandir(root_path))
    except Exception as e:
        if log_func:
            log_func(f"Error accessing {root_path}: {e}")
        return structure
    if log_func:
        log_func(f"Scanning: {root_path}")
    # Only collect subfolders
    subfolders = [entry for entry in entries if entry.is_dir()]
    # Use ThreadPoolExecutor for parallel scanning of subfolders
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_name = {
            executor.submit(scan_folder_structure, entry.path, log_func): entry.name
            for entry in subfolders
        }
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            try:
                structure[name] = future.result()
            except Exception as e:
                if log_func:
                    log_func(f"Error scanning {name}: {e}")
                structure[name] = {}
    return structure

class FolderStructureUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folder Structure to JSON")
        self.setGeometry(300, 300, 700, 500)
        self.setAcceptDrops(True)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Drag and drop a folder here, or use the button below."))

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box)

        self.btn = QPushButton("Select Folder")
        self.btn.clicked.connect(self.select_folder)
        layout.addWidget(self.btn)

        self.setLayout(layout)

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
                    self.process_folder(path)
                    break
            event.acceptProposedAction()
        else:
            event.ignore()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.process_folder(folder)

    def process_folder(self, folder):
        self.result_box.clear()
        def log_func(msg):
            # Ensure thread-safe append to QTextEdit
            QMetaObject.invokeMethod(
                self.result_box,
                "append",
                Qt.QueuedConnection,
                Q_ARG(str, msg)
            )
        try:
            structure = scan_folder_structure(folder, log_func=log_func)
            QMetaObject.invokeMethod(
                self.result_box,
                "append",
                Qt.QueuedConnection,
                Q_ARG(str, "\n--- Folder Structure JSON ---\n")
            )
            QMetaObject.invokeMethod(
                self.result_box,
                "append",
                Qt.QueuedConnection,
                Q_ARG(str, json.dumps(structure, indent=2, ensure_ascii=False))
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to scan folder:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FolderStructureUI()
    win.show()
    sys.exit(app.exec_())
