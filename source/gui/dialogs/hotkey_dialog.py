from PyQt6 import QtWidgets
try:
    import keyboard
except ImportError:
    keyboard = None
from ..common_widgets import LineEdit, PrimaryPushButton, BodyLabel

class HotkeyDialog(QtWidgets.QDialog):
    def __init__(self, current_hotkey_str, hotkey_type="general", parent=None):
        super().__init__(parent)
        if hotkey_type == "translate":
            self.setWindowTitle("Change Hotkey (Translation)")
        elif hotkey_type == "copy":
            self.setWindowTitle("Change Hotkey (Copy)")
        else:
            self.setWindowTitle(f"Change Hotkey ({hotkey_type})")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.initial_hotkey = current_hotkey_str
        self.new_hotkey_str = current_hotkey_str

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        self.info_label = BodyLabel(
            "Press the 'Record' button, then press the desired key combination.\n"
            "The combination will be automatically captured.\n"
            "You can also enter the shortcut manually (e.g. ctrl+alt+p)."
        )
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        self.hotkey_input_display = LineEdit()
        self.hotkey_input_display.setText(current_hotkey_str)
        self.hotkey_input_display.setReadOnly(True)
        self.layout.addWidget(self.hotkey_input_display)

        self.record_button = PrimaryPushButton("Record Hotkey")
        self.record_button.clicked.connect(self.toggle_recording_hotkey)
        self.layout.addWidget(self.record_button)

        self.recording_status_label = BodyLabel("Press the key combination...")
        self.recording_status_label.setVisible(False)
        self.recording_status_label.setStyleSheet("color: #009faa;")
        self.layout.addWidget(self.recording_status_label)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept_dialog)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.is_recording_active = False
        self.keyboard_hook_id = None
        self.currently_pressed_keys = set()
        self.recorded_key_combination_list = []

    def toggle_recording_hotkey(self):
        if not self.is_recording_active:
            self.is_recording_active = True
            self.currently_pressed_keys.clear()
            self.recorded_key_combination_list = []
            self.hotkey_input_display.clear()
            self.hotkey_input_display.setPlaceholderText("Recording... Press keys.")
            self.hotkey_input_display.setEnabled(False)
            self.recording_status_label.setVisible(True)
            self.record_button.setText("Stop Recording")
            self.keyboard_hook_id = keyboard.hook(self._handle_key_event_for_dialog, suppress=True)
            print("[HotkeyDialog] Started recording hotkey.")
        else:
            self._stop_hotkey_recording_session()
            print("[HotkeyDialog] Stopped recording hotkey (prematurely).")

    def _handle_key_event_for_dialog(self, event):
        if not self.is_recording_active: 
            return
        key_name = event.name
        if key_name is None: 
            return

        if key_name in ('ctrl_l', 'ctrl_r'): 
            key_name = 'ctrl'
        elif key_name in ('shift_l', 'shift_r'): 
            key_name = 'shift'
        elif key_name in ('alt_l', 'alt_r', 'alt gr'): 
            key_name = 'alt'
        elif key_name in ('cmd_l', 'cmd_r', 'win_l', 'win_r', 'left windows', 'right windows', 'meta'): 
            key_name = 'win'

        known_modifiers = {'ctrl', 'shift', 'alt', 'win'}

        if event.event_type == keyboard.KEY_DOWN:
            if key_name not in self.currently_pressed_keys:
                self.currently_pressed_keys.add(key_name)

            if key_name not in known_modifiers:
                self.recorded_key_combination_list = sorted([k for k in self.currently_pressed_keys if k in known_modifiers])
                if key_name not in self.recorded_key_combination_list:
                    self.recorded_key_combination_list.append(key_name)
                self._update_hotkey_display_from_list()
                self._stop_hotkey_recording_session()
            else:
                temp_display_list = sorted([k for k in self.currently_pressed_keys if k in known_modifiers])
                current_display = " + ".join(temp_display_list)
                if temp_display_list:
                    current_display += " + ..."
                else:
                    current_display = "Press keys..."
                self.hotkey_input_display.setText(current_display)

        elif event.event_type == keyboard.KEY_UP:
            if key_name in self.currently_pressed_keys:
                self.currently_pressed_keys.remove(key_name)
            if self.is_recording_active:
                temp_display_list = sorted([k for k in self.currently_pressed_keys if k in known_modifiers])
                current_display = " + ".join(temp_display_list)
                if temp_display_list:
                    current_display += " + ..."
                else:
                    current_display = "Press keys..."
                self.hotkey_input_display.setText(current_display)

    def _update_hotkey_display_from_list(self):
        if self.recorded_key_combination_list:
            self.new_hotkey_str = "+".join(self.recorded_key_combination_list)
            self.hotkey_input_display.setText(self.new_hotkey_str)
        else:
            self.hotkey_input_display.setText(self.initial_hotkey)
            self.new_hotkey_str = self.initial_hotkey

    def _stop_hotkey_recording_session(self):
        if self.is_recording_active:
            self.is_recording_active = False
            if self.keyboard_hook_id:
                keyboard.unhook(self.keyboard_hook_id)
                self.keyboard_hook_id = None
            self.hotkey_input_display.setEnabled(True)
            self.recording_status_label.setVisible(False)
            self.record_button.setText("Record Hotkey")
            if not self.recorded_key_combination_list:
                self.hotkey_input_display.setText(self.initial_hotkey)
                self.new_hotkey_str = self.initial_hotkey

    def accept_dialog(self):
        if self.is_recording_active: 
            self._stop_hotkey_recording_session()
        final_text = self.hotkey_input_display.text().strip().lower()
        if not final_text or "..." in final_text or final_text == "press keys...":
            QtWidgets.QMessageBox.warning(self, "Incomplete Hotkey", "No valid shortcut was recorded or entered.")
            return
        try:
            keyboard.parse_hotkey(final_text)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Hotkey Format",
                                          f"The shortcut '{final_text}' has an invalid format.\n"
                                          "Examples: 'ctrl+shift+a', 'alt+f1', 'win+space'.")
            return
        self.new_hotkey_str = final_text
        self.accept()

    def get_hotkey(self): 
        return self.new_hotkey_str

    def closeEvent(self, event):
        if self.is_recording_active: 
            self._stop_hotkey_recording_session()
        super().closeEvent(event)
