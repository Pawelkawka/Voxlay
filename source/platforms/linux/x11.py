import logging
import subprocess
from PyQt6 import QtCore, QtGui

import os

logger = logging.getLogger("Linux.X11")

def apply_click_through(window_id):
    logger.info(f"Applying X11 click-through for window ID: {window_id}")
    pass

def setup_window(window):
    logger.info("Setting up X11 overlay window")
    
    flags = (
        QtCore.Qt.WindowType.ToolTip |
        QtCore.Qt.WindowType.FramelessWindowHint |
        QtCore.Qt.WindowType.WindowStaysOnTopHint |
        QtCore.Qt.WindowType.WindowDoesNotAcceptFocus |
        QtCore.Qt.WindowType.WindowTransparentForInput |
        QtCore.Qt.WindowType.X11BypassWindowManagerHint |
        QtCore.Qt.WindowType.BypassWindowManagerHint
    )
    
    window.setWindowFlags(flags)
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_X11NetWmWindowTypeToolTip, True)
