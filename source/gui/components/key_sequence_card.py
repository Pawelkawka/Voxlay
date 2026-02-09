from PyQt6 import QtWidgets, QtCore, QtGui
from ..common_widgets import SettingCard, PrimaryPushButton, FluentIcon

class KeyCaptureDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Press Hotkey")
        self.setFixedSize(400, 200)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        self.label = QtWidgets.QLabel("Press the key combination...", self)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        font = self.label.font()
        font.setPointSize(14)
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        self.sub_label = QtWidgets.QLabel("(Press Esc to cancel)", self)
        self.sub_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_label)
        
        self.cancel_btn = QtWidgets.QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
        
        self.result_string = None

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        if key == QtCore.Qt.Key.Key_Escape:
            self.reject()
            return

        if key in (QtCore.Qt.Key.Key_Control, QtCore.Qt.Key.Key_Shift, QtCore.Qt.Key.Key_Alt, QtCore.Qt.Key.Key_Meta):
            return

        parts = []
        if modifiers & QtCore.Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
            parts.append("alt")
        if modifiers & QtCore.Qt.KeyboardModifier.MetaModifier:
            parts.append("win")
            
        key_sequence = QtGui.QKeySequence(key)
        key_text = key_sequence.toString().lower()
        
        if not key_text:
            pass
            
        if key_text:
            parts.append(key_text)
            
        if parts:
            self.result_string = "+".join(parts)
            self.accept()

class KeySequenceCard(SettingCard):
    
    keySequenceChanged = QtCore.pyqtSignal(str)
    
    def __init__(self, config_item, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.config_item = config_item
        
        self.button = PrimaryPushButton(self.tr('Change'), self)
        self.button.setFixedWidth(120)
        self.button.clicked.connect(self._change_hotkey)
        
        self.hBoxLayout.addWidget(self.button, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        
        self._update_button_text()
        
    def _update_button_text(self):
        current = self.config_item.value
        if current:
            self.button.setText(current)
        else:
            self.button.setText(self.tr('Change'))

    def _change_hotkey(self):
        dialog = KeyCaptureDialog(self.window())
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted and dialog.result_string:
            new_hotkey = dialog.result_string
            self.config_item.value = new_hotkey
            self.keySequenceChanged.emit(new_hotkey)
            self._update_button_text()

    def setValue(self, value):
        self.config_item.value = value
        self._update_button_text()
