#!/bin/bash
set -e

APP_NAME="Voxlay"
REPO="PawelKawka/Voxlay"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_NAME="voxlay.png"

if [ "$EUID" -eq 0 ]; then
  echo "Please run as a normal user, not root."
  exit 1
fi

mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

echo "Translator Installer"
echo "Fetching latest release..."

RELEASE_JSON=$(curl -s "https://api.github.com/repos/$REPO/releases/latest")
DOWNLOAD_URL=$(echo "$RELEASE_JSON" | grep -o 'https://github.com/[^"]*linux.zip' | head -n 1)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "Error: Could not find linux.zip in latest release."
    if [ -f "linux.zip" ]; then
        echo "Using local linux.zip"
        cp "linux.zip" "/tmp/translator_install.zip"
    else
        echo "Aborting."
        exit 1
    fi
else
    echo "Downloading from $DOWNLOAD_URL..."
    curl -L -s -o "/tmp/translator_install.zip" "$DOWNLOAD_URL"
fi

TMP_DIR="/tmp/translator_extract"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

echo "Extracting..."
unzip -q -o "/tmp/translator_install.zip" -d "$TMP_DIR"

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

echo "Installation complete!"
echo "You can run 'voxlay' from your terminal or launch it from the app menu"
echo "To uninstall run: voxlay remove"
