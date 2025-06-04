# SearchFolderStructures

A collection of Python tools for scanning, organizing, and managing folder structures with AI-powered file classification capabilities.

## 🎯 Overview

This project provides several utilities for working with large folder structures, particularly useful for VFX/post-production workflows:

- **AI File Organizer** - Main GUI application for classifying and organizing files using AI
- **Folder Structure Scanner** - Tool for scanning and exporting folder structures to JSON
- **Structure Analyzer** - Utilities for converting folder structures to JSON format

## 🚀 Main Applications

### 1. AI File Organizer (`FIelOrganizer.py`)

The primary application featuring a modern PyQt5 GUI for intelligent file organization.

**Features:**
- 🤖 **AI-Powered Classification** - Uses Ollama LLM to automatically classify files
- 📁 **Drag & Drop Interface** - Easy file and folder addition
- 🎨 **Dark Theme UI** - Modern, professional interface with dockable panels
- 🔄 **Batch Operations** - Move/copy multiple files at once
- 📊 **Results Table** - Review and modify AI suggestions before applying
- 💬 **Chat Interface** - Interact with AI for refinements
- 🏗️ **Template Structures** - KENT and Sphere VFX folder structures
- 🔍 **File Browser** - Integrated file system browser
- ⚡ **Sequence Detection** - Automatically detects and groups image sequences

**Supported File Types:**
- **VFX/Commercial**: `.exr`, `.dpx`, `.tif`, `.png`, `.mov`, `.mxf`, `.avi`, `.psd`, `.ai`, `.jpg`, `.mp4`, `.docx`, `.pdf`, `.xlsx`, `.pptx`, `.wav`, `.mp3`, `.aiff`, `.nk`, `.aep`, `.prproj`, `.drp`, `.xml`, `.edl`, `.json`, `.txt`, `.aaf`

**How to Use:**
1. Launch the application: `python FIelOrganizer.py`
2. Set up Ollama server URL and select a model
3. Add files or folders via drag-drop or buttons
4. Set destination project folder
5. Choose folder structure template (KENT or Sphere)
6. Click "Classify with Ollama" to get AI suggestions
7. Review results and move/copy files as needed

### 2. AI Folder Scanner (`ai_folder_scanner.py`)

Tkinter-based application for scanning large directory structures and exporting to JSON.

**Features:**
- 🚀 **High-Performance Scanning** - Efficiently handles large directories
- 📈 **Real-time Progress** - Visual progress bar with file counts
- 🔄 **Sequence Detection** - Groups numbered file sequences
- 📊 **JSON Export** - Structured output for analysis
- ➕ **Append Mode** - Add to existing scans without duplicates
- 🎯 **Drag & Drop** - Easy folder addition

**Usage:**
```bash
python ai_folder_scanner.py
```

### 3. Folder Structure to JSON (`folder_structure_to_json.py`)

Command-line and GUI tools for converting folder structures to JSON format.

**Command Line:**
```bash
python folder_structure_to_json.py /path/to/folder -o output.json
```

**GUI Version:**
```bash
python folder_structure_to_json_ui.py
```

## 🛠️ Installation

### Prerequisites

- Python 3.7+
- Ollama (for AI classification features)

### Dependencies

Install required packages:

```bash
pip install PyQt5 langchain-ollama tkinterdnd2 tqdm
```

### Ollama Setup

1. Install [Ollama](https://ollama.ai/)
2. Pull a compatible model:
   ```bash
   ollama pull gemma2:2b
   # or
   ollama pull llama3.1:8b
   ```
3. Start Ollama server:
   ```bash
   ollama serve
   ```

## 📁 Project Structure

```
SearchFolderStructures/
├── FIelOrganizer.py              # Main AI file organizer application
├── ai_folder_scanner.py          # Folder structure scanner
├── folder_structure_to_json.py   # CLI folder-to-JSON converter
├── folder_structure_to_json_ui.py # GUI folder-to-JSON converter
├── prompt_kent.md               # KENT VFX structure template
├── prompt_sphere.md             # Sphere VFX structure template
├── prompt_refine.md             # AI refinement prompt template
├── KENT.json                    # KENT structure definition
├── Sphere.json                  # Sphere structure definition
├── KENT_structure_description.md # KENT structure documentation
└── GenerateFindings.ps1         # PowerShell utility script
```

## 🎨 VFX Folder Templates

### KENT Structure
Optimized for traditional VFX pipelines:
- `2D/` - Illustrations, Images, Storyboards
- `3D/` - Models, Previz, Renders, Textures
- `Audio/` - Music, SFX, Dialogue
- `Deliverables/` - Finals, Review versions
- `Documents/` - Scripts, Notes, Spreadsheets
- `Projects/` - Native project files (AE, Nuke, etc.)

### Sphere Structure
Alternative VFX organization structure with similar categories but different hierarchy.

## 🤖 AI Integration

The AI classification system uses Ollama to analyze file names, types, and content to suggest appropriate folder destinations. The system:

1. **Analyzes** file names and extensions
2. **Considers** existing project structure
3. **Suggests** optimal folder placement
4. **Allows** user refinement and feedback
5. **Learns** from user corrections

## 🔧 Configuration

### Ollama Settings
- **Default URL**: `http://localhost:11434`
- **Recommended Models**: `gemma2:2b`, `llama3.1:8b`
- **Default Model**: `gemma3:12b` (if available)

### Window State
The application automatically saves and restores:
- Window size and position
- Dock panel layout
- Last used settings

## 📝 Usage Examples

### Organizing VFX Assets
1. Add render outputs from various software
2. Let AI classify into appropriate render folders
3. Review and adjust suggestions
4. Batch move files to final structure

### Project Cleanup
1. Scan messy project directories
2. Use AI to suggest reorganization
3. Preview changes before applying
4. Maintain consistent folder structure

### Asset Management
1. Import mixed media files
2. Classify by type and purpose
3. Organize into production-ready structure
4. Generate structured exports

## 🚧 Development

### Adding New Templates
1. Create new prompt markdown file
2. Define JSON structure
3. Add to dropdown in `FIelOrganizer.py`
4. Update prompt loading logic

### Extending File Support
1. Update `ALLOWED_EXTENSIONS_*` constants
2. Add file type recognition logic
3. Update classification prompts

## 📄 License

This project is available for educational and professional use. Please respect any dependencies' licenses.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the project.

## 🆘 Troubleshooting

### Common Issues

**Ollama Connection Error:**
- Ensure Ollama is running: `ollama serve`
- Check URL in settings (default: `http://localhost:11434`)
- Verify model is available: `ollama list`

**File Permission Errors:**
- Run with appropriate permissions
- Check folder access rights
- Ensure destination folders are writable

**Memory Issues with Large Scans:**
- Use folder scanner for very large directories
- Process in smaller batches
- Monitor system resources

### Performance Tips

- Use SSD storage for better performance
- Limit scan depth for large directories
- Close unnecessary dock panels
- Use sequence detection for image sequences

---

*Built for VFX professionals and anyone working with complex folder structures.*
