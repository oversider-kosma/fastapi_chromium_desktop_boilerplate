@echo off
echo Build started at %date% %time%
setlocal enabledelayedexpansion

chcp 65001
set LANG=en_US.UTF-8
set LC_ALL=C

set NUITKA_CACHE_DIR=.nuitka_cache

uv sync || goto :error
uv run utils.py bumb || goto :error

for /f "usebackq tokens=*" %%a in (`uv run utils.py get_version`) do set "VERSION=%%a"
for /f "usebackq tokens=*" %%a in (`uv run utils.py get_name`) do set "APPNAME=%%a"
for /f "usebackq tokens=*" %%a in (`uv run utils.py get_description`) do set "DESCRIPTION=%%a"

uv run nuitka ^
    --standalone ^
    --onefile ^
    --product-version=%VERSION% ^
    --file-version=%VERSION% ^
    --product-name="%APPNAME%" ^
    --file-description="%DESCRIPTION%" ^
    --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" ^
    --jobs=%NUMBER_OF_PROCESSORS% ^
    --assume-yes-for-downloads ^
    --include-data-dir=frontend=frontend ^
    --include-data-dir=vendor=vendor ^
    --include-data-file=pyproject.toml=pyproject.toml ^
    --include-data-file=.build_no=.build_no ^
    --windows-console-mode=attach ^
    --onefile-windows-splash-screen-image="misc/splashscreen.png" ^
    --windows-icon-from-ico=frontend/static/favicon.ico ^
    --user-plugin=prepare_build.py ^
    --output-dir=dist ^
    --output-filename="%APPNAME%_v%VERSION%.exe" ^
    main.py

if %errorlevel% neq 0 goto :error
echo Build finished at %date% %time%
exit /b 0

:error
echo Build FAILED at %date% %time% with error %errorlevel%
exit /b %errorlevel%
