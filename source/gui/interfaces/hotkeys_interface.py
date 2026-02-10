from PyQt6 import QtWidgets, QtCore
from ..common_widgets import (
    ScrollArea, SettingCardGroup, FluentIcon as FIF, MessageBox, TitleLabel
)
from ..components.bridge_config_item import BridgeConfigItem
from ..components.key_sequence_card import KeySequenceCard
import logging

logger = logging.getLogger("GUI.Hotkeys")

class HotkeysInterface(ScrollArea):
    def __init__(self, parent=None, config=None, register_trans_func=None, register_copy_func=None):
        super().__init__(parent)
        self.config = config
        self.register_trans_func = register_trans_func
        self.register_copy_func = register_copy_func
        logger.info("Initializing Hotkeys interface")
        
        self.view = QtWidgets.QWidget(self)
        self.vBoxLayout = QtWidgets.QVBoxLayout(self.view)
        
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)
        self.view.setObjectName('view')
        self.setObjectName('HotkeysInterface')
        
        self._init_ui()

    def _init_ui(self):
        layout = self.vBoxLayout
        
        layout.addWidget(TitleLabel("Keyboard Shortcuts"))
        hotkeyGroup = SettingCardGroup("", self.view)
        
        self.trans_config_item = BridgeConfigItem(self.config.get("hotkey_translate", "ctrl+m"), [])
        self.translateHotkeyCard = KeySequenceCard(
            self.trans_config_item,
            FIF.EDIT,
            "Translation Hotkey",
            "Shortcut to trigger translation",
            hotkeyGroup
        )
        self.translateHotkeyCard.keySequenceChanged.connect(self.on_translate_hotkey_changed)
        hotkeyGroup.addSettingCard(self.translateHotkeyCard)
        
        self.copy_config_item = BridgeConfigItem(self.config.get("hotkey_copy", "ctrl+shift+c"), [])
        self.copyHotkeyCard = KeySequenceCard(
            self.copy_config_item,
            FIF.COPY,
            "Copy Hotkey",
            "Shortcut to trigger copy",
            hotkeyGroup
        )
        self.copyHotkeyCard.keySequenceChanged.connect(self.on_copy_hotkey_changed)
        hotkeyGroup.addSettingCard(self.copyHotkeyCard)
        
        layout.addWidget(hotkeyGroup)
        layout.addStretch(1)

    def on_translate_hotkey_changed(self, new_hotkey):
        old_hotkey = self.config.get("hotkey_translate", "ctrl+m")
        logger.info(f"Changing translation hotkey from '{old_hotkey}' to '{new_hotkey}'")
        if new_hotkey == old_hotkey:
            return

        current_copy_hotkey = self.config.get("hotkey_copy", "ctrl+shift+c")
        if new_hotkey == current_copy_hotkey:
            logger.warning(f"Translation hotkey '{new_hotkey}' conflicts with copy hotkey")
            MessageBox(
                "Duplicate Hotkey",
                f"The hotkey '{new_hotkey}' is already used by the copy function.\n"
                "Each function must have a unique keyboard shortcut.",
                parent=self.window()
            ).exec()
            self.trans_config_item.value = old_hotkey
            self.translateHotkeyCard.setValue(old_hotkey)
            return
        
        if self.register_trans_func:
            if self.register_trans_func(new_hotkey):
                logger.info(f"Translation hotkey successfully registered: {new_hotkey}")
                self.config["hotkey_translate"] = new_hotkey
            else:
                logger.error(f"Failed to register translation hotkey: {new_hotkey}")
                self.trans_config_item.value = old_hotkey
                self.translateHotkeyCard.setValue(old_hotkey)

    def on_copy_hotkey_changed(self, new_hotkey):
        old_hotkey = self.config.get("hotkey_copy", "ctrl+shift+c")
        logger.info(f"Changing copy hotkey from '{old_hotkey}' to '{new_hotkey}'")
        if new_hotkey == old_hotkey:
            return

        current_trans_hotkey = self.config.get("hotkey_translate", "ctrl+m")
        if new_hotkey == current_trans_hotkey:
            logger.warning(f"Copy hotkey '{new_hotkey}' conflicts with translation hotkey")
            MessageBox(
                "Duplicate Hotkey",
                f"The hotkey '{new_hotkey}' is already used by the translation function.\n"
                "Each function must have a unique keyboard shortcut.",
                parent=self.window()
            ).exec()
            self.copy_config_item.value = old_hotkey
            self.copyHotkeyCard.setValue(old_hotkey)
            return
        
        if self.register_copy_func:
            if self.register_copy_func(new_hotkey):
                logger.info(f"Copy hotkey successfully registered: {new_hotkey}")
                self.config["hotkey_copy"] = new_hotkey
            else:
                logger.error(f"Failed to register copy hotkey: {new_hotkey}")
                self.copy_config_item.value = old_hotkey
                self.copyHotkeyCard.setValue(old_hotkey)

    def update_ui(self):
        self.trans_config_item.value = self.config.get("hotkey_translate", "ctrl+m")
        self.translateHotkeyCard.setValue(self.trans_config_item.value)
        
        self.copy_config_item.value = self.config.get("hotkey_copy", "ctrl+shift+c")
        self.copyHotkeyCard.setValue(self.copy_config_item.value)
