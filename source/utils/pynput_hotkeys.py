try:
    from pynput import keyboard as pynput_keyboard
except ImportError:
    pynput_keyboard = None

import logging
import threading

logger = logging.getLogger("Linux.Hotkeys")

class PynputHotkeyManager:
    def __init__(self, controller):
        self.controller = controller
        self.listener = None
        self.hotkeys = {}
        self._key_mapping = {}

    def parse_hotkey(self, hotkey_str):
        parts = hotkey_str.lower().split('+')
        keys = []
        for part in parts:
            if part in ('ctrl', 'control'):
                keys.append(pynput_keyboard.Key.ctrl)
            elif part == 'alt':
                keys.append(pynput_keyboard.Key.alt)
            elif part == 'shift':
                keys.append(pynput_keyboard.Key.shift)
            elif len(part) == 1:
                keys.append(pynput_keyboard.KeyCode.from_char(part))
            else:
                pass
        return tuple(sorted(str(k) for k in keys))

    def start(self):
        if not pynput_keyboard:
            logger.warning("pynput not installed. Non-root hotkeys unavailable.")
            return

        self._restart_listener()

    def _restart_listener(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
            
        hotkey_map = {}
        
        def make_callback(cb):
            return lambda: cb()

        for name, data in self.hotkeys.items():
            hk_str = data['accel']
            hk_str = hk_str.lower().replace(" ", "")
            
            p_parts = []
            for part in hk_str.split('+'):
                if part in ('ctrl', 'control', 'alt', 'shift', 'win', 'cmd'):
                    p_parts.append(f"<{part}>")
                else:
                    p_parts.append(part)
            
            pynput_str = "+".join(p_parts)
            hotkey_map[pynput_str] = make_callback(data['callback'])
            
        try:
            self.listener = pynput_keyboard.GlobalHotKeys(hotkey_map)
            self.listener.start()
            logger.info(f"Started pynput GlobalHotKeys listener for {list(hotkey_map.keys())}")
        except Exception as e:
            logger.error(f"Failed to start hotkey listener: {e}")

    def register_hotkey(self, name, accelerator, callback):
        self.hotkeys[name] = {'accel': accelerator, 'callback': callback}
        self.start()

    def stop(self):
        if self.listener:
            self.listener.stop()

