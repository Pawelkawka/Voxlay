import os
import sys
import requests
import logging
import threading
import subprocess
import shutil
import zipfile
from pathlib import Path
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMessageBox

REPO = "PawelKawka/Voxlay"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

logger = logging.getLogger("Updater")

class UpdateSignals(QtCore.QObject):
    update_available = QtCore.pyqtSignal(str, str)
    no_update_found = QtCore.pyqtSignal()
    update_error = QtCore.pyqtSignal(str)

class UpdateManager:
    def __init__(self, current_version):
        self.signals = UpdateSignals()
        self.current_version = current_version
        self.download_url = None
        self.latest_version = None
        self.last_status = "Ready"
        self.last_error = None

    def check_for_updates(self, silent=True):
        self.last_status = "Checking"
        threading.Thread(target=self._check_thread, args=(silent,), daemon=True).start()

    def _check_thread(self, silent):
        try:
            logger.info("Checking for updates...")
            response = requests.get(GITHUB_API_URL, timeout=5)
            if response.status_code != 200:
                err_msg = f"HTTP {response.status_code}"
                if response.status_code == 404:
                    err_msg = "Repository error: No releases found or repository is private (404)."
                
                logger.warning(f"Update check failed: {err_msg}")
                self.last_status = "Error"
                self.last_error = err_msg
                self.signals.update_error.emit(err_msg)
                return

            data = response.json()
            tag_name = data.get("tag_name", "").strip()
            
            if tag_name.startswith('v'):
                remote_ver = tag_name.lstrip('v')
            else:
                remote_ver = tag_name

            if remote_ver != self.current_version:
                logger.info(f"New version found: {remote_ver} (Current: {self.current_version})")
                self.latest_version = tag_name
                self.last_status = "Available"
                
                assets = data.get("assets", [])
                self.download_url = next((a.get("browser_download_url") for a in assets if "linux.zip" in a.get("name", "").lower()), None)
                
                if self.download_url:
                    self.signals.update_available.emit(self.latest_version, self.download_url)
            else:
                logger.info("No updates available.")
                self.last_status = "NoUpdate"
                self.signals.no_update_found.emit()
                    
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Error checking updates: {err_msg}")
            self.last_status = "Error"
            self.last_error = err_msg
            self.signals.update_error.emit(err_msg)

    def perform_update(self, download_url):
        threading.Thread(target=self._download_and_install, args=(download_url,), daemon=True).start()

    def _download_and_install(self, url):
        try:
            if getattr(sys, 'frozen', False):
                binary_path = Path(sys.executable)
                app_dir = binary_path.parent
            else:
                logger.warning("Running from source, update simulation only.")
                app_dir = Path.cwd()
                binary_path = app_dir / "Voxlay" 

            zip_path = app_dir / "update.zip"
            extract_dir = app_dir / "update_extract"
            if extract_dir.exists(): shutil.rmtree(extract_dir)
            extract_dir.mkdir()

            logger.info(f"Downloading update from {url}...")
            r = requests.get(url, stream=True)
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info("Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            new_binary = next(extract_dir.rglob("Voxlay"), None)
            if not new_binary:
                logger.error("New binary not found in update.")
                return

            logger.info("Replacing binary...")
            backup_path = binary_path.with_suffix(".old")
            
            if backup_path.exists():
                backup_path.unlink()
                
            if binary_path.exists():
                binary_path.rename(backup_path)
            
            shutil.move(str(new_binary), str(binary_path))
            binary_path.chmod(0o755)

            zip_path.unlink()
            shutil.rmtree(extract_dir)
            
            logger.info("Update successful. Restarting...")
            self._restart_app(binary_path)

        except Exception as e:
            logger.error(f"Update failed: {e}")
            if 'backup_path' in locals() and backup_path.exists() and not binary_path.exists():
                backup_path.rename(binary_path)

    def _restart_app(self, binary_path):
        os.execv(str(binary_path), [str(binary_path)] + sys.argv[1:])
