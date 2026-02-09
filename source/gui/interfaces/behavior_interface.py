from PyQt6 import QtWidgets, QtCore
from ..common_widgets import (
    ScrollArea, SettingCardGroup, RangeSettingCard, 
    SwitchSettingCard, PushSettingCard, TitleLabel,
    FluentIcon as FIF
)
from ..components.bridge_config_item import BridgeConfigItem
from core.constants import DEFAULT_CONFIG_STRUCT
import logging

logger = logging.getLogger("GUI.Behavior")

class BehaviorInterface(ScrollArea):
    def __init__(self, parent=None, config=None, save_func=None):
        super().__init__(parent)
        self.config = config
        self.save_func = save_func
        logger.info("Initializing Behavior interface")
        
        self.view = QtWidgets.QWidget(self)
        self.vBoxLayout = QtWidgets.QVBoxLayout(self.view)
        
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)
        self.view.setObjectName('view')
        self.setObjectName('BehaviorInterface')
        
        self._init_ui()

    def _init_ui(self):
        layout = self.vBoxLayout
        
        layout.addWidget(TitleLabel("Timing & Delays"))
        timingGroup = SettingCardGroup("", self.view)
        
        self.displayTimeCard = RangeSettingCard(
            BridgeConfigItem(DEFAULT_CONFIG_STRUCT["overlay_display_time"], []),
            FIF.HISTORY,
            "Overlay Display Time",
            "How long the overlay stays visible (seconds)",
            timingGroup
        )
        self.displayTimeCard.configItem.range = [5, 60]
        if hasattr(self.displayTimeCard, 'slider'):
             self.displayTimeCard.slider.setRange(5, 60)
             
        self.displayTimeCard.setValue(self.config.get("overlay_display_time", 15))
        self.displayTimeCard.valueChanged.connect(self.change_display_time)
        timingGroup.addSettingCard(self.displayTimeCard)
        
        self.phraseTimeCard = RangeSettingCard(
            BridgeConfigItem(DEFAULT_CONFIG_STRUCT["phrase_time_limit"], []),
            FIF.HISTORY,
            "Maximum Recording Time",
            "Max duration for a single speech segment (seconds)",
            timingGroup
        )
        self.phraseTimeCard.configItem.range = [10, 120]
        if hasattr(self.phraseTimeCard, 'slider'):
             self.phraseTimeCard.slider.setRange(10, 120)

        self.phraseTimeCard.setValue(self.config.get("phrase_time_limit", 30))
        self.phraseTimeCard.valueChanged.connect(self.change_phrase_time_limit)
        timingGroup.addSettingCard(self.phraseTimeCard)
        
        self.silenceCard = RangeSettingCard(
            BridgeConfigItem(int(DEFAULT_CONFIG_STRUCT["initial_silence_timeout"] * 10), []),
            FIF.MICROPHONE,
            "Initial Silence Timeout",
            "Wait time before stopping if no speech detected (x0.1s)",
            timingGroup
        )
        self.silenceCard.configItem.range = [15, 80]
        if hasattr(self.silenceCard, 'slider'):
             self.silenceCard.slider.setRange(15, 80)

        init_val = int(round(self.config.get("initial_silence_timeout", 1.5) * 10))
        self.silenceCard.setValue(init_val)
        self.silenceCard.valueChanged.connect(self.change_initial_silence_slider)
        
        timingGroup.addSettingCard(self.silenceCard)
        
        layout.addWidget(timingGroup)
        
        layout.addWidget(TitleLabel("Manual Control"))
        manualGroup = SettingCardGroup("", self.view)
        
        self.manualModeCard = SwitchSettingCard(
            FIF.POWER_BUTTON,
            "Enable Manual Recording Mode",
            "Manually start and stop recording with hotkeys instead of auto-detection",
            BridgeConfigItem(self.config.get("enable_manual_mode", False), []),
            manualGroup
        )
        self.manualModeCard.setChecked(self.config.get("enable_manual_mode", False))
        self.manualModeCard.checkedChanged.connect(self.toggle_manual_mode)
        manualGroup.addSettingCard(self.manualModeCard)
        
        layout.addWidget(manualGroup)
        
        layout.addStretch(1)

    def toggle_manual_mode(self, is_checked):
        logger.info(f"Toggled manual mode: {is_checked}")
        self.config["enable_manual_mode"] = is_checked
        if self.save_func:
            self.save_func()

    def change_display_time(self, value):
        logger.info(f"Changed overlay display time to: {value}s")
        self.config["overlay_display_time"] = value
        if self.save_func:
            self.save_func()

    def change_phrase_time_limit(self, value):
        logger.info(f"Changed phrase time limit to: {value}s")
        self.config["phrase_time_limit"] = value
        if self.save_func:
            self.save_func()

    def change_initial_silence_slider(self, value):
        float_val = value / 10.0
        logger.info(f"Changed initial silence timeout to: {float_val}s")
        self.config["initial_silence_timeout"] = float_val
        if self.save_func:
            self.save_func()

    def update_ui(self):
        self.displayTimeCard.setValue(self.config.get("overlay_display_time", 15))
        self.phraseTimeCard.setValue(self.config.get("phrase_time_limit", 30))
        init_val = int(round(self.config.get("initial_silence_timeout", 1.5) * 10))
        self.silenceCard.setValue(init_val)
