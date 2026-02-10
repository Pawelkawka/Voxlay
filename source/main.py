import sys
import os
import logging
import threading
from PyQt6 import QtWidgets, QtCore, QtGui

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Main")

from core.config_handler import config_handler
from core.controller import ApplicationController
from core.constants import APP_NAME, APP_VERSION, OVERLAY_POSITIONS

app_controller = None

def register_hotkey_translation_wrapper(hotkey, window):
    if app_controller:
        config_handler.set("hotkey_translate", hotkey)
        return app_controller.register_hotkeys()
    return False

def register_hotkey_copy_wrapper(hotkey, window):
    if app_controller:
        config_handler.set("hotkey_copy", hotkey)
        return app_controller.register_hotkeys()
    return False

def main():
    global app_controller
    logger.info("Initializing application...")
    
    config_handler.load_config()
    
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY")
    
    if session_type == "wayland" or wayland_display:
        logger.info("Wayland session detected.")
        if not os.environ.get("QT_QPA_PLATFORM"):
            os.environ["QT_QPA_PLATFORM"] = "xcb;wayland"
            logger.info("Setting QT_QPA_PLATFORM='xcb;wayland' (XWayland prioritized for stable overlays).")
    else:
        if not os.environ.get("QT_QPA_PLATFORM"):
            os.environ["QT_QPA_PLATFORM"] = "xcb"
            logger.info("Forcing QT_QPA_PLATFORM='xcb' for X11.")
    
    logger.info("Creating QApplication...")
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    app.setDesktopFileName(APP_NAME.lower())
    
    app.setQuitOnLastWindowClosed(False)
    
    
    app_controller = ApplicationController(app)
    
    logger.info("Creating overlay window...")
    from gui.overlay_window import OverlayWindow
    cfg = config_handler.config
    
    icon_path = os.path.join(os.path.dirname(__file__), "pythonicon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))
    else:
        logger.warning(f"Icon file not found at {icon_path}")
    
    try:
        overlay = OverlayWindow(cfg)
        if os.path.exists(icon_path):
            overlay.setWindowIcon(QtGui.QIcon(icon_path))
        app_controller.set_overlay_window(overlay)
    except Exception as e:
        logger.critical(f"Failed to create OverlayWindow: {e}")
        sys.exit(1)
    
    logger.info("Initializing system tray...")
    from gui.tray_application import SystemTrayApp
    
    try:
        tray = SystemTrayApp(
            app_instance=app,
            overlay_window_instance=overlay,
            current_config_ref=config_handler.config,
            register_hotkey_translation_func=register_hotkey_translation_wrapper,
            register_hotkey_copy_func=register_hotkey_copy_wrapper,
            save_config_func=config_handler.save_config,
            app_version_ref=APP_VERSION
        )
        
        tray.controller = app_controller
    except Exception as e:
        logger.critical(f"Failed to create SystemTrayApp: {e}")
        sys.exit(1)
    
    logger.info("Registering hotkeys...")
    try:
        app_controller.register_hotkeys()
    except Exception as e:
        logger.error(f"Failed to register hotkeys: {e}")
    
    tray.show_settings_window()

    def preload_engines():
        logger.info("Pre-loading translation engines...")
        from engines import ctranslate2_engine
        ctranslate2_engine._import_libs()
        logger.info("Translation engines pre-loaded successfully.")

    QtCore.QTimer.singleShot(1000, lambda: threading.Thread(target=preload_engines, daemon=True).start())
    
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
