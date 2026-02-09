from PyQt6 import QtWidgets, QtCore
from ..common_widgets import SettingCard, PrimaryPushButton, LineEdit, FluentIcon, InfoBar, InfoBarPosition
import requests
import logging

logger = logging.getLogger("GUI.ServerConfig")

class ServerConfigCard(SettingCard):
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
        QtWidgets.QApplication.processEvents()
        
        try:
            payload = {
                "q": "test",
                "source": "auto",
                "target": "en"
            }
            headers = {
                "Content-Type": "application/json"
            }
            logger.debug(f"Sending test request to: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=3)
            
            if response.status_code == 200:
                logger.info(f"Connection test successful! Server responded with status 200")
                self._show_message("Success", "Connection established successfully!", False)
            elif response.status_code == 400:
                base_url = self.urlEdit.text().strip()
                logger.debug(f"Status 400, trying base URL: {base_url}")
                response = requests.post(base_url, json=payload, headers=headers, timeout=3)
                if response.status_code == 200:
                    logger.info(f"Connection test successful with base URL! Status 200")
                    self._show_message("Success", "Connection established successfully!", False)
                    self.urlEdit.setText(base_url)
                    self.config["libretranslate_url"] = base_url
                else:
                    logger.error(f"Connection test failed! Server returned status {response.status_code}")
                    self._show_message("Failed", f"Invalid request format (400). Check server configuration.", True)
            else:
                logger.error(f"Connection test failed! Server returned status {response.status_code}")
                self._show_message("Failed", f"Server returned status: {response.status_code}", True)
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: Could not connect to server at {url}")
            self._show_message("Connection Error", "Could not connect to server. Is it running?", True)
        except requests.exceptions.Timeout:
            logger.error(f"Connection timeout: Server did not respond in time (3s timeout)")
            self._show_message("Timeout", "Server did not respond in time. Check if LibreTranslate is running.", True)
        except Exception as e:
            logger.error(f"Connection test exception: {str(e)}")
            self._show_message("Error", f"Connection failed: {str(e)}", True)
        finally:
            self.testBtn.setEnabled(True)
            self.testBtn.setText("Test Connection")

    def _show_message(self, title, content, is_error):
        if is_error:
            InfoBar.error(
                title=title,
                content=content,
                orient=QtCore.Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self.window()
            )
        else:
            InfoBar.success(
                title=title,
                content=content,
                orient=QtCore.Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self.window()
            )
            
    def setValue(self, value):
        self.urlEdit.setText(value)
