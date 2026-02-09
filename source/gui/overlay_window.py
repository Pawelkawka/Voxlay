import sys
import logging
from PyQt6 import QtWidgets, QtCore, QtGui

from platforms.linux import apply_click_through, setup_overlay_window as setup_platform_window

from core.constants import OVERLAY_POSITIONS

logger = logging.getLogger("GUI.Overlay")

class OverlayWindow(QtWidgets.QWidget):
    show_text_signal = QtCore.pyqtSignal(str, bool, bool, int)
    copy_to_clipboard_signal = QtCore.pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        self._init_ui()
        
        self._setup_window_flags()
        
        self.hide_timer = QtCore.QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_overlay_and_clear_text)
        
        self.show_text_signal.connect(self._on_show_text_signal)
        self.copy_to_clipboard_signal.connect(self._on_copy_to_clipboard)
        
        self.hide()
        
    def _init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.label = QtWidgets.QLabel(self)
        self.label.setWordWrap(True)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        
        self.layout.addWidget(self.label)
        
        self._apply_styles()
        
    def _setup_window_flags(self):
        try:
            setup_platform_window(self)
            self._apply_click_through()
            return
        except Exception as e:
            logger.error(f"Platform setup failed: {e}")
        
        flags = (
            QtCore.Qt.WindowType.ToolTip |
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.WindowDoesNotAcceptFocus |
            QtCore.Qt.WindowType.WindowTransparentForInput |
            QtCore.Qt.WindowType.BypassWindowManagerHint
        )
        
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self._apply_click_through()

    def _apply_click_through(self):
        apply_click_through(self.winId())

    def _apply_styles(self):
        font_size = self.config.get("font_size", 12)
        text_color = self.config.get("text_color", "#FFFFFF")
        bg_color_hex = self.config.get("background_color", "#000000")
        bg_opacity_percent = self.config.get("background_opacity", 80)
        
        bg_opacity_percent = max(0, min(100, bg_opacity_percent))
        bg_opacity = bg_opacity_percent / 100.0
        
        c = QtGui.QColor(bg_color_hex)
        c.setAlphaF(bg_opacity)
        
        bg_color_rgba = f"rgba({c.red()}, {c.green()}, {c.blue()}, {c.alphaF():.2f})"
        
        padding = self.config.get("padding", 10)
        border_width = self.config.get("border_width", 0)
        border_color = self.config.get("border_color", "#4c4c4c")
        corner_radius = self.config.get("corner_radius", 10)
        font_family = self.config.get("font_family", "Arial")
        font_bold = "bold" if self.config.get("font_bold", False) else "normal"
        
        style = (
            f"QLabel {{"
            f"  color: {text_color};"
            f"  font-family: '{font_family}';"
            f"  font-size: {font_size}px;"
            f"  font-weight: {font_bold};"
            f"  background-color: {bg_color_rgba};"
            f"  padding: {padding}px;"
            f"  border: {border_width}px solid {border_color};"
            f"  border-radius: {corner_radius}px;"
            f"}}"
        )
        self.label.setStyleSheet(style)
        
        font = QtGui.QFont(font_family, font_size)
        if self.config.get("font_bold", False):
            font.setBold(True)
        self.label.setFont(font)

    def update_settings_from_config(self, new_config):
        self.config = new_config
        self._apply_styles()
        if self.isVisible() and self.label.text():
            self._show_text_internal(self.label.text(), is_final=False)

    @QtCore.pyqtSlot(str, bool, bool, int)
    def _on_show_text_signal(self, text, is_error, is_final, duration_ms):
        self._show_text_internal(text, is_final, duration_ms)

    def _show_text_internal(self, text, is_final=True, duration_ms=0):
        if not text:
            self.hide()
            return
            
        self.label.setText(text)
        self.label.adjustSize()
        self.adjustSize()
        
        self.move_to_position(is_final, duration_ms)

    def move_to_position(self, is_final=True, duration_ms=0):
        pos_setting = self.config.get("overlay_position", "top_center")
        
        if " " in pos_setting:
            pos_setting = pos_setting.lower().replace(" ", "_")
            
        self._move_to_position(pos_setting)
        
        self.show()
        self.raise_()
        self._apply_click_through()
            
        if is_final:
            if duration_ms > 0:
                duration = duration_ms
            else:
                duration = self.config.get("overlay_display_time", 5) * 1000
            self.hide_timer.start(int(duration))
        else:
            self.hide_timer.stop()

    @QtCore.pyqtSlot(str)
    def _on_copy_to_clipboard(self, text):
        clipboard = QtWidgets.QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
            logger.info("Text copied to clipboard via OverlayWindow signal.")

    def _resize_and_position(self):
        min_w = self.config.get("overlay_min_width", 200)
        max_w = self.config.get("overlay_max_width", 800)
        min_h = self.config.get("overlay_min_height", 50)
        padding = self.config.get("padding", 10)
        
        metrics = QtGui.QFontMetrics(self.label.font())
        
        available_text_width = max_w - (2 * padding)
        rect = metrics.boundingRect(
            QtCore.QRect(0, 0, available_text_width, 0),
            QtCore.Qt.TextFlag.TextWordWrap,
            self.label.text()
        )
        
        required_width = rect.width() + 10
        width = max(min_w, min(max_w, required_width))
        
        required_height = rect.height() + 10
        height = max(min_h, required_height)
        
        self.resize(width, height)
        
        pos_key = self.config.get("overlay_position", "bottom_center")
        self._move_to_position(pos_key)

    def _move_to_position(self, pos_key):
        screen_geo = QtWidgets.QApplication.primaryScreen().geometry()
        
        if screen_geo.width() <= 0 or screen_geo.height() <= 0:
             logger.warning("Invalid screen geometry detected. Defaulting to 1920x1080 for calculation.")
             screen_geo.setWidth(1920)
             screen_geo.setHeight(1080)

        x, y = 0, 0
        w, h = self.width(), self.height()
        screen_margin = self.config.get("screen_margin", 10)
        
        if pos_key == "top_left":
            x, y = screen_margin, screen_margin
        elif pos_key == "top_center":
            x = (screen_geo.width() - w) // 2
            y = screen_margin
        elif pos_key == "top_right":
            x = screen_geo.width() - w - screen_margin
            y = screen_margin
        elif pos_key == "bottom_left":
            x = screen_margin
            y = screen_geo.height() - h - screen_margin
        elif pos_key == "bottom_center":
            x = (screen_geo.width() - w) // 2
            y = screen_geo.height() - h - screen_margin
        elif pos_key == "bottom_right":
            x = screen_geo.width() - w - screen_margin
            y = screen_geo.height() - h - screen_margin
            
        if x < 0: x = 0
        if y < 0: y = 0
            
        logger.debug(f"Moving overlay to {x}, {y} (Screen: {screen_geo.width()}x{screen_geo.height()})")
        self.move(x + screen_geo.x(), y + screen_geo.y())

    @QtCore.pyqtSlot()
    def hide_overlay_and_clear_text(self):
        self.hide()
        self.label.clear()

    def reposition_overlay(self, position_key, is_test_display=False):
        self.config["overlay_position"] = position_key
        self._resize_and_position()
        
        if is_test_display:
            self._show_text_internal("Test overlay position")
            self.hide_timer.start(3000)
