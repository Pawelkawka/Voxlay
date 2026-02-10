from PyQt6 import QtWidgets, QtCore
from ..common_widgets import (
    ScrollArea, SettingCardGroup, ComboBoxSettingCard, 
    PushSettingCard, SubtitleLabel, LineEdit, FluentIcon as FIF,
    InfoBar, InfoBarPosition, TitleLabel
)
from ..components.bridge_config_item import BridgeConfigItem
from ..components.server_config_card import ServerConfigCard
from ..dialogs.download_model_dialog import DownloadModelDialog
from ..workers.model_installer import ModelInstallerThread
from core.constants import DEFAULT_CONFIG_STRUCT, SOURCE_LANGUAGES, TARGET_LANGUAGES, TRANSLATOR_ENGINES, DEFAULT_CTRANSLATE2_MODEL_DIR
import logging
import threading
import shutil
from pathlib import Path

logger = logging.getLogger("GUI.General")

class GeneralInterface(ScrollArea):
    def __init__(self, parent=None, config=None, save_func=None):
        super().__init__(parent)
        self.config = config
        self.save_func = save_func
        logger.info("Initializing General interface")
        self.view = QtWidgets.QWidget(self)
        self.vBoxLayout = QtWidgets.QVBoxLayout(self.view)
        
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)
        self.view.setObjectName('view')
        self.setObjectName('GeneralInterface')
        
        self._init_ui()

    def _init_ui(self):
        layout = self.vBoxLayout
        
        layout.addWidget(TitleLabel("Languages"))
        langGroup = SettingCardGroup("", self.view)
        
        self.sourceLangCardLibreTranslate = ComboBoxSettingCard(
            BridgeConfigItem(DEFAULT_CONFIG_STRUCT["source_language"], list(SOURCE_LANGUAGES.keys())),
            FIF.MICROPHONE,
            "Source Language",
            "Language for speech recognition (Google)",
            list(SOURCE_LANGUAGES.values()),
            self.view
        )
        
        for i, (code, name) in enumerate(SOURCE_LANGUAGES.items()):
            self.sourceLangCardLibreTranslate.comboBox.setItemData(i, code)
        
        src_lang = self.config.get("source_language", "pl-PL")
        for i in range(self.sourceLangCardLibreTranslate.comboBox.count()):
            if self.sourceLangCardLibreTranslate.comboBox.itemData(i) == src_lang:
                self.sourceLangCardLibreTranslate.comboBox.setCurrentIndex(i)
                break
        
        self.sourceLangCardLibreTranslate.comboBox.currentIndexChanged.connect(self.change_source_language_libretranslate)
        
        self.sourceLangCardCTranslate2 = ComboBoxSettingCard(
            BridgeConfigItem(DEFAULT_CONFIG_STRUCT["source_language"], list(SOURCE_LANGUAGES.keys())),
            FIF.MICROPHONE,
            "Source Language",
            "Language for speech recognition (Google)",
            list(SOURCE_LANGUAGES.values()),
            self.view
        )
        
        for i, (code, name) in enumerate(SOURCE_LANGUAGES.items()):
            self.sourceLangCardCTranslate2.comboBox.setItemData(i, code)
        
        for i in range(self.sourceLangCardCTranslate2.comboBox.count()):
            if self.sourceLangCardCTranslate2.comboBox.itemData(i) == src_lang:
                self.sourceLangCardCTranslate2.comboBox.setCurrentIndex(i)
                break
        
        self.sourceLangCardCTranslate2.comboBox.currentIndexChanged.connect(self.change_source_language_ctranslate2)
        
        self.sourceLangCard = self.sourceLangCardLibreTranslate
        
        langGroup.addSettingCard(self.sourceLangCardLibreTranslate)
        langGroup.addSettingCard(self.sourceLangCardCTranslate2)
        
        self.targetLangCard = ComboBoxSettingCard(
            BridgeConfigItem(DEFAULT_CONFIG_STRUCT["target_language"], list(TARGET_LANGUAGES.keys())),
            FIF.LANGUAGE,
            "Target Language",
            "Language for translation (Libretranslate)",
            list(TARGET_LANGUAGES.values()),
            self.view
        )
        
        for i, (code, name) in enumerate(TARGET_LANGUAGES.items()):
            self.targetLangCard.comboBox.setItemData(i, code)
            
        tgt_lang = self.config.get("target_language", "en")
        for i in range(self.targetLangCard.comboBox.count()):
            if self.targetLangCard.comboBox.itemData(i) == tgt_lang:
                self.targetLangCard.comboBox.setCurrentIndex(i)
                break
                
        self.targetLangCard.comboBox.currentIndexChanged.connect(self.change_target_language)
        langGroup.addSettingCard(self.targetLangCard)
        
        src_lang_prefix = src_lang.split("-")[0].lower()
        self._update_target_language_options(src_lang_prefix)
        self._update_source_language_options_libretranslate(tgt_lang)
        
        layout.addWidget(langGroup)

        layout.addWidget(TitleLabel("Translation Engine"))
        engineGroup = SettingCardGroup("", self.view)
        
        self.engineCard = ComboBoxSettingCard(
            BridgeConfigItem(DEFAULT_CONFIG_STRUCT["translator_engine"], list(TRANSLATOR_ENGINES.keys())),
            FIF.ROBOT,
            "Translation Engine",
            "Select the translation engine to use",
            list(TRANSLATOR_ENGINES.values()),
            self.view
        )
        
        for i, (code, name) in enumerate(TRANSLATOR_ENGINES.items()):
            self.engineCard.comboBox.setItemData(i, code)
            
        current_engine = self.config.get("translator_engine", "libretranslate_local")
        for i in range(self.engineCard.comboBox.count()):
            if self.engineCard.comboBox.itemData(i) == current_engine:
                self.engineCard.comboBox.setCurrentIndex(i)
                break
                
        self.engineCard.comboBox.currentIndexChanged.connect(self.change_translator_engine)
        engineGroup.addSettingCard(self.engineCard)
        
        self.downloadModelCard = PushSettingCard(
            "Download New Model",
            FIF.DOWNLOAD,
            "Download and install a new Helsinki-NLP model",
            parent=self.view
        )
        self.downloadModelCard.clicked.connect(self.show_download_dialog)
        engineGroup.addSettingCard(self.downloadModelCard)
        
        self.modelCard = ComboBoxSettingCard(
            BridgeConfigItem(DEFAULT_CONFIG_STRUCT["ctranslate2_model"], [""]),
            FIF.FOLDER,
            "CTranslate2 Model",
            "Select the model to use (from config/Voxlay/models)",
            ["No models found"],
            self.view
        )
        self.modelCard.comboBox.currentIndexChanged.connect(self.change_ctranslate2_model)
        engineGroup.addSettingCard(self.modelCard)
        
        layout.addWidget(engineGroup)

        self.manageModelsTitle = TitleLabel("Manage Models")
        layout.addWidget(self.manageModelsTitle)
        self.manageModelsGroup = SettingCardGroup("", self.view)
        layout.addWidget(self.manageModelsGroup)
        
        self.serverTitle = TitleLabel("Server Configuration")
        layout.addWidget(self.serverTitle)
        self.serverGroup = SettingCardGroup("", self.view)
        self.serverCard = ServerConfigCard(self.config, self.save_func, self.view)
        self.serverGroup.addSettingCard(self.serverCard)
        
        layout.addWidget(self.serverGroup)
        
        layout.addStretch(1)
        self.update_visibility()

    def refresh_models(self):
        from engines import ctranslate2_engine
        from core.constants import DEFAULT_CTRANSLATE2_MODEL_DIR
        
        self.modelCard.comboBox.blockSignals(True)
        
        try:
            translator = ctranslate2_engine.get_translator(DEFAULT_CTRANSLATE2_MODEL_DIR)
            models = translator.list_models()
            
            self.modelCard.comboBox.clear()
            if not models:
                self.modelCard.comboBox.addItem("No models found", "")
                self.modelCard.setEnabled(False)
            else:
                self.modelCard.setEnabled(True)
                for i, model in enumerate(models):
                    self.modelCard.comboBox.addItem(model, model)
                
                current_model = self.config.get("ctranslate2_model", "")
                
                is_valid = False
                for i in range(self.modelCard.comboBox.count()):
                    data = self.modelCard.comboBox.itemData(i)
                    text = self.modelCard.comboBox.itemText(i)
                    if (data and data == current_model) or text == current_model:
                        self.modelCard.comboBox.setCurrentIndex(i)
                        is_valid = True
                        logger.info(f"Restored previously selected model: {current_model}")
                        break
                
                if not is_valid and self.modelCard.comboBox.count() > 0:
                    self.modelCard.comboBox.setCurrentIndex(0)
                    new_model = self.modelCard.comboBox.itemData(0) or self.modelCard.comboBox.itemText(0)
                    logger.info(f"Previous model '{current_model}' not found. Auto-selecting first available: {new_model}")
                    self.config["ctranslate2_model"] = new_model
                    if self.save_func: 
                        self.save_func()
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            self.modelCard.comboBox.addItem("Error listing models", "")
            self.modelCard.setEnabled(False)
        finally:
            self.modelCard.comboBox.blockSignals(False)
            self._update_model_management_list()

    def _update_model_management_list(self):
        while self.manageModelsGroup.viewLayout.count():
            item = self.manageModelsGroup.viewLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        from engines import ctranslate2_engine
        try:
            translator = ctranslate2_engine.get_translator(DEFAULT_CTRANSLATE2_MODEL_DIR)
            models = translator.list_models()
            
            if not models:
                self.manageModelsGroup.viewLayout.addWidget(QtWidgets.QLabel("No models installed."))
            else:
                for model_name in models:
                    item_widget = QtWidgets.QWidget()
                    item_layout = QtWidgets.QHBoxLayout(item_widget)
                    item_layout.setContentsMargins(10, 5, 10, 5)
                    
                    name_label = QtWidgets.QLabel(model_name)
                    item_layout.addWidget(name_label)
                    item_layout.addStretch()
                    
                    del_btn = QtWidgets.QPushButton("Delete")
                    del_btn.setFixedWidth(80)
                    del_btn.setStyleSheet("background-color: #c42b1c; color: white;")
                    del_btn.clicked.connect(lambda checked, m=model_name: self.delete_model(m))
                    item_layout.addWidget(del_btn)
                    
                    self.manageModelsGroup.viewLayout.addWidget(item_widget)
        except Exception as e:
            logger.error(f"Error updating management list: {e}")

    def delete_model(self, model_name):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.window(),
            "Delete Model",
            f"Are you sure you want to delete model '{model_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                model_path = Path(DEFAULT_CTRANSLATE2_MODEL_DIR) / model_name
                if model_path.exists():
                    import shutil
                    shutil.rmtree(model_path)
                    InfoBar.success(
                        title="Model Deleted",
                        content=f"Model {model_name} has been removed.",
                        orient=QtCore.Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000,
                        parent=self.window()
                    )
                    self.refresh_models()
            except Exception as e:
                logger.error(f"Error deleting model {model_name}: {e}")
                InfoBar.error(
                    title="Deletion Failed",
                    content=f"Could not delete model: {e}",
                    orient=QtCore.Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self.window()
                )

    def change_ctranslate2_model(self):
        idx = self.modelCard.comboBox.currentIndex()
        model = self.modelCard.comboBox.itemData(idx)
        text = self.modelCard.comboBox.itemText(idx)
        
        if not model and text and text not in ["No models found", "Error listing models", ""]:
            model = text
        
        logger.info(f"change_ctranslate2_model triggered. Index: {idx}, Data: '{model}'")
        
        if not model:
            text = self.modelCard.comboBox.currentText()
            if text and text not in ["No models found", "Error listing models", ""]:
                model = text
                logger.info(f"Data missing, using text as model name: {model}")

        if model:
            self.config["ctranslate2_model"] = model
            logger.info(f"Updated config['ctranslate2_model'] to: {model}")
            if self.save_func:
                self.save_func()
        else:
            logger.warning("change_ctranslate2_model called with empty model data/text")

    def change_target_language(self):
        code = self.targetLangCard.comboBox.currentData()
        logger.info(f"Changed target language to: {code}")
        
        source_lang = self.config.get("source_language", "pl-PL")
        source_lang_code = source_lang.split("-")[0].lower()
        
        self._update_source_language_options_libretranslate(code)
        
        if source_lang_code == code:
            logger.info(f"Source language {source_lang_code} matches target {code}, switching to different source")
            for code_src, name_src in SOURCE_LANGUAGES.items():
                src_lang_prefix = code_src.split("-")[0].lower()
                if src_lang_prefix != code:
                    self.config["source_language"] = code_src
                    for i in range(self.sourceLangCardLibreTranslate.comboBox.count()):
                        if self.sourceLangCardLibreTranslate.comboBox.itemData(i) == code_src:
                            self.sourceLangCardLibreTranslate.comboBox.blockSignals(True)
                            self.sourceLangCardLibreTranslate.comboBox.setCurrentIndex(i)
                            self.sourceLangCardLibreTranslate.comboBox.blockSignals(False)
                            break
                    break
        
        self.config["target_language"] = code
        if self.save_func:
            self.save_func()

    def _update_target_language_options(self, excluded_lang_code):
        self.targetLangCard.comboBox.blockSignals(True)
        current_selected = self.targetLangCard.comboBox.currentData()
        
        self.targetLangCard.comboBox.clear()
        
        for code, name in TARGET_LANGUAGES.items():
            if code != excluded_lang_code:
                self.targetLangCard.comboBox.addItem(name)
                self.targetLangCard.comboBox.setItemData(self.targetLangCard.comboBox.count() - 1, code)
        
        if current_selected and current_selected != excluded_lang_code:
            for i in range(self.targetLangCard.comboBox.count()):
                if self.targetLangCard.comboBox.itemData(i) == current_selected:
                    self.targetLangCard.comboBox.setCurrentIndex(i)
                    break
        
        self.targetLangCard.comboBox.blockSignals(False)

    def _update_source_language_options_libretranslate(self, excluded_lang_code):
        self.sourceLangCardLibreTranslate.comboBox.blockSignals(True)
        current_selected = self.sourceLangCardLibreTranslate.comboBox.currentData()
        
        self.sourceLangCardLibreTranslate.comboBox.clear()
        
        for code, name in SOURCE_LANGUAGES.items():
            src_lang_prefix = code.split("-")[0].lower()
            if src_lang_prefix != excluded_lang_code:
                self.sourceLangCardLibreTranslate.comboBox.addItem(name)
                self.sourceLangCardLibreTranslate.comboBox.setItemData(self.sourceLangCardLibreTranslate.comboBox.count() - 1, code)
        
        if current_selected:
            for i in range(self.sourceLangCardLibreTranslate.comboBox.count()):
                if self.sourceLangCardLibreTranslate.comboBox.itemData(i) == current_selected:
                    self.sourceLangCardLibreTranslate.comboBox.setCurrentIndex(i)
                    break
        
        self.sourceLangCardLibreTranslate.comboBox.blockSignals(False)

    def change_translator_engine(self):
        code = self.engineCard.comboBox.currentData()
        logger.info(f"Changed translator engine to: {code}")
        self.config["translator_engine"] = code
        if self.save_func:
            self.save_func()
        self.update_visibility()

    def update_visibility(self):
        engine = self.config.get("translator_engine", "libretranslate_local")
        if engine == "libretranslate_local":
            self.serverTitle.setVisible(True)
            self.serverGroup.setVisible(True)
            self.targetLangCard.setVisible(True)
            self.sourceLangCardLibreTranslate.setVisible(True)
            self.sourceLangCardCTranslate2.setVisible(False)
            self.modelCard.setVisible(False)
            self.downloadModelCard.setVisible(False)
            self.manageModelsTitle.setVisible(False)
            self.manageModelsGroup.setVisible(False)
            self.manageModelsGroup.setVisible(False)
            self.sourceLangCard = self.sourceLangCardLibreTranslate
        elif engine == "ctranslate2":
            self.serverTitle.setVisible(False)
            self.serverGroup.setVisible(False)
            self.targetLangCard.setVisible(False)
            self.sourceLangCardLibreTranslate.setVisible(False)
            self.sourceLangCardCTranslate2.setVisible(True)
            self.modelCard.setVisible(True)
            self.downloadModelCard.setVisible(True)
            self.manageModelsTitle.setVisible(True)
            self.manageModelsGroup.setVisible(True)
            self.sourceLangCard = self.sourceLangCardCTranslate2
            self.refresh_models()
        else:
            self.serverTitle.setVisible(False)
            self.serverGroup.setVisible(False)
            self.targetLangCard.setVisible(True)
            self.sourceLangCardLibreTranslate.setVisible(True)
            self.sourceLangCardCTranslate2.setVisible(False)
            self.modelCard.setVisible(False)
            self.downloadModelCard.setVisible(False)
            self.manageModelsTitle.setVisible(False)
            self.manageModelsGroup.setVisible(False)
            self.sourceLangCard = self.sourceLangCardLibreTranslate

    def change_source_language_libretranslate(self):
        code = self.sourceLangCardLibreTranslate.comboBox.currentData()
        logger.info(f"Changed LibreTranslate source language to: {code}")
        
        source_lang_code = code.split("-")[0].lower()
        target_lang = self.config.get("target_language", "en")
        
        self._update_target_language_options(source_lang_code)
        
        if source_lang_code == target_lang:
            logger.info(f"Target language {target_lang} matches source {source_lang_code}, switching to different target")
            for code_tgt, name_tgt in TARGET_LANGUAGES.items():
                if code_tgt != source_lang_code:
                    self.config["target_language"] = code_tgt
                    for i in range(self.targetLangCard.comboBox.count()):
                        if self.targetLangCard.comboBox.itemData(i) == code_tgt:
                            self.targetLangCard.comboBox.blockSignals(True)
                            self.targetLangCard.comboBox.setCurrentIndex(i)
                            self.targetLangCard.comboBox.blockSignals(False)
                            break
                    break
        
        self.config["source_language"] = code
        if self.save_func:
            self.save_func()

    def change_source_language_ctranslate2(self):
        code = self.sourceLangCardCTranslate2.comboBox.currentData()
        logger.info(f"Changed CTranslate2 source language to: {code}")
        
        self.config["source_language"] = code
        if self.save_func:
            self.save_func()

    def change_source_language(self):
        engine = self.config.get("translator_engine", "libretranslate_local")
        if engine == "ctranslate2":
            self.change_source_language_ctranslate2()
        else:
            self.change_source_language_libretranslate()

    def update_ui(self):
        src_lang = self.config.get("source_language", "pl-PL")
        for i in range(self.sourceLangCard.comboBox.count()):
            if self.sourceLangCard.comboBox.itemData(i) == src_lang:
                self.sourceLangCard.comboBox.setCurrentIndex(i)
                break
        
        tgt_lang = self.config.get("target_language", "en")
        for i in range(self.targetLangCard.comboBox.count()):
            if self.targetLangCard.comboBox.itemData(i) == tgt_lang:
                self.targetLangCard.comboBox.setCurrentIndex(i)
                break
                
        self.serverCard.setValue(self.config.get("libretranslate_url", "http://localhost:5000/translate"))

    def show_download_dialog(self):
        from engines import ctranslate2_engine
        current_source = self.config.get("source_language", "pl-PL")
        fixed_src = current_source.replace("_", "-").split("-")[0].lower().strip()
        
        dialog = DownloadModelDialog(self.window(), fixed_source_lang=fixed_src)
        if dialog.exec():
            model_name = dialog.get_model_name()
            
            if not model_name:
                return

            parts = model_name.split("-")
            if len(parts) >= 2:
                src = parts[-2]
                tgt = parts[-1]
                if src == tgt:
                    InfoBar.error(
                        title="Invalid Selection",
                        content=f"Source ({src}) and Target ({tgt}) languages cannot be the same.",
                        orient=QtCore.Qt.Orientation.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000,
                        parent=self.window()
                    )
                    return

            translator = ctranslate2_engine.get_translator(DEFAULT_CTRANSLATE2_MODEL_DIR)
            installed_models = translator.list_models()
            safe_name = model_name.replace("/", "_")
            legacy_name = model_name.split("/")[-1]
            
            if safe_name in installed_models or legacy_name in installed_models:
                InfoBar.warning(
                    title="Model Already Installed",
                    content=f"The model '{model_name}' is already installed.",
                    orient=QtCore.Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self.window()
                )
                return

            logger.info(f"User requested download of model: {model_name}")
            self.start_model_download(model_name)

    def start_model_download(self, model_name):
        self.downloadModelCard.setEnabled(False)
        self.modelCard.setEnabled(False)
        self.downloadModelCard.setContent("Downloading... Please wait.")
        self.downloadModelCard.button.setText("Downloading...")
        
        self.installer_thread = ModelInstallerThread(model_name, DEFAULT_CTRANSLATE2_MODEL_DIR)
        self.installer_thread.finished_signal.connect(self.on_download_finished)
        self.installer_thread.start()

    def on_download_finished(self, success, message, model_name):
        self.downloadModelCard.setEnabled(True)
        self.modelCard.setEnabled(True)
        self.downloadModelCard.setContent("Download and install a new Helsinki-NLP model")
        self.downloadModelCard.button.setText("Download New Model")
        
        if success:
            InfoBar.success(
                title="Model Installed",
                content=f"Model {model_name} installed successfully.",
                orient=QtCore.Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self.window()
            )
            self.refresh_models()
            
            safe_name = model_name.replace("/", "_")
            
            if not any(self.modelCard.comboBox.itemData(i) == safe_name for i in range(self.modelCard.comboBox.count())):
                 safe_name_legacy = model_name.split("/")[-1]
                 if any(self.modelCard.comboBox.itemData(i) == safe_name_legacy for i in range(self.modelCard.comboBox.count())):
                     safe_name = safe_name_legacy

            for i in range(self.modelCard.comboBox.count()):
                if self.modelCard.comboBox.itemData(i) == safe_name:
                    self.modelCard.comboBox.setCurrentIndex(i)
                    logger.info(f"Auto-selected new model: {safe_name}")
                    break
        else:
            InfoBar.error(
                title="Installation Failed",
                content=f"Failed to install model: {message}",
                orient=QtCore.Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=10000,
                parent=self.window()
            )
