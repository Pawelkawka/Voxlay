#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "building"
rm -rf build dist
echo "starting build"

if [ -f "$HOME/venv/bin/python3" ]; then
    PYTHON_CMD="$HOME/venv/bin/python3"
    echo "using venv python: $PYTHON_CMD"
else
    PYTHON_CMD="python3"
    echo "using system python: $PYTHON_CMD"
fi

$PYTHON_CMD -m PyInstaller --noconfirm --onefile --windowed --name "Voxlay" \
    --icon "source/pythonicon.png" \
    --add-data "source/pythonicon.png:." \
    --hidden-import "pynput.keyboard._xorg" \
    --hidden-import "pynput.mouse._xorg" \
    --collect-all "ctranslate2" \
    --collect-all "speech_recognition" \
    --exclude-module "nvidia" \
    --exclude-module "triton" \
    --exclude-module "tkinter" \
    --exclude-module "matplotlib" \
    --exclude-module "scipy" \
    source/main.py

echo "build finished"
if [ -f "dist/Voxlay" ]; then
    echo "binary created at dist/Voxlay"
    
    echo "Creating linux.zip for release..."
    cp source/pythonicon.png dist/icon.png
    cd dist
    zip -r ../linux.zip Voxlay icon.png
    cd ..
    echo "success! linux.zip created"
else
    echo "error: binary not found"
    exit 1
fi
