from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, 
    QPushButton, QFrame, QGroupBox, QScrollArea, QDialog,
    QLineEdit, QMessageBox, QSlider, QCheckBox, QColorDialog
)
from PyQt6 import QtCore, QtGui

class ScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")

class SimpleCard(QFrame):
    def __init__(self, title, content=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("QFrame { border: none; background: transparent; }")
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 5, 0, 5)
        
        info_layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.title_label)
        
        if content:
             self.content_label = QLabel(content)
             self.content_label.setWordWrap(True)
             info_layout.addWidget(self.content_label)
        else:
             self.content_label = None

        self.hBoxLayout.addLayout(info_layout)
        self.hBoxLayout.addStretch(1)
        self.setMinimumHeight(50)

    def setContent(self, content):
        if self.content_label:
            self.content_label.setText(content) 

class SettingCard(SimpleCard):
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(title, content, parent)

class ComboBoxSettingCard(SimpleCard):
    def __init__(self, config_item, icon, title, content, texts, parent=None):
        super().__init__(title, content, parent)
        self.configItem = config_item
        self.comboBox = QComboBox()
        if texts:
            self.comboBox.addItems(texts)
        self.comboBox.setFixedWidth(200)
        self.hBoxLayout.addWidget(self.comboBox)

class PushSettingCard(SimpleCard):
    clicked = QtCore.pyqtSignal()
    
    def __init__(self, text, icon, title, content=None, parent=None):
        super().__init__(title, content, parent)
        self.button = QPushButton(text)
        self.button.clicked.connect(self.clicked)
        self.hBoxLayout.addWidget(self.button)

class SwitchSettingCard(SimpleCard):
    checkedChanged = QtCore.pyqtSignal(bool)
    
    def __init__(self, icon, title, content, config_item=None, parent=None):
        super().__init__(title, content, parent)
        self.configItem = config_item
        self.checkbox = QCheckBox()
        self.checkbox.toggled.connect(self.checkedChanged)
        self.hBoxLayout.addWidget(self.checkbox)
        
    def setChecked(self, checked):
        self.checkbox.setChecked(checked)
        
    def isChecked(self):
        return self.checkbox.isChecked()

class RangeSettingCard(SimpleCard):
    valueChanged = QtCore.pyqtSignal(int)
    
    def __init__(self, config_item, icon, title, content, parent=None):
        super().__init__(title, content, parent)
        self.configItem = config_item
        self.slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setFixedWidth(150)
        self.slider.valueChanged.connect(self._on_value_changed)
        
        self.valueLabel = QLabel("0")
        self.hBoxLayout.addWidget(self.valueLabel)
        self.hBoxLayout.addWidget(self.slider)
        
    def _on_value_changed(self, val):
        self.valueLabel.setText(str(val))
        self.valueChanged.emit(val)
        
    def setValue(self, val):
        self.slider.setValue(val)
        self.valueLabel.setText(str(val))

class ColorSettingCard(SimpleCard):
    colorChanged = QtCore.pyqtSignal(object) 
    
    def __init__(self, config_item, icon, title, content, parent=None):
        super().__init__(title, content, parent)
        self.configItem = config_item
        self.colorBtn = QPushButton("Select Color")
        self.colorBtn.clicked.connect(self._pick_color)
        self.colorLabel = QLabel()
        self.colorLabel.setFixedSize(20, 20)
        self.colorLabel.setAutoFillBackground(True)
        
        self.hBoxLayout.addWidget(self.colorLabel)
        self.hBoxLayout.addWidget(self.colorBtn)
        
        self.currentColor = config_item.value if config_item and hasattr(config_item, 'value') else "#000000"
        self.setColor(self.currentColor)

    def _pick_color(self):
        color = QColorDialog.getColor(initial=QtGui.QColor(self.currentColor), parent=self)
        if color.isValid():
            self.setColor(color.name())
            self.colorChanged.emit(color)

    def setColor(self, color):
        self.currentColor = color
        self.colorLabel.setStyleSheet(f"background-color: {color}; border: 1px solid gray;")

class SettingCardGroup(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.viewLayout = QVBoxLayout(self)
        self.viewLayout.setSpacing(10)
        
    def addSettingCard(self, card):
        self.viewLayout.addWidget(card)

class SubtitleLabel(QLabel):
     def __init__(self, text, parent=None):
         super().__init__(text, parent)
         self.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")

     def setTextColor(self, color, dark_color=None):
         pass

class BodyLabel(QLabel):
     def setTextColor(self, color, dark_color=None):
         pass

class PrimaryPushButton(QPushButton):
    pass

class FluentIconMeta(type):
    def __getattr__(cls, name):
        return name

class FluentIcon(metaclass=FluentIconMeta):
    pass

class InfoBarPosition:
    TOP = 1
    BOTTOM = 2
    TOP_RIGHT = 3
    BOTTOM_RIGHT = 4

class InfoBar:
    @staticmethod
    def success(title, content, duration=2000, parent=None, position=None, **kwargs):
        print(f"[SUCCESS] {title}: {content}")
        if parent:
            QMessageBox.information(parent, title, content)

    @staticmethod
    def error(title, content, duration=2000, parent=None, position=None, **kwargs):
        print(f"[ERROR] {title}: {content}")
        if parent:
            QMessageBox.critical(parent, title, content)

    @staticmethod
    def warning(title, content, duration=2000, parent=None, position=None, **kwargs):
        print(f"[WARNING] {title}: {content}")
        if parent:
            QMessageBox.warning(parent, title, content)

    @staticmethod
    def info(title, content, duration=2000, parent=None, position=None, **kwargs):
        print(f"[INFO] {title}: {content}")
        if parent:
            QMessageBox.information(parent, title, content)

class MessageBoxBase(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.viewLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()
        
        self.layout.addLayout(self.viewLayout)
        self.layout.addLayout(self.buttonLayout)
        
        self.yesButton = QPushButton("Yes", self)
        self.cancelButton = QPushButton("Cancel", self)
        self.buttonLayout.addStretch(1)
        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addWidget(self.cancelButton)
        
        self.yesButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        
        self.widget = self

    def addWidget(self, widget):
        self.viewLayout.addWidget(widget)

    def setYesButtonText(self, text):
        self.yesButton.setText(text)
        
    def setCancelButtonText(self, text):
        self.cancelButton.setText(text)

class MessageBox:
    def __init__(self, title, content, parent=None):
        self.box = QMessageBox(parent)
        self.box.setWindowTitle(title)
        self.box.setText(content)
        self.box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)

    def exec(self):
        return self.box.exec() == QMessageBox.StandardButton.Yes

class LineEdit(QLineEdit):
    pass

class ComboBox(QComboBox):
    pass

class TitleLabel(QLabel):
     def __init__(self, text, parent=None):
         super().__init__(text, parent)
         self.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 2px; margin-top: 5px;")

class PrimaryPushSettingCard(PushSettingCard):
    pass

class HyperlinkCard(SimpleCard):
    def __init__(self, url, text, icon, title, content, parent=None):
        super().__init__(title, content, parent)
        self.url = url
        self.btn = QPushButton(text)
        self.btn.clicked.connect(self._open_url)
        self.hBoxLayout.addWidget(self.btn)
        
    def _open_url(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.url))
