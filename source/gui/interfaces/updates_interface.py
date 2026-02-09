from PyQt6 import QtWidgets, QtCore
from ..common_widgets import ScrollArea, SettingCardGroup, PushSettingCard, BodyLabel, TitleLabel
import logging

logger = logging.getLogger("GUI.Updates")

class UpdatesInterface(ScrollArea):
    def __init__(self, parent=None, tray_app=None, app_version="unknown"):
        super().__init__(parent)
        self.tray_app = tray_app
        self.app_version = app_version
        
        self.view = QtWidgets.QWidget()
        self.vBoxLayout = QtWidgets.QVBoxLayout(self.view)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)
        self.setWidget(self.view)
        
        self._init_ui()

    def _init_ui(self):
        
        self.vBoxLayout.addWidget(TitleLabel("Version Information"))
        version_group = SettingCardGroup("")
        self.vBoxLayout.addWidget(version_group)
        
        self.current_ver_label = BodyLabel(f"Current Version: {self.app_version}")
        version_group.viewLayout.addWidget(self.current_ver_label)
        
        self.vBoxLayout.addWidget(TitleLabel("Check for Updates"))
        update_group = SettingCardGroup("")
        self.vBoxLayout.addWidget(update_group)
        
        self.check_btn_card = PushSettingCard(
            "Check Now", None, "Check for Updates", 
            "Manually check if a newer version is available on GitHub."
        )
        self.check_btn_card.clicked.connect(self.check_for_updates)
        update_group.addSettingCard(self.check_btn_card)
        
        self.status_label = BodyLabel("Ready")
        self.vBoxLayout.addWidget(self.status_label)
        
        self.update_btn_card = PushSettingCard(
            "Install Update", None, "New Version Available", 
            "A newer version is available. Click to download and install."
        )
        self.update_btn_card.setVisible(False)
        self.update_btn_card.clicked.connect(self.start_update)
        self.vBoxLayout.addWidget(self.update_btn_card)
        
        self.vBoxLayout.addStretch(1)

        if self.tray_app and hasattr(self.tray_app, 'update_manager'):
            manager = self.tray_app.update_manager
            manager.signals.update_available.connect(self.on_update_available)
            manager.signals.no_update_found.connect(self.on_no_update_found)
            manager.signals.update_error.connect(self.on_update_error)
            
            if manager.last_status == "Checking":
                self.status_label.setText("Checking for updates...")
                self.check_btn_card.button.setEnabled(False)
            elif manager.last_status == "Available":
                self._handle_update_found(manager.latest_version, manager.download_url)
            elif manager.last_status == "NoUpdate":
                self._handle_no_update()
            elif manager.last_status == "Error":
                self._handle_update_error(manager.last_error)

    def check_for_updates(self):
        self.status_label.setText("Checking for updates...")
        self.check_btn_card.button.setEnabled(False)
        
        if self.tray_app and hasattr(self.tray_app, 'update_manager'):
            self.tray_app.update_manager.check_for_updates(silent=False)
        else:
            self.status_label.setText("Update manager not initialized.")
            self.check_btn_card.button.setEnabled(True)

    def on_update_available(self, version, url):
        self._handle_update_found(version, url)

    def on_no_update_found(self):
        self._handle_no_update()

    def _handle_no_update(self):
        self.status_label.setText("You are using the latest version.")
        self.check_btn_card.button.setEnabled(True)

    def on_update_error(self, error_msg):
        self._handle_update_error(error_msg)

    def _handle_update_error(self, error_msg):
        self.status_label.setText(f"Error checking for updates: {error_msg}")
        self.check_btn_card.button.setEnabled(True)

    def _handle_update_found(self, version, url):
        self.status_label.setText(f"Update found! Newest version: {version}")
        self.update_btn_card.setContent(f"Version {version} is ready for installation.")
        self.update_btn_card.setVisible(True)
        self.check_btn_card.button.setEnabled(True)
        self.download_url = url

    def start_update(self):
        if hasattr(self, 'download_url') and self.tray_app:
             self.status_label.setText("Starting update process... The application will restart.")
             self.tray_app.update_manager.perform_update(self.download_url)
