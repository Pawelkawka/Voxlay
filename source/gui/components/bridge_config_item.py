from PyQt6 import QtCore

class BridgeConfigItem(QtCore.QObject):
    valueChanged = QtCore.pyqtSignal(object)
    
    def __init__(self, value, options):
        super().__init__()
        self._value = value
        self.options = options
        self.range = [0, 0]
        self.validator = None
        self.restart = False
        
    @property
    def value(self):
        return self._value
        
    @value.setter
    def value(self, v):
        self._value = v
        self.valueChanged.emit(v)
        
    @property
    def key(self):
        return "BridgeKey"
