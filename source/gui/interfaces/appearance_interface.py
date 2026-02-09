from PyQt6 import QtWidgets, QtCore, QtGui
from ..common_widgets import (
    ScrollArea, SettingCardGroup, ComboBoxSettingCard, 
    FluentIcon as FIF, ColorSettingCard, RangeSettingCard,
    SwitchSettingCard, TitleLabel
)
from ..components.bridge_config_item import BridgeConfigItem
from core.constants import DEFAULT_CONFIG_STRUCT, OVERLAY_POSITIONS
import logging

logger = logging.getLogger("GUI.Appearance")

class AppearanceInterface(ScrollArea):
    def __init__(self, parent=None, config=None, tray_app=None):
        super().__init__(parent)
        self.config = config
        self.tray_app = tray_app
        logger.info("Initializing Appearance interface")
        
        self.view = QtWidgets.QWidget(self)
        self.vBoxLayout = QtWidgets.QVBoxLayout(self.view)
        
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)
        self.view.setObjectName('view')
        self.setObjectName('AppearanceInterface')
        
        self._init_ui()

    def _init_ui(self):
        layout = self.vBoxLayout
        
        layout.addWidget(TitleLabel("Preview"))
        previewGroup = SettingCardGroup("", self.view)
        self.previewSwitch = SwitchSettingCard(
            FIF.VIEW,
            "Live Preview Mode",
            "Show a sample text overlay while editing settings",
            BridgeConfigItem(False, []),
            previewGroup
        )
        self.previewSwitch.checkedChanged.connect(self._toggle_preview)
        previewGroup.addSettingCard(self.previewSwitch)
        layout.addWidget(previewGroup)
        
        layout.addWidget(TitleLabel("Position"))
        posGroup = SettingCardGroup("", self.view)
        
        self.posCard = ComboBoxSettingCard(
            BridgeConfigItem(DEFAULT_CONFIG_STRUCT["overlay_position"], list(OVERLAY_POSITIONS.keys())),
            FIF.ALIGNMENT,
            "Overlay Position",
            "Where the overlay appears on screen",
            list(OVERLAY_POSITIONS.values()),
            posGroup
        )
        
        for i, (key, name) in enumerate(OVERLAY_POSITIONS.items()):
            self.posCard.comboBox.setItemData(i, key)
            
        current_pos = self.config.get("overlay_position", "top_center")
        for i in range(self.posCard.comboBox.count()):
            if self.posCard.comboBox.itemData(i) == current_pos:
                self.posCard.comboBox.setCurrentIndex(i)
                break
                
        self.posCard.comboBox.currentIndexChanged.connect(self.change_overlay_position)
        posGroup.addSettingCard(self.posCard)
        layout.addWidget(posGroup)

        layout.addWidget(TitleLabel("Text"))
        typeGroup = SettingCardGroup("", self.view)
        
        default_font = self.config.get("font_family", "Arial")
        
        self.fontFamilyCard = ComboBoxSettingCard(
            BridgeConfigItem(default_font, [default_font]),
            FIF.FONT,
            "Font Family",
            "Select the font for the overlay text",
            [default_font], 
            typeGroup
        )
        
        fonts = QtGui.QFontDatabase.families()
        
        self.fontFamilyCard.comboBox.clear()
        self.fontFamilyCard.comboBox.addItems(fonts)
        
        if default_font in fonts:
            self.fontFamilyCard.comboBox.setCurrentText(default_font)
        elif fonts:
            self.fontFamilyCard.comboBox.setCurrentIndex(0)
            
        self.fontFamilyCard.comboBox.currentTextChanged.connect(lambda f: self._update_config("font_family", f))
        typeGroup.addSettingCard(self.fontFamilyCard)

        self.fontSizeCard = RangeSettingCard(
            BridgeConfigItem(self.config.get("font_size", 18), []),
            FIF.FONT_SIZE,
            "Font Size",
            "Adjust the text size",
            typeGroup
        )
        self.fontSizeCard.slider.setRange(10, 72)
        self.fontSizeCard.setValue(self.config.get("font_size", 18))
        self.fontSizeCard.valueChanged.connect(lambda v: self._update_config("font_size", v))
        typeGroup.addSettingCard(self.fontSizeCard)

        self.fontBoldCard = SwitchSettingCard(
            FIF.FONT,
            "Bold Text",
            "Make the text bold",
            BridgeConfigItem(self.config.get("font_bold", False), []),
            typeGroup
        )
        self.fontBoldCard.setChecked(self.config.get("font_bold", False))
        self.fontBoldCard.checkedChanged.connect(lambda c: self._update_config("font_bold", c))
        typeGroup.addSettingCard(self.fontBoldCard)

        self.textColorCard = ColorSettingCard(
            BridgeConfigItem(self.config.get("text_color", "#FFFFFF"), []),
            FIF.PALETTE,
            "Text Color",
            "Choose the color of the text",
            typeGroup
        )
        self.textColorCard.colorChanged.connect(lambda c: self._update_config("text_color", c.name()))
        typeGroup.addSettingCard(self.textColorCard)

        layout.addWidget(typeGroup)

        layout.addWidget(TitleLabel("Style"))
        styleGroup = SettingCardGroup("", self.view)

        self.bgColorCard = ColorSettingCard(
            BridgeConfigItem(self.config.get("background_color", "#000000"), []),
            FIF.BRUSH,
            "Background Color",
            "Choose the background color",
            styleGroup
        )
        self.bgColorCard.colorChanged.connect(self._on_bg_color_changed)
        styleGroup.addSettingCard(self.bgColorCard)

        self.borderColorCard = ColorSettingCard(
            BridgeConfigItem(self.config.get("border_color", "#4c4c4c"), []),
            FIF.PENCIL_INK,
            "Border Color",
            "Color of the window border",
            styleGroup
        )
        self.borderColorCard.colorChanged.connect(lambda c: self._update_config("border_color", c.name()))
        styleGroup.addSettingCard(self.borderColorCard)

        current_opacity_int = int(self.config.get("background_opacity", 80))
        self.bgOpacityCard = RangeSettingCard(
            BridgeConfigItem(current_opacity_int, []),
            FIF.CONSTRACT,
            "Background Opacity",
            "Adjust the transparency of the background",
            styleGroup
        )
        self.bgOpacityCard.slider.setRange(0, 100)
        self.bgOpacityCard.setValue(current_opacity_int)
        self.bgOpacityCard.valueChanged.connect(lambda v: self._update_config("background_opacity", v))
        styleGroup.addSettingCard(self.bgOpacityCard)

        self.radiusCard = RangeSettingCard(
            BridgeConfigItem(self.config.get("corner_radius", 10), []),
            FIF.CHECKBOX,
            "Corner Radius",
            "Roundness of the overlay corners",
            styleGroup
         )
        self.radiusCard.slider.setRange(0, 30)
        self.radiusCard.setValue(self.config.get("corner_radius", 10))
        self.radiusCard.valueChanged.connect(lambda v: self._update_config("corner_radius", v))
        styleGroup.addSettingCard(self.radiusCard)

        self.screenMarginCard = RangeSettingCard(
            BridgeConfigItem(self.config.get("screen_margin", 10), []),
            FIF.MOVE,
            "Screen Margin",
            "Distance from screen edges",
            styleGroup
        )
        self.screenMarginCard.slider.setRange(0, 200)
        self.screenMarginCard.setValue(self.config.get("screen_margin", 10))
        self.screenMarginCard.valueChanged.connect(lambda v: self._update_config("screen_margin", v))
        styleGroup.addSettingCard(self.screenMarginCard)

        self.paddingCard = RangeSettingCard(
            BridgeConfigItem(self.config.get("padding", 10), []),
            FIF.LAYOUT,
            "Padding",
            "Space between text and border",
            styleGroup
        )
        self.paddingCard.slider.setRange(1, 25)
        self.paddingCard.setValue(self.config.get("padding", 10))
        self.paddingCard.valueChanged.connect(lambda v: self._update_config("padding", v))
        styleGroup.addSettingCard(self.paddingCard)

        self.borderWidthCard = RangeSettingCard(
            BridgeConfigItem(self.config.get("border_width", 0), []),
            FIF.EDIT,
            "Border Width",
            "Thickness of the window border",
            styleGroup
        )
        self.borderWidthCard.slider.setRange(0, 10)
        self.borderWidthCard.setValue(self.config.get("border_width", 0))
        self.borderWidthCard.valueChanged.connect(lambda v: self._update_config("border_width", v))
        styleGroup.addSettingCard(self.borderWidthCard)

        layout.addWidget(styleGroup)
        
        layout.addStretch(1)

    def _update_config(self, key, value):
        logger.info(f"Updating config {key} -> {value}")
        self.config[key] = value
        if self.previewSwitch.isChecked() and self.tray_app and self.tray_app.controller.overlay_window:
             self.tray_app.controller.overlay_window.update_settings_from_config(self.config)

    def _on_bg_color_changed(self, color):
        self._update_config("background_color", color.name())

    def _on_opacity_changed(self, value):
        opacity = value / 100.0
        self._update_config("background_opacity", opacity)

    def change_overlay_position(self, index):
        key = self.posCard.comboBox.itemData(index)
        logger.info(f"Changed overlay position to: {key}")
        if key != self.config["overlay_position"]:
            self.config["overlay_position"] = key
            if self.tray_app:
                self.tray_app._suppress_tray_messages = True
                self.tray_app.change_position(key)
                self.tray_app._suppress_tray_messages = False
            if self.previewSwitch.isChecked() and self.tray_app and self.tray_app.controller.overlay_window:
                 self.tray_app.controller.overlay_window.update_settings_from_config(self.config)
        
    def _toggle_preview(self, is_checked):
        if not self.tray_app:
            return
            
        overlay = getattr(self.tray_app, 'overlay_window', None)
        if not overlay and self.tray_app.controller:
             overlay = self.tray_app.controller.overlay_window
             
        if not overlay:
            return

        if is_checked:
            sample_text = "This is a sample translation text.\nIt demonstrates how your overlay looks."
            overlay.update_settings_from_config(self.config)
            overlay.show_text_signal.emit(sample_text, False, False, 0)
        else:
            overlay.show_text_signal.emit("", False, True, 0)

    def update_ui(self):
        self.previewSwitch.setChecked(False)
        
        current_pos = self.config.get("overlay_position", "top_center")
        for i in range(self.posCard.comboBox.count()):
            if self.posCard.comboBox.itemData(i) == current_pos:
                self.posCard.comboBox.setCurrentIndex(i)
                break
        
        self.fontFamilyCard.comboBox.setCurrentText(self.config.get("font_family", "Arial"))
        self.fontSizeCard.setValue(self.config.get("font_size", 18))
        self.fontBoldCard.setChecked(self.config.get("font_bold", False))
        
        text_color = self.config.get("text_color", "#FFFFFF")
        self.textColorCard.setColor(QtGui.QColor(text_color))
        self.textColorCard.configItem.value = text_color
        
        bg_color = self.config.get("background_color", "#000000")
        self.bgColorCard.setColor(QtGui.QColor(bg_color))
        self.bgColorCard.configItem.value = bg_color

        self.bgOpacityCard.setValue(int(self.config.get("background_opacity", 80)))
        self.radiusCard.setValue(self.config.get("corner_radius", 10))
        self.paddingCard.setValue(self.config.get("padding", 10))
        self.borderWidthCard.setValue(self.config.get("border_width", 0))
        
        border_color = self.config.get("border_color", "#4c4c4c")
        self.borderColorCard.setColor(QtGui.QColor(border_color))
        self.borderColorCard.configItem.value = border_color
