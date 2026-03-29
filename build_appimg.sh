#!/bin/bash

error_exit() {
    echo "Build FAILED at $(LC_ALL=C date) with code $1"
    exit "$1"
}


echo "Build started at $(LC_ALL=C date)"

export LANG=en_US.UTF-8
export NUITKA_CACHE_DIR=.nuitka_cache


if ! ldconfig -p | grep -q "libfuse.so.2"; then
    echo "Warning: libfuse2 is not installed. "
    echo "Please install libfuse2 using your package manager (apt, dnf, pacman, etc.)"
    exit 1
fi

if ! command -v gcc &> /dev/null; then
    echo "Error: gcc not found. Please install build-essential or equivalent."
    exit 1
fi

if ! command -v ccache &> /dev/null; then
    echo "Note: install 'ccache' to speed up subsequent Nuitka builds."
fi

# 1. Tools check
APPIMAGETOOL="./appimagetool-x86_64.AppImage"
APPIMAGE_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "No AppImageTool found."
    if command -v curl &> /dev/null; then
        echo "Downloading AppImageTool..."
        curl -L -O --retry 5 --retry-delay 2 --retry-connrefused $APPIMAGE_URL
        chmod +x "$APPIMAGETOOL"
    fi
    if [ ! -f "$APPIMAGETOOL" ]; then
        echo "Error: $APPIMAGETOOL not found. Download it from GitHub AppImageKit."
        exit 1
    fi
fi

# 2. Preparation and metadata
uv sync || error_exit $?
uv run ./app/utils.py bumb || error_exit $?
VERSION=$(uv run ./app/utils.py get_version)
APPNAME=$(uv run ./app/utils.py get_name)
SAFE_NAME="${APPNAME// /_}"
ICONFILE="./resources/icon.png"
cp "./resources/favicon" "./app/frontend/static" favicon.ico > /dev/null 2>&1
cp "./LICENSE" "./app/" > /dev/null 2>&1
uv run prepare_build.py build_info_toml


# 3. Standalone build via Nuitka
# Use --standalone instead of --onefile for subsequent packaging
uv run nuitka \
    --standalone \
    --jobs="$(nproc)" \
    --assume-yes-for-downloads \
    --include-data-dir=./app/frontend=frontend \
    --include-data-dir=./app/vendor=vendor \
    --include-data-file=./app/info.toml=info.toml \
    --include-data-file=./app/.build_no=.build_no \
    --include-data-file=./app/LICENSE=LICENSE \
    --user-plugin=prepare_build.py \
    --enable-plugin=tk-inter \
    --output-dir=dist \
    ./app/main.py || error_exit $?


# 4. AppDir structure formation
APPDIR="dist/${SAFE_NAME}.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

# Copy Nuitka output (main.dist folder) to AppDir
cp -r dist/main.dist/. "$APPDIR/usr/bin/"

# Create AppRun (entry point)
# Note: EOF1 is quoted ('EOF1') so that $HERE, $0, $@ are NOT expanded here —
# they must expand at AppRun runtime inside the AppImage environment.
cat <<'EOF1' > "$APPDIR/AppRun"
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/main.bin" "$@"
EOF1

chmod +x "$APPDIR/AppRun"

# Create .desktop file
# EOF2 is unquoted so that ${APPNAME} and ${SAFE_NAME} expand from the current shell.
cat <<EOF2 > "$APPDIR/${SAFE_NAME}.desktop"
[Desktop Entry]
Name=${APPNAME}
Exec=main
Icon=${SAFE_NAME}
Type=Application
Categories=Utility;
EOF2

# Copy icon (AppImage looks for it in the AppDir root)
cp "$ICONFILE" "$APPDIR/${SAFE_NAME}.png"


# 5. Packaging into AppImage
export ARCH=x86_64
$APPIMAGETOOL "$APPDIR" "dist/${APPNAME}_v${VERSION}.AppImage" || error_exit $?

rm app/info.toml
rm app/LICENSE

echo "Build finished! File: dist/${APPNAME}_v${VERSION}.AppImage"
