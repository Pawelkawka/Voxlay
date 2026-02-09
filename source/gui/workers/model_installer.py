from PyQt6 import QtCore
from engines import ctranslate2_engine

class ModelInstallerThread(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal(bool, str, str)

    def __init__(self, model_name, output_dir):
        super().__init__()
        self.model_name = model_name
        self.output_dir = output_dir

    def run(self):
        success, result = ctranslate2_engine.install_model(self.model_name, self.output_dir)
        self.finished_signal.emit(success, result, self.model_name)
