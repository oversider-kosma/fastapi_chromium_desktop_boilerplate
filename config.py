from build_asset import BuildAsset

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
CHROMIUM_REPACKED_ZIP = "ungoogled-chromium.tar.xz"



# Have to use a binary unarchiver because at the moment the BCJ2 filter is not supported by py7zr.
# And it seems that the 7z archive provided by portapps contains exactly this type of compression.
ASSETS ={
    'Windows': {
        '7zip': BuildAsset(
            url="https://github.com/ip7z/7zip/releases/download/26.00/7zr.exe",
            sha_256="4bec0bc59836a890a11568b58bd12a3e7b23a683557340562da211b6088058ba"),

        "chromium": BuildAsset(
            url="https://github.com/portapps/ungoogled-chromium-portable/releases/download/140.0.7339.137-21/ungoogled-chromium-win64.7z",
            sha_256="85080bf51f51ac5655125b42cf2e0e50ba11a929ca763044ec7f54ec45da49ef")
    },
    'Linux': {
        # Sience linux version is shipped whithin tar.xz we no need for 7zip here
        "chromium": BuildAsset(
            url="https://github.com/ungoogled-software/ungoogled-chromium-portablelinux/releases/download/146.0.7680.71-1/ungoogled-chromium-146.0.7680.71-1-x86_64_linux.tar.xz",
            sha_256="5ad13b142b6de1656382a47f8526e14869770275ed4202b57c66d01f936e5b4b")
    },
}


# Specifies the name of the file that stores the incremental build number,
# which is appended as the last digit of the application version.
# This version is used in the folder name where the one-file image extracts itself.
# This allows the one-file image to cache its contents for subsequent runs
# while avoiding version conflict bugs.
BUILD_NO_FILE = ".build_no"

# Clear dirs with old unpacked versions of onefile
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
    'disk-cache-size=1',
    'enable-early-process-singleton',
    'in-process-gpu',
    'instant-process'
    'media-cache-size=1',
    'no-crash-upload',
    'no-default-browser-check',
    'no-first-run',
]
