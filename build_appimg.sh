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

# 1. Проверка инструментов
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
        echo "Ошибка: $APPIMAGETOOL не найден. Скачайте его с GitHub AppImageKit."
        exit 1
    fi
fi

# 2. Подготовка и метаданные
uv sync || error_exit $?
uv run utils.py bumb || error_exit $?
VERSION=$(uv run utils.py get_version)
APPNAME=$(uv run utils.py get_name)
SAFE_NAME="${APPNAME// /_}"
ICONFILE="misc/icon.png"


# 3. Сборка Standalone через Nuitka
# Используем --standalone вместо --onefile для последующей упаковки
uv run nuitka \
    --standalone \
    --jobs="$(nproc)" \
    --assume-yes-for-downloads \
    --include-data-dir=frontend=frontend \
    --include-data-dir=vendor=vendor \
    --include-data-file=pyproject.toml=pyproject.toml \
    --include-data-file=.build_no=.build_no \
    --user-plugin=prepare_build.py \
    --enable-plugin=tk-inter \
    --output-dir=dist \
    main.py || error_exit $?

# 4. Формирование структуры AppDir
APPDIR="dist/${SAFE_NAME}.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

# Копируем результат Nuitka (папка main.dist) в AppDir
cp -r dist/main.dist/. "$APPDIR/usr/bin/"

# Создаем AppRun (точка входа)
cat <<EOF > "$APPDIR/AppRun"
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export PATH="\$HERE/usr/bin:\$PATH"
exec "\$HERE/usr/bin/main.bin" "\$@"
EOF
chmod +x "$APPDIR/AppRun"

# Создаем .desktop файл
cat <<EOF > "$APPDIR/${SAFE_NAME}.desktop"
[Desktop Entry]
Name=${APPNAME}
Exec=main
Icon=${SAFE_NAME}
Type=Application
Categories=Utility;
EOF

# Копируем иконку (AppImage ищет её в корне AppDir)
cp "$ICONFILE" "$APPDIR/${SAFE_NAME}.png"

# 5. Упаковка в AppImage
export ARCH=x86_64
$APPIMAGETOOL "$APPDIR" "dist/${APPNAME}_v${VERSION}.AppImage" || error_exit $?

echo "Build finished! File: dist/${APPNAME}_v${VERSION}.AppImage"
