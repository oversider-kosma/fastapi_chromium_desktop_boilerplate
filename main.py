import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import psutil
import requests

from config import (CHROMIUM_DIR, CHROMIUM_REPACKED_ZIP, CLEAR_OLD_VERSIONS,
                    DEFAULT_BG_COLOR, CHROMIUM_ADDITIONAL_LAUNCH_ARGS, VENDOR_DIR, WIN_HEIGHT,
                    WIN_WIDTH)
from server import run_server
from utils import clear_old_caches, decompress_zstd_archive, get_base_path, get_description, get_free_port, get_name, get_version, kill_proc_tree, print_current_dir, remove_nuitka_splash




def main():
    # some preparations
    base_path = get_base_path()

    # launch backend
    port = get_free_port()
    server_url = f"http://127.0.0.1:{port}"
    print(f"[*] Starting server on 127.0.0.1:{port}...")
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    
    # fetch chromium
    print(f"[*] Fetching client...")
    zip_file_name = base_path / VENDOR_DIR / CHROMIUM_REPACKED_ZIP
    target_dir = base_path / CHROMIUM_DIR
    decompress_zstd_archive(zip_file_name, base_path)
    print(f"[*] Cleint fetched into {target_dir}")
    

    # ensure server has started
    print("[*] Waiting for server readiness...")
    while True:
        try:
            response = requests.get(f"{server_url}/hello", timeout=1)
            if response.status_code == 200:
                print("[+] Server is ready!")
                break
        except requests.exceptions.RequestException as e:
            time.sleep(0.5)


    # starting client
    chrome_path = base_path / CHROMIUM_DIR / "chrome.exe"
    print(f"[*] Looking for chrome at: {chrome_path}")
    with tempfile.TemporaryDirectory() as tmp_data_dir:
        try:
            user_data_dir = Path(tmp_data_dir) / "Data"
            os.makedirs(user_data_dir, exist_ok=True)
            
            launch_cmd = [chrome_path, 
                        f"--app={server_url}", 
                        f'--user-data-dir={user_data_dir}',
                        f'--window-size={WIN_WIDTH},{WIN_HEIGHT}',
                        f'defaullt-background-color={DEFAULT_BG_COLOR}']
            launch_cmd.extend([f"--{arg}" for arg in CHROMIUM_ADDITIONAL_LAUNCH_ARGS])

            print('Launching chromium as: ', ' '.join(str(x) for x in launch_cmd))
            chrome_proc = subprocess.Popen(launch_cmd)
            print(f"[+] Chromium started with PID: {chrome_proc.pid}")
        except FileNotFoundError:
            print(f"Couldn't find unpacked chromium-bin")
            sys.exit(0)

        remove_nuitka_splash()


        # watching client
        print("[*] Monitoring Chromium, process")
        try:
            while True:
                # Check if front is alive
                if not hasattr(chrome_proc, "pid") or not psutil.pid_exists(chrome_proc.pid):
                    print("[!] Chromium closed. Shutting down...")
                    break
                
                # Check for zombi case
                if chrome_proc.poll() is not None:
                    print("[!] Chromium process terminated. Shutting down...")
                    break                
                time.sleep(0.5)
        
            # gracefull exit. Lets clean up.
            if CLEAR_OLD_VERSIONS:
                print("[!] Gracefull exit. Clearing old caches...")
                clear_old_caches()

        except KeyboardInterrupt:
            print("\n[!] Interrupted by user.")
            
        finally:
            if hasattr(chrome_proc, "pid"):
                kill_proc_tree(chrome_proc.pid)

            print("[*] Cleaning up and exiting...")
  
            server_thread.server.should_exit = True
            server_thread.join()

            sys.exit(0) 


if __name__ == "__main__":
    main()