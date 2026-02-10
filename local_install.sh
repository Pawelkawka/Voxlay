#!/bin/bash
set -e

APP_NAME="Voxlay"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_NAME="voxlay.png"
LOCAL_ZIP="linux.zip"

if [ "$EUID" -eq 0 ]; then
  echo "Please run as a normal user, not root."
  exit 1
fi

if ! command -v unzip &> /dev/null; then
    echo "Error: 'unzip' is required but not installed. Please install 'unzip' and try again."
    exit 1
fi

if [ ! -f "$LOCAL_ZIP" ]; then
    echo "Error: $LOCAL_ZIP not found in current directory."
    echo "Please ensure you have built the project or placed linux.zip here."
    exit 1
fi

mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

echo "Offline Installer"
echo "Using local $LOCAL_ZIP..."

TMP_DIR="/tmp/translator_extract"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

echo "Extracting..."
unzip -q -o "$LOCAL_ZIP" -d "$TMP_DIR"

BINARY_PATH=$(find "$TMP_DIR" -type f -name "Voxlay" | head -n 1)
ICON_PATH=$(find "$TMP_DIR" -type f -name "icon.png" | head -n 1)

if [ -z "$BINARY_PATH" ]; then
    echo "Error: 'Voxlay' binary not found in zip."
    exit 1
fi

echo "Installing to $INSTALL_DIR..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

cp "$BINARY_PATH" "$INSTALL_DIR/Voxlay"
chmod +x "$INSTALL_DIR/Voxlay"

if [ -n "$ICON_PATH" ]; then
    cp "$ICON_PATH" "$INSTALL_DIR/icon.png"
    echo "Icon installed."
    INSTALLED_ICON="$INSTALL_DIR/icon.png"
else
    INSTALLED_ICON="utilities-terminal"
fi

WRAPPER="$BIN_DIR/voxlay"
echo "Creating wrapper script at $WRAPPER..."

cat > "$WRAPPER" <<EOF
#!/bin/bash
INSTALL_DIR="$INSTALL_DIR"
BINARY="\$INSTALL_DIR/Voxlay"

if [ "\$1" == "remove" ]; then
    echo "Uninstalling Voxlay..."
    rm -rf "\$INSTALL_DIR"
    rm -f "\$0"
    rm -f "$DESKTOP_DIR/voxlay.desktop"
    
    touch "$DESKTOP_DIR"
    if command -v update-desktop-database &> /dev/null; then
         update-desktop-database "$DESKTOP_DIR" &> /dev/null || true
    fi
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/" &> /dev/null || true
    fi
    if command -v kbuildsycoca6 &> /dev/null; then
        kbuildsycoca6 &> /dev/null || true
    elif command -v kbuildsycoca5 &> /dev/null; then
        kbuildsycoca5 &> /dev/null || true
    fi

    echo "Voxlay has been removed."
    exit 0
fi

if [ ! -f "\$BINARY" ]; then
    echo "Error: Voxlay binary not found at \$BINARY"
    exit 1
fi

"\$BINARY" "\$@"
EOF

chmod +x "$WRAPPER"

DESKTOP_FILE="$DESKTOP_DIR/voxlay.desktop"
echo "Creating desktop entry..."

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Voxlay
Comment=Speech Translator Overlay
Exec=$WRAPPER
Icon=$INSTALLED_ICON
Type=Application
Categories=Utility;
Terminal=false
StartupWMClass=Voxlay
EOF

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" &> /dev/null || true
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/" &> /dev/null || true
fi
if command -v kbuildsycoca6 &> /dev/null; then
    kbuildsycoca6 &> /dev/null || true
elif command -v kbuildsycoca5 &> /dev/null; then
    kbuildsycoca5 &> /dev/null || true
fi

echo "Installation complete!"
echo "You can run 'voxlay' from your terminal or launch it from the app menu"
echo "To uninstall run: voxlay remove"
