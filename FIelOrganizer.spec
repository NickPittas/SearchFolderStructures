# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['FIelOrganizer.py'],
    pathex=[],
    binaries=[],
    datas=[('prompt_kent.md', '.'), ('prompt_sphere.md', '.'), ('prompt_refine.md', '.')],
    hiddenimports=[
        'requests', 'requests.adapters', 'requests.exceptions', 'urllib3',
        'langchain', 'langchain_ollama', 'langchain_ollama.llms',
        'langchain_core', 'langchain_core.prompts', 'langchain_core.language_models',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FIelOrganizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

