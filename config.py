# directory to store downloaded 7z and chromium. 
# Gitignored. Needed only for build.
BUILD_ASSETS_DIR = "build_assets" 

# directory containing repacked chromium. Included in Nuitka build.
VENDOR_DIR = "vendor" 

# directory where chromium will be unpacked at runtime
CHROMIUM_DIR = "chromium-bin" 

# NB: We repack chromium while building the application image mainly for two reasons: 
# 1. zstd can be unpacked faster than lzma thanks to multithreading 
# 2. we don't need to bring the 7zip binary into the built image (see below for why it's needed).

SEVENZIP_EXE = "7zr.exe"
CHROMIUM_REPACKED_ZIP = "ungoogled-chromium-win64.zip"
CHROMIUM_ORIG_7Z = "ungoogled-chromium-win64.7z"

ASSETS = {
    # Have to use a binary unarchiver because at the moment the BCJ2 filter is not supported by py7zr.
    # And it seems that the 7z archive provided by portapps contains exactly this type of compression.
    SEVENZIP_EXE:
            "https://github.com/ip7z/7zip/releases/download/26.00/7zr.exe",
    
    CHROMIUM_ORIG_7Z:
            "https://github.com/portapps/ungoogled-chromium-portable/releases/download/140.0.7339.137-21/ungoogled-chromium-win64.7z",
    
}


# Specifies the name of the file that stores the incremental build number, 
# which is appended as the last digit of the application version. 
# This version is used in the folder name where the one-file image extracts itself. 
# This allows the one-file image to cache its contents for subsequent runs 
# while avoiding version conflict bugs.
BUILD_NO_FILE = ".build_no" 


CLEAR_OLD_VERSIONS = True

WIN_WIDTH = 1300
WIN_HEIGHT = 700
DEFAULT_BG_COLOR='ff77889'

CHROMIUM_ADDITIONAL_LAUNCH_ARGS = [
    'new-window',
    'incognito',
    'minimal',
    'hide-scrollbars',
    'bwsi',
    'disable-breakpad',
    'disable-breakpad',
    'disable-crush-reporter',
    'disable-default-apps', 
    'disable-demo-mode',
    'disable-dev-tools'
    'disable-encryption-win',
    'disable-extensions',
    'disable-local-storage',
    'disable-logging', 
    'disable-machine-id ',
    'disable-notifications',
    'disable-speech-api', 
    'disable-touch-drag-drop',
    'disable-translate',
    'disk-cache-size=1'
    'enable-early-process-singleton',
    'in-process-gpu',
    'instant-process'
    'media-cache-size=1',
    'no-crash-upload', 
    'no-default-browser-check', 
    'no-first-run', 
]
