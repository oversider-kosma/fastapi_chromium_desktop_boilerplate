@echo off
echo Build started at %date% %time%
chcp 437
set LANG=en_US.UTF-8
set LC_ALL=C

uv sync

uv run utils.py bumb

FOR /F "tokens=*" %%a IN ('uv run utils.py get_version') DO SET VERSION=%%a
FOR /F "tokens=*" %%a IN ('uv run utils.py get_name') DO SET APPNAME=%%a
FOR /F "tokens=*" %%a IN ('uv run utils.py get_description') DO SET DESCRIPTION=%%a


uv run nuitka ^
    --standalone ^
    --onefile ^
    --product-version=%VERSION% ^
    --file-version=%VERSION% ^
    --product-name=%APPNAME% ^
    --file-description="%DESCRIPTION%" ^
    --onefile-tempdir-spec="{CACHE_DIR}/{PRODUCT}/{VERSION}" ^
    --jobs=%NUMBER_OF_PROCESSORS%^
    --assume-yes-for-downloads ^
    --include-data-dir=frontend=frontend ^
    --include-data-dir=vendor=vendor ^
    --include-data-file=pyproject.toml=pyproject.toml ^
    --include-data-file=.build_no=.build_no ^
    --windows-console-mode=attach ^
    --onefile-windows-splash-screen-image="misc/splashscreen.png" ^
    --windows-icon-from-ico=frontend/static/favicon.ico ^
    --user-plugin=prepare_build.py ^
    --output-filename=%APPNAME%.exe ^
    main.py
echo Build finished at %date% %time%
