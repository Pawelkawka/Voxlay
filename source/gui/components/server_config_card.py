from PyQt6 import QtWidgets, QtCore
from ..common_widgets import SettingCard, PrimaryPushButton, LineEdit, FluentIcon, InfoBar, InfoBarPosition
import requests
import logging
import threading

logger = logging.getLogger("GUI.ServerConfig")

class ServerConfigCard(SettingCard):
    test_finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, config, save_func=None, parent=None):
        super().__init__(FluentIcon.LINK, "LibreTranslate Server", "Configure local translation server URL", parent)
        self.config = config
        self.save_func = save_func
        logger.info("Initializing ServerConfigCard")
        
        self.urlEdit = LineEdit(self)
        self.urlEdit.setPlaceholderText("http://localhost:5000/translate")
        self.urlEdit.setText(self.config.get("libretranslate_url", "http://localhost:5000/translate"))
        self.urlEdit.setFixedWidth(300)
        self.urlEdit.textChanged.connect(self._on_url_changed)
        
        self.testBtn = PrimaryPushButton("Test Connection", self)
        self.testBtn.setFixedWidth(140)
        self.testBtn.clicked.connect(self._test_connection)
        
        self.hBoxLayout.addWidget(self.urlEdit, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.testBtn, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def _on_url_changed(self, text):
        old_url = self.config.get("libretranslate_url", "http://localhost:5000/translate")
        new_url = text.strip()
        logger.info(f"LibreTranslate URL changed from '{old_url}' to '{new_url}'")
        self.config["libretranslate_url"] = new_url
        if self.save_func:
            self.save_func()

    def _test_connection(self):
        url = self.urlEdit.text().strip()
        logger.info(f"Testing connection to LibreTranslate server: {url}")
        if not url:
            logger.warning("Connection test failed: URL is empty")
            self._show_message("Error", "URL cannot be empty", True)
            return
        
        if not url.endswith('/translate'):
            url = url.rstrip('/') + '/translate'
            
        self.testBtn.setEnabled(False)
        self.testBtn.setText("Testing...")
        self.test_finished.connect(self._on_test_finished, QtCore.Qt.ConnectionType.UniqueConnection)
        
        def run_test():
            try:
                from core.constants import DEFAULT_SOURCE_LANGUAGE, DEFAULT_TARGET_LANGUAGE, TARGET_LANGUAGES
                
                src_full = self.config.get("source_language", DEFAULT_SOURCE_LANGUAGE)
                src = src_full.split("-")[0].lower()
                tgt = self.config.get("target_language", DEFAULT_TARGET_LANGUAGE).lower()
                test_src, test_tgt = src, tgt
                
                if test_src == test_tgt:
                    available = list(TARGET_LANGUAGES.keys())
                    if len(available) >= 2:
                        test_src, test_tgt = available[0], available[1]
                    else:
                        test_src, test_tgt = "en", "pl"

                payload = {
                    "q": "Test",
                    "source": test_src,
                    "target": test_tgt,
                    "format": "text"
                }
                headers = {
                    "Content-Type": "application/json"
                }
                logger.debug(f"Sending test request to: {url} using {test_src}->{test_tgt}")
                
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"Connection test successful! Server responded with status 200")
                        self.test_finished.emit(True, "Connection established successfully!")
                        return
                except Exception:
                    pass

                base_url = url.replace('/translate', '')
                if not base_url: base_url = url
                
                logger.debug(f"Translate failed, trying /languages at: {base_url}/languages")
                try:
                    resp_langs = requests.get(f"{base_url.rstrip('/')}/languages", timeout=3)
                    if resp_langs.status_code == 200:
                        logger.info(f"Connection test successful via /languages!")
                        self.test_finished.emit(True, "Server is alive (detected via /languages).")
                        return
                except Exception:
                    pass

                self.test_finished.emit(False, "Could not connect to server. Check URL and Docker status.")

            except Exception as e:
                logger.error(f"Connection test error: {str(e)}")
                self.test_finished.emit(False, f"Error: {str(e)}")

        threading.Thread(target=run_test, daemon=True).start()

    @QtCore.pyqtSlot(bool, str)
    def _on_test_finished(self, success, message):
        try:
            self.test_finished.disconnect(self._on_test_finished)
        except Exception:
            pass
        
        self.testBtn.setText("Wait...")
        self._show_message("Success" if success else "Failed", message, not success)
        
        QtCore.QTimer.singleShot(2000, self._enable_test_button)

    def _enable_test_button(self):
        self.testBtn.setEnabled(True)
        self.testBtn.setText("Test Connection")

    def _show_message(self, title, content, is_error):
        parent_widget = self.window() or self
        
        if is_error:
            InfoBar.error(
                title=title,
                content=content,
                orient=QtCore.Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500,
                parent=parent_widget
            )
        else:
            InfoBar.success(
                title=title,
                content=content,
                orient=QtCore.Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3500,
                parent=parent_widget
            )
            
    def setValue(self, value):
        self.urlEdit.setText(value)
