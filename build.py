"""
Build script for Nihongo Quest - Windows 64-bit executable.

Usage:
    python build.py

Requirements:
    pip install pyinstaller

This will create a standalone .exe in the dist/ folder.
"""

import subprocess
import sys
import os
import shutil

def build():
    print("=" * 60)
    print("  Nihongo Quest - Windows Build Script")
    print("=" * 60)

    # Ensure we're in the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # Check for PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Check for Ursina
    try:
        import ursina
        print(f"[OK] Ursina found")
    except ImportError:
        print("[!] Ursina not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ursina"])

    # Clean previous builds
    for folder in ["build", "dist"]:
        path = os.path.join(project_dir, folder)
        if os.path.exists(path):
            print(f"[*] Cleaning {folder}/...")
            shutil.rmtree(path)

    spec_file = os.path.join(project_dir, "NihongoQuest.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    # Find ursina package location for data files
    ursina_path = os.path.dirname(ursina.__file__)
    panda3d_path = None
    try:
        import panda3d
        panda3d_path = os.path.dirname(panda3d.__file__)
    except ImportError:
        pass

    # Build PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NihongoQuest",
        "--onedir",
        "--windowed",
        "--noconfirm",
        # Collect ursina package data (models, shaders, textures, fonts)
        f"--collect-all=ursina",
        f"--collect-all=panda3d",
        # Hidden imports that PyInstaller might miss
        "--hidden-import=ursina",
        "--hidden-import=panda3d",
        "--hidden-import=panda3d.core",
        "--hidden-import=panda3d.direct",
        "--hidden-import=direct",
        "--hidden-import=direct.showbase",
        "--hidden-import=direct.showbase.ShowBase",
        "--hidden-import=direct.task",
        "--hidden-import=direct.interval",
        "--hidden-import=direct.gui",
        "--hidden-import=direct.filter",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        # Add our game packages
        "--add-data", f"core{os.pathsep}core",
        "--add-data", f"screens{os.pathsep}screens",
        "--add-data", f"minigames{os.pathsep}minigames",
        "--add-data", f"content{os.pathsep}content",
        "--add-data", f"entities{os.pathsep}entities",
        "--add-data", f"ui{os.pathsep}ui",
        "--add-data", f"config.py{os.pathsep}.",
    ]

    # Add assets directory if it exists and has files
    assets_dir = os.path.join(project_dir, "assets")
    if os.path.exists(assets_dir):
        cmd.extend(["--add-data", f"assets{os.pathsep}assets"])

    # Entry point
    cmd.append("main.py")

    print("\n[*] Building executable...")
    print(f"[*] Command: {' '.join(cmd)}\n")

    try:
        subprocess.check_call(cmd)
        print("\n" + "=" * 60)
        print("  BUILD SUCCESSFUL!")
        print("=" * 60)
        print(f"\n  Executable: dist/NihongoQuest/NihongoQuest.exe")
        print(f"  Folder size: {_get_dir_size('dist/NihongoQuest')}")
        print(f"\n  To run: double-click NihongoQuest.exe in the dist/NihongoQuest/ folder")
        print(f"  To distribute: zip the entire dist/NihongoQuest/ folder")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed with exit code {e.returncode}")
        print("Check the output above for errors.")
        sys.exit(1)


def _get_dir_size(path):
    """Get human-readable directory size."""
    total = 0
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
    if total > 1_000_000_000:
        return f"{total / 1_000_000_000:.1f} GB"
    elif total > 1_000_000:
        return f"{total / 1_000_000:.1f} MB"
    else:
        return f"{total / 1_000:.1f} KB"


if __name__ == "__main__":
    build()
