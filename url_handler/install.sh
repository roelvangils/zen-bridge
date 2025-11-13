#!/bin/bash
#
# Inspekt URL Handler Installation Script
#
# This script installs the inspekt:// URL scheme handler on macOS.
# It creates an app bundle in /Applications and registers it with LaunchServices.
#
# Usage:
#   ./install.sh          # Install
#   ./install.sh remove   # Uninstall
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="/Applications/Inspekt.app"
HANDLER_SCRIPT="$SCRIPT_DIR/inspekt_url_handler.py"

echo "╔════════════════════════════════════════╗"
echo "║  Inspekt URL Handler Installation     ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if running uninstall
if [ "$1" = "remove" ] || [ "$1" = "uninstall" ]; then
    echo "🗑️  Uninstalling Inspekt URL handler..."

    if [ -d "$APP_DIR" ]; then
        sudo rm -rf "$APP_DIR"
        echo "✓ Removed $APP_DIR"
    else
        echo "⚠️  App bundle not found at $APP_DIR"
    fi

    echo ""
    echo "✓ Uninstallation complete!"
    echo ""
    echo "Note: You may need to restart your browser for changes to take effect."
    exit 0
fi

# Check if handler script exists
if [ ! -f "$HANDLER_SCRIPT" ]; then
    echo "❌ Error: Handler script not found at $HANDLER_SCRIPT"
    exit 1
fi

echo "📋 Installation steps:"
echo "  1. Create app bundle structure"
echo "  2. Copy handler script"
echo "  3. Create Info.plist"
echo "  4. Register inspekt:// protocol"
echo ""

# Create app bundle structure
echo "📁 Creating app bundle..."
sudo mkdir -p "$APP_DIR/Contents/MacOS"
sudo mkdir -p "$APP_DIR/Contents/Resources"

# Copy handler script
echo "📄 Copying handler script..."
sudo cp "$HANDLER_SCRIPT" "$APP_DIR/Contents/Resources/"
sudo chmod +x "$APP_DIR/Contents/Resources/inspekt_url_handler.py"

# Create launcher script
echo "🚀 Creating launcher..."
sudo tee "$APP_DIR/Contents/MacOS/Inspekt" > /dev/null <<'EOF'
#!/bin/bash
# Inspekt URL Handler Launcher

# Get the URL passed by macOS
URL="$1"

# Get the script directory
SCRIPT_DIR="$(dirname "$0")/../Resources"

# Call the Python handler script
exec "$SCRIPT_DIR/inspekt_url_handler.py" "$URL"
EOF

sudo chmod +x "$APP_DIR/Contents/MacOS/Inspekt"

# Create Info.plist
echo "⚙️  Creating Info.plist..."
sudo tee "$APP_DIR/Contents/Info.plist" > /dev/null <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Inspekt</string>
    <key>CFBundleDisplayName</key>
    <string>Inspekt URL Handler</string>
    <key>CFBundleIdentifier</key>
    <string>com.roelvangils.inspekt</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>Inspekt</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>LSBackgroundOnly</key>
    <true/>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>Inspekt URL</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>inspekt</string>
            </array>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
        </dict>
    </array>
</dict>
</plist>
EOF

# Register with LaunchServices
echo "🔗 Registering protocol with macOS..."
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP_DIR"

# Wait a moment for registration
sleep 1

# Verify registration
echo ""
echo "🔍 Verifying installation..."
if /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -dump | grep -q "inspekt:"; then
    echo "✓ Protocol registered successfully!"
else
    echo "⚠️  Warning: Protocol registration could not be verified"
    echo "   This may work anyway - try testing it"
fi

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  ✓ Installation Complete!             ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "📚 Usage:"
echo "  • Click inspekt:// links from any app"
echo "  • Terminal: open \"inspekt://info\""
echo "  • Shortcuts: Add 'Open URL' action"
echo ""
echo "🧪 Test it:"
echo "  open \"inspekt://info\""
echo ""
echo "📖 Documentation:"
echo "  $SCRIPT_DIR/../docs/url-scheme.md"
echo ""
echo "🌐 Example links:"
echo "  file://$SCRIPT_DIR/test_links.html"
echo ""
echo "💡 Tip: Make sure the bridge server is running:"
echo "  inspekt server status"
echo "  inspekt api start -d"
echo ""
