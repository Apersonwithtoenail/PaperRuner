#!/bin/bash
set -e
echo "PaperRuner installer"
echo "=================="

if [ ! -f /etc/debian_version ]; then
    echo "Only Debian / Ubuntu / Kali supported for auto-install."
    exit 1
fi

echo "-> Installing dependencies..."
sudo apt update
sudo apt install -y mpv ffmpeg python3-gi python3-gi-cairo \
                    python3-pil libx11-dev libxext-dev libxrender-dev \
                    git build-essential x11-utils

echo "-> Installing xwinwrap..."
if ! command -v xwinwrap >/dev/null; then
    TMP=$(mktemp -d)
    cd "$TMP"
    git clone https://github.com/mmbrown/xwinwrap.git
    cd xwinwrap
    make
    sudo cp xwinwrap /usr/local/bin/
    cd ~
    rm -rf "$TMP"
fi

echo "-> Copying files..."
INSTALL_DIR="$HOME/.local/share/paperruner"
mkdir -p "$INSTALL_DIR"
cp paperruner-app.py paperruner-engine.sh "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/paperruner-app.py" "$INSTALL_DIR/paperruner-engine.sh"

echo "-> Creating launcher..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/paperruner" << 'WRAP'
#!/bin/bash
exec python3 "$HOME/.local/share/paperruner/paperruner-app.py" "$@"
WRAP
chmod +x "$HOME/.local/bin/paperruner"

mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/paperruner.desktop" << 'DESK'
[Desktop Entry]
Type=Application
Name=PaperRuner
Comment=Lightweight live wallpaper manager
Exec=/home/kavish/.local/bin/paperruner
Icon=preferences-desktop-wallpaper
Terminal=false
Categories=Graphics;Utility;
DESK
update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true

echo ""
echo "Installed! Run: paperruner"
echo "Add wallpapers to: ~/Videos/PaperRunerpapers/"
