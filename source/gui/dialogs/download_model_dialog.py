from PyQt6 import QtWidgets, QtCore, QtGui
from ..common_widgets import MessageBoxBase, SubtitleLabel, ComboBox, BodyLabel
from core.constants import TARGET_LANGUAGES
import logging

logger = logging.getLogger("GUI.DownloadDialog")

class DownloadModelDialog(MessageBoxBase):
    def __init__(self, parent=None, fixed_source_lang=None):
        super().__init__(parent)
        self.setWindowTitle("Download Model")
        self.fixed_source_lang = fixed_source_lang.lower().strip() if fixed_source_lang else None
        self.titleLabel = SubtitleLabel("Download Helsinki-NLP Model", self)
        self.viewLayout.addWidget(self.titleLabel)
        
        if self.fixed_source_lang:
            self.infoLabel = BodyLabel(f"Source language is set to: {self.fixed_source_lang.upper()}. Select target language.", self)
        else:
            self.infoLabel = BodyLabel("Select source and target languages to download the corresponding model.", self)
            
        self.viewLayout.addWidget(self.infoLabel)
        
        self.formLayout = QtWidgets.QFormLayout()
        self.viewLayout.addLayout(self.formLayout)
        
        self.targetCombo = ComboBox(self)
        self.sourceCombo = None
        
        if not self.fixed_source_lang:
            self.sourceCombo = ComboBox(self)
            self.formLayout.addRow("Source Language:", self.sourceCombo)
            
        self.formLayout.addRow("Target Language:", self.targetCombo)
        
        self.warningLabel = BodyLabel("", self)
        self.warningLabel.setTextColor(QtGui.QColor("#ff9900"), QtGui.QColor("#ff9900"))
        self.warningLabel.setWordWrap(True)
        self.warningLabel.setVisible(False)
        self.viewLayout.addWidget(self.warningLabel)
        
        self.widget.setMinimumWidth(400)
        
        self.yesButton.setText("Download")
        self.cancelButton.setText("Cancel")
        
        self.targetCombo.currentIndexChanged.connect(self._check_direct_pair)
        
        self._init_languages()

    def _init_languages(self):
        languages = TARGET_LANGUAGES
        
        sorted_langs = sorted(languages.items(), key=lambda x: x[1])
        
        if not self.fixed_source_lang:
            for code, name in sorted_langs:
                self.sourceCombo.addItem(name, code)
            
            self.sourceCombo.currentIndexChanged.connect(self._update_target_combo)
            
            self.sourceCombo.setCurrentIndex(self.sourceCombo.findData("en"))
            
        self._update_target_combo()

    def _update_target_combo(self):
        current_target = self.targetCombo.currentData()
        self.targetCombo.clear()
        
        if self.fixed_source_lang:
            src_code = self.fixed_source_lang
        else:
            src_code = self.sourceCombo.currentData()
            
        logger.debug(f"Updating target combo. Source: {src_code}")
            
        languages = TARGET_LANGUAGES
        sorted_langs = sorted(languages.items(), key=lambda x: x[1])
        
        for code, name in sorted_langs:
            if str(code).lower().strip() == str(src_code).lower().strip():
                continue
            self.targetCombo.addItem(name, code)
            
        if current_target and current_target != src_code:
            idx = self.targetCombo.findData(current_target)
            if idx >= 0:
                self.targetCombo.setCurrentIndex(idx)
        
        if self.targetCombo.currentIndex() < 0:
             if src_code == "pl":
                 idx = self.targetCombo.findData("en")
             else:
                 idx = self.targetCombo.findData("pl")
                 
             if idx >= 0:
                 self.targetCombo.setCurrentIndex(idx)
             else:
                 if self.targetCombo.count() > 0:
                     self.targetCombo.setCurrentIndex(0)
                     
        logger.debug(f"Target combo updated. Count: {self.targetCombo.count()}, Current: {self.targetCombo.currentData()}")
        self._check_direct_pair()

    def _check_direct_pair(self):
        if self.fixed_source_lang:
            src = self.fixed_source_lang
        else:
            src = self.sourceCombo.currentData()
            
        tgt = self.targetCombo.currentData()
        
        if not src or not tgt:
            self.warningLabel.setVisible(False)
            return
            
        if src != "en" and tgt != "en":
            self.warningLabel.setText(f"Warning: Direct translation models for {src.upper()}-{tgt.upper()} often do not exist. If the download fails, please try using the LibreTranslate engine instead.")
            self.warningLabel.setVisible(True)
        else:
            self.warningLabel.setVisible(False)

    def get_model_name(self):
        if self.fixed_source_lang:
            src = self.fixed_source_lang
        else:
            src = self.sourceCombo.itemData(self.sourceCombo.currentIndex())
            
        tgt = self.targetCombo.itemData(self.targetCombo.currentIndex())
        
        if not tgt:
            text = self.targetCombo.currentText()
            for code, name in TARGET_LANGUAGES.items():
                if name == text:
                    tgt = code
                    break
        
        logger.info(f"get_model_name: src='{src}', tgt='{tgt}', fixed='{self.fixed_source_lang}'")
        
        if not src: src = "en"
        if not tgt: 
            return None
            
        return f"Helsinki-NLP/opus-mt-{src}-{tgt}"
