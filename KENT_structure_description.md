# KENT.json Structure Documentation

This document describes the folder structure and the purpose of each section in KENT.json.

```
Files
├── 2D
│   ├── Illustrations      # Hand-drawn or digital illustrations
│   ├── Images             # General images and reference pictures
│   └── Storyboard         # Storyboard frames and sequences
├── 3D
│   ├── Models             # 3D model files (e.g., .obj, .fbx)
│   ├── Previz             # Previsualization files and scenes
│   ├── Renders            # Rendered images or animations from 3D
│   └── Textures           # Texture maps for 3D models
├── Audio                  # Audio files such as music, sound effects, and dialogue
├── Deliverables
│   ├── Finals             # Final approved deliverables
│   └── Review             # Files for review or feedback
├── Documents              # Documents such as scripts, notes, and spreadsheets
├── Projects
│   ├── AfterEffects       # Adobe After Effects project files
│   ├── Davinci            # DaVinci Resolve project files
│   ├── Nuke               # Foundry Nuke project files
│   ├── Premiere           # Adobe Premiere project files
│   └── Tracking           # Tracking data and project files
├── Renders
│   ├── AE                 # Renders from After Effects
│   └── Nuke               # Renders from Nuke
└── Video
    ├── Footage            # Raw or edited video footage
    ├── Guides             # Guide videos or reference edits
    └── XML-EDL-AAF        # Edit decision lists and interchange formats
```

---

# Sphere.json Structure Documentation

This document describes the folder structure and the purpose of each section in Sphere.json.

```
01_plates                # Raw or source plates for the project
02_support               # Support files (could include LUTs, reference, etc.)
03_references
│   ├── audio            # Reference audio files
│   ├── artwork          # Reference artwork
│   ├── style_guides     # Style guides for the project
│   └── client_brief     # Client brief documents or files
04_vfx
│   └── <shot_name>
│        ├── project     # VFX project files for the shot
│        └── render      # VFX renders for the shot
05_comp
│   └── <shot_name>
│        ├── project     # Compositing project files for the shot
│        └── render      # Compositing renders for the shot
06_mograph
│   └── render           # Motion graphics renders
07_shared
│   ├── fonts            # Shared fonts
│   ├── graphics         # Shared graphics
│   ├── stock_footage    # Shared stock footage
│   └── templates        # Shared templates
08_output
    └── render           # Final output renders
```
