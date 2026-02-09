from PyQt6 import QtWidgets, QtCore, QtGui
from copy import deepcopy

from .interfaces.general_interface import GeneralInterface
from .interfaces.hotkeys_interface import HotkeysInterface
from .interfaces.appearance_interface import AppearanceInterface
from .interfaces.behavior_interface import BehaviorInterface
from .interfaces.updates_interface import UpdatesInterface
from core.constants import DEFAULT_CONFIG_STRUCT
from utils.app_control import restart_application

class SettingsWindow(QtWidgets.QMainWindow):
    def __init__(self, tray_app, current_config_ref,
                 register_hotkey_translation_func, register_hotkey_copy_func, register_hotkey_stop_func,
                 save_config_func, app_version_ref):
        super().__init__()
        self.tray_app = tray_app
        self.current_config_ref = current_config_ref
        self.register_hotkey_translation_func = register_hotkey_translation_func
        self.register_hotkey_copy_func = register_hotkey_copy_func
        self.register_hotkey_stop_func = register_hotkey_stop_func
        self.save_config_func = save_config_func
        self.app_version = app_version_ref
        
        self.setWindowTitle("Voxlay")
        
        self.resize(750, 750)
        self.setMinimumSize(750, 750)
        
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)
        
        self.tab_widget = QtWidgets.QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        self.generalInterface = GeneralInterface(self, self.current_config_ref, self.save_config_func)
        self.hotkeysInterface = HotkeysInterface(self, self.current_config_ref, self.register_hotkey_translation_func, self.register_hotkey_copy_func, self.register_hotkey_stop_func)
        self.appearanceInterface = AppearanceInterface(self, self.current_config_ref, self.tray_app)
        self.behaviorInterface = BehaviorInterface(self, self.current_config_ref, self.save_config_func)
        self.updatesInterface = UpdatesInterface(self, self.tray_app, self.app_version)
        
        self.initNavigation()
        
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.reset_btn = QtWidgets.QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.reset_btn)
        
        self.layout.addLayout(self.bottom_layout)

    def initNavigation(self):
        self.tab_widget.addTab(self.generalInterface, 'General')
        self.tab_widget.addTab(self.hotkeysInterface, 'Hotkeys')
        self.tab_widget.addTab(self.appearanceInterface, 'Appearance')
        self.tab_widget.addTab(self.behaviorInterface, 'Behavior')
        self.tab_widget.addTab(self.updatesInterface, 'Updates')

    def reset_to_defaults(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?\n\nThe application will restart automatically to apply changes.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            defaults = deepcopy(DEFAULT_CONFIG_STRUCT)
            
            try:
                self.current_config_ref.clear()
                self.current_config_ref.update(defaults)
                
                if self.save_config_func:
                    self.save_config_func()

                restart_application()

            except Exception as e:
                print(f"Error resetting defaults: {e}")

    def exit_application(self):
        self.close()
        self.tray_app.quit_app()
