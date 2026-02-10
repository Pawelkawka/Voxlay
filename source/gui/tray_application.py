from PyQt6 import QtWidgets, QtCore, QtGui
import sys
import os
import logging

try:
	import keyboard
except Exception:
	keyboard = None

from core.constants import APP_NAME, APP_VERSION, OVERLAY_POSITIONS
from utils.updater import UpdateManager
from utils.app_control import restart_application

logger = logging.getLogger("TrayApp")

class SystemTrayApp:
	def __init__(self, app_instance, overlay_window_instance,
				 current_config_ref,
				 register_hotkey_translation_func,
				 register_hotkey_copy_func,
				 save_config_func,
				 app_version_ref=APP_VERSION):
		self.app = app_instance
		self.overlay_window = overlay_window_instance
		self.current_config_ref = current_config_ref
		self.register_hotkey_translation_func = register_hotkey_translation_func
		self.register_hotkey_copy_func = register_hotkey_copy_func
		self.save_config_func = save_config_func
		self.app_version = app_version_ref
		
		self.controller = None

		self.tray_icon = QtWidgets.QSystemTrayIcon(self.app)
		self.settings_window = None
		self.debug_console_window = None

		self._suppress_tray_messages = False

		if getattr(sys, 'frozen', False):
			base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
		else:
			base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		
		icon_path_png = os.path.join(base_path, "pythonicon.png")
		
		if os.path.exists(icon_path_png):
			icon = QtGui.QIcon(icon_path_png)
		else:
			icon = self.app.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon)
		self.tray_icon.setIcon(icon)
		
		self.menu = QtWidgets.QMenu()
		settings_action = QtGui.QAction("Open Settings", self.app)
		settings_action.triggered.connect(self.show_settings_window)
		self.menu.addAction(settings_action)
		self.menu.addSeparator()
		exit_action = QtGui.QAction("Exit", self.app)
		exit_action.triggered.connect(self.quit_app)
		self.menu.addAction(exit_action)
		self.tray_icon.setContextMenu(self.menu)

		self.tray_icon.activated.connect(self._on_tray_activated)

		self.tray_icon.show()
		
		self.update_manager = UpdateManager(self.app_version)
		self.update_manager.signals.update_available.connect(self.on_update_available)
		self.update_manager.signals.update_error.connect(self.on_update_error)
		self.update_manager.signals.restart_required.connect(self.on_restart_required)
		
		QtCore.QTimer.singleShot(3000, lambda: self.update_manager.check_for_updates(silent=True))

	def on_restart_required(self):
		logger.info("Restart required signal received.")
		restart_application()

	def on_update_available(self, version, url):
		self._show_update_dialog(version, url)

	def on_update_error(self, error_msg):
		logger.warning(f"SystemTray on_update_error: {error_msg}")

	def _show_update_dialog(self, version, url):
		msg = QtWidgets.QMessageBox()
		msg.setWindowTitle("Update Available")
		msg.setText(f"A new version {version} is available!")
		msg.setInformativeText("Do you want to download and install it now?")
		msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
		msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
		
		if msg.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
			self.show_settings_window()
			self.settings_window.switch_to_updates_tab()
			if self.settings_window.updatesInterface and hasattr(self.settings_window.updatesInterface, 'start_update'):
				self.settings_window.updatesInterface.start_update()

	def _on_tray_activated(self, reason):
		if reason in (QtWidgets.QSystemTrayIcon.ActivationReason.Trigger,
					  QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick):
			self.show_settings_window()

	def change_position(self, position_key):
		old_position = self.current_config_ref.get("overlay_position")
		if old_position != position_key:
			self.overlay_window.reposition_overlay(position_key, is_test_display=True)
			self.current_config_ref["overlay_position"] = position_key
			try:
				self.save_config_func()
			except Exception:
				pass
			if not getattr(self, '_suppress_tray_messages', False):
				self.tray_icon.showMessage(
					"Voxlay",
					f"Position changed to: {OVERLAY_POSITIONS.get(position_key, 'Unknown')}",
					QtWidgets.QSystemTrayIcon.MessageIcon.Information,
					2000
				)

	def show_settings_window(self):
		if self.settings_window is None:
			from gui.main_window import SettingsWindow
			self.settings_window = SettingsWindow(self, self.current_config_ref,
							  self.register_hotkey_translation_internal,
							  self.register_hotkey_copy_internal,
							  self.save_config_func,
							  self.app_version)
		self.settings_window.show()
		self.settings_window.raise_()
		self.settings_window.activateWindow()

	def register_hotkey_translation_internal(self, new_hotkey_str):
		try:
			self.register_hotkey_translation_func(new_hotkey_str, self.overlay_window)
			self.current_config_ref["hotkey_translate"] = new_hotkey_str
			return True
		except Exception:
			return False

	def register_hotkey_copy_internal(self, new_hotkey_str):
		try:
			self.register_hotkey_copy_func(new_hotkey_str, self.overlay_window)
			self.current_config_ref["hotkey_copy"] = new_hotkey_str
			try:
				self.save_config_func()
			except Exception:
				pass
			return True
		except (ValueError, KeyError) as e:
			QtWidgets.QMessageBox.warning(self.overlay_window, "Hotkey Change Error",
				f"Failed to set shortcut '{new_hotkey_str.upper()}'.\nError: {e}")
			return False

	def quit_app(self):
		try:
			self.save_config_func()
		except Exception:
			pass
		try:
			if keyboard:
				keyboard.unhook_all()
		except Exception:
			pass
		if self.debug_console_window:
			try:
				self.debug_console_window.close()
			except Exception:
				pass
		self.tray_icon.hide()
		QtCore.QCoreApplication.quit()
