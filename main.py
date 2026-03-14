import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import suppress
from pathlib import Path
from typing import List, Optional

import psutil
import requests

from config import (CHROMIUM_ADDITIONAL_LAUNCH_ARGS, CHROMIUM_DIR,
                    CLEAR_OLD_VERSIONS, DEFAULT_BG_COLOR, WIN_HEIGHT,
                    WIN_WIDTH)
from server import run_server
from utils import (clear_old_caches, fetch_chromium, get_base_path,
                   get_free_port, kill_proc_tree, remove_nuitka_splash,
                   wipe_dir)


def main() -> None:
    # 1. Background Tasks: Cleanup and Fetching
    if CLEAR_OLD_VERSIONS:
        print("[*] Starting background cache cleanup...")
        cleanup_thread = threading.Thread(target=clear_old_caches, daemon=True)
        cleanup_thread.start()

    # Fetching browser
    print("[*] Fetching client in background...")
    chromium_tmp_dir = tempfile.TemporaryDirectory()
    fetching_thread = threading.Thread(target=fetch_chromium, args=(chromium_tmp_dir.name,), daemon=True)
    setattr(fetching_thread, 'chromium_fetched', False)
    fetching_thread.start()

    # 3. Launch backend
    port: int = get_free_port()
    server_url: str = f"http://127.0.0.1:{port}"
    print(f"[*] Starting server on 127.0.0.1:{port}...")

    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    # 4. Readiness check
    print("[*] Waiting for server and client readiness...")
    server_ready: bool = False
    start_time: float = time.time()
    timeout: int = 60

    while True:
        if not server_ready:
            with suppress(requests.exceptions.RequestException):
                response = requests.get(f"{server_url}/hello", timeout=1)
                if response.status_code == 200:
                    print("[+] Server is ready!")
                    server_ready = True

        # Check if chromium is fetched (attribute updated from inside fetch_chromium thread)
        if server_ready and getattr(fetching_thread, 'chromium_fetched', False):
            break

        if time.time() - start_time > timeout:
            print("[!] Timeout waiting for resources. Exiting...")
            sys.exit(1)

        time.sleep(0.5)

    # 5. Launch chromium
    chromium_exe = "chrome.exe" if platform.system() == "Windows" else "chrome"
    chrome_path: Path = Path(chromium_tmp_dir.name) / CHROMIUM_DIR / chromium_exe
    print(f"[*] Looking for chrome at: {chrome_path}")

    chrome_proc: Optional[subprocess.Popen] = None


    try:
        user_data_dir: Path = Path(chromium_tmp_dir.name) / "Data"
        os.makedirs(user_data_dir, exist_ok=True)

        launch_cmd: List[str] = [
            str(chrome_path),
            f"--app={server_url}",
            f'--user-data-dir={user_data_dir}',
            f'--window-size={WIN_WIDTH},{WIN_HEIGHT}',
            f'--default-background-color={DEFAULT_BG_COLOR}'
        ]
        launch_cmd.extend([f"--{arg}" for arg in CHROMIUM_ADDITIONAL_LAUNCH_ARGS])

        print('Launching chromium as:', ' '.join(launch_cmd))
        chrome_proc = subprocess.Popen(launch_cmd)
        print(f"[+] Chromium started with PID: {chrome_proc.pid}")
    except FileNotFoundError:
        print(f"[!] Error: Couldn't find unpacked chromium-bin at {chrome_path}")
        sys.exit(1)

    remove_nuitka_splash()

    # 6. Monitor Loop
    print("[*] Monitoring Chromium process...")
    try:
        while chrome_proc:
            if not psutil.pid_exists(chrome_proc.pid) or chrome_proc.poll() is not None:
                print("[!] Chromium closed. Shutting down...")
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")

    finally:
        if chrome_proc and psutil.pid_exists(chrome_proc.pid):
            kill_proc_tree(chrome_proc.pid)

        print("[*] Cleaning up and exiting...")
        with suppress(Exception):
            wipe_dir(chromium_tmp_dir.name)
        chromium_tmp_dir.cleanup()

        if hasattr(server_thread, 'server'):
            server = getattr(server_thread, "server")
            server.should_exit = True

        server_thread.join(timeout=2)
        sys.exit(0)


if __name__ == "__main__":
    main()
