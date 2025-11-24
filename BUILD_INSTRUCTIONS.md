# Build Instructions - AI File Organizer

## 🎯 Quick Build

The easiest way to build the executables is to use the provided PowerShell script:

```powershell
.\build_executables.ps1
```

This will automatically:
- Install/update all required dependencies (PyQt5, requests, langchain, etc.)
- Build both versions of the application
- Place executables in the `dist` folder

---

## 📦 What Gets Built

### Two Versions Available:

1. **FIelOrganizer.exe** (Standard Version)
   - Single-threaded processing
   - Simpler, more stable
   - Good for most use cases

2. **FilelOrganizer_MT.exe** (Multi-threaded Version)
   - Parallel file processing
   - Faster for large batches
   - Advanced features

**Both versions now include LM Studio support!**

---

## 🔧 Manual Build Process

If you prefer to build manually:

### Prerequisites

```powershell
# Install all required dependencies
pip install -r requirements.txt
```

This installs:
- **PyQt5** - GUI framework
- **requests** - HTTP library for API calls
- **langchain & langchain-ollama** - LLM framework
- **cryptography** - Encrypted API key storage
- **pyinstaller** - Build tool

### Build Standard Version
```powershell
python -m PyInstaller FIelOrganizer.spec --clean
```

### Build Multi-threaded Version
```powershell
python -m PyInstaller FilelOrganizer_MT.spec --clean
```

### Output Location
Executables will be created in: `dist\`

---

## 📋 Build Configuration

### Spec Files
- `FIelOrganizer.spec` - Configuration for standard version
- `FilelOrganizer_MT.spec` - Configuration for multi-threaded version

### Included Data Files
Both builds automatically include:
- `prompt_kent.md` - KENT folder structure prompts
- `prompt_sphere.md` - Sphere folder structure prompts
- `prompt_refine.md` - Refinement prompts

### Build Settings
- **Console**: Disabled (GUI-only application)
- **UPX Compression**: Enabled (smaller file size)
- **One-file mode**: Enabled (single .exe file)
- **Icon**: Default PyInstaller icon

---

## 🚀 Distribution

### What to Distribute
The executables in the `dist` folder are standalone and can be distributed without Python installed.

### Files to Include with Distribution:
1. **FIelOrganizer.exe** or **FilelOrganizer_MT.exe**
2. **LMSTUDIO_QUICK_START.md** (LM Studio setup guide)
3. **OPENROUTER_QUICK_START.md** (OpenRouter setup guide)
4. **README.md** (General documentation)

### System Requirements for End Users:
- Windows 10/11 (64-bit)
- No Python installation required
- For LM Studio: 8GB+ RAM recommended
- For cloud providers: Internet connection

---

## 🔍 Troubleshooting Build Issues

### "PyInstaller not found"
**Solution**: Install PyInstaller
```powershell
pip install pyinstaller
```

### "Module not found" errors during build
**Solution**: Install missing dependencies
```powershell
pip install PyQt5 langchain langchain-ollama requests cryptography
```

### Build succeeds but exe crashes
**Solution**: Check the build warnings
```powershell
# View warnings
cat build\FIelOrganizer\warn-FIelOrganizer.txt
```

### Large executable size
**Solution**: This is normal for PyQt5 apps. The exe includes:
- Python runtime
- PyQt5 libraries
- All dependencies
- Typical size: 50-100 MB

---

## 🔄 Rebuilding After Changes

Whenever you modify the source code:

1. **Quick rebuild** (recommended):
   ```powershell
   .\build_executables.ps1
   ```

2. **Manual rebuild**:
   ```powershell
   python -m PyInstaller FIelOrganizer.spec --clean
   python -m PyInstaller FilelOrganizer_MT.spec --clean
   ```

The `--clean` flag ensures old build artifacts are removed.

---

## 📝 Customizing the Build

### Adding an Icon
1. Create or obtain a `.ico` file
2. Edit the spec file:
   ```python
   exe = EXE(
       ...
       icon='path/to/your/icon.ico',
       ...
   )
   ```

### Including Additional Data Files
Edit the spec file's `datas` list:
```python
datas=[
    ('prompt_kent.md', '.'),
    ('prompt_sphere.md', '.'),
    ('prompt_refine.md', '.'),
    ('your_file.txt', '.'),  # Add your file here
]
```

### Reducing File Size
1. Remove UPX compression (may increase size):
   ```python
   upx=False,
   ```

2. Exclude unused modules in spec file:
   ```python
   excludes=['tkinter', 'matplotlib', 'numpy'],
   ```

---

## ✅ Verification

After building, verify the executable works:

1. Navigate to `dist` folder
2. Double-click `FIelOrganizer.exe` or `FilelOrganizer_MT.exe`
3. The application should launch without errors
4. Test all AI providers:
   - Ollama (if installed)
   - OpenRouter (with API key)
   - Mistral (with API key)
   - LM Studio (if running)

---

## 🎉 Success!

Your executables are ready for distribution. Users can run them without installing Python or any dependencies!

