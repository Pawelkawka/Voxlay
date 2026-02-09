import logging
from PyQt6 import QtCore, QtGui

logger = logging.getLogger("Linux.Wayland")

def setup_window(window):
    logger.info("Setting up Wayland overlay window")
    
    flags = (
        QtCore.Qt.WindowType.ToolTip | 
        QtCore.Qt.WindowType.FramelessWindowHint |
        QtCore.Qt.WindowType.WindowStaysOnTopHint |
        QtCore.Qt.WindowType.WindowDoesNotAcceptFocus |
        QtCore.Qt.WindowType.WindowTransparentForInput |
        QtCore.Qt.WindowType.NoDropShadowWindowHint |
        QtCore.Qt.WindowType.BypassWindowManagerHint |
        QtCore.Qt.WindowType.X11BypassWindowManagerHint
    )
    
    window.setWindowFlags(flags)
    
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeToolTip, True)

def apply_click_through(window_id):
    logger.info("Wayland click through handled via qt window attributes (WA_TransparentForMouseEvents)")
