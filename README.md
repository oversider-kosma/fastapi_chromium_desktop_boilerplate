# Boilerplate for desktop app with FastAPI as a backend and Ungoogled Chromium as a frontend

The `backend` and `frontend` folders are self-explanatory.

The project is compiled into a single executable file (`.exe` for Windows, `.AppImage` for Linux) using [`Nuitka`](https://github.com/Nuitka/Nuitka).
Chromium binaries will be downloaded and integrated into the image during the build process and is not required to be present on the target system.

## Build
### Windows:
Prerequisites:
* [`uv`](https://github.com/astral-sh/uv)
* `ccache` (optional, but speeds up subsequent builds. Use `winget install ccache`)

Run the following in the project directory:
```bash
uv sync
build.bat
```

### Linux:
Prerequisites:
* [`uv`](https://github.com/astral-sh/uv)
* libfuse2
* gcc (maybe Nuitka might handle it without `gcc` using `zig`, needs experimentation)
* ccache (optional, but speeds up subsequent builds)

Run the following in the project directory:
```bash
uv sync
./build_appimg.sh
```

Everything else required, including Ungoogled Chromium, appimagetool, etc., will be downloaded automatically during the build process. The build result will be inside the `dist` directory.


## Running backend independently for dev/debug purpose:
```bash
uv run server.py --port 8080
```


## Plans/TODO/Future:
* possibly none (most likely)
* _maybe_: some js <-> python interaction similar to how it's done in eel
* _maybe_: even some [pyscript](https://pyscript.net/) for DOM manipulation without direct JS interaction.
