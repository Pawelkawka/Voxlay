import sys
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
try:
    from utils.pynput_hotkeys import PynputHotkeyManager
except ImportError:
    PynputHotkeyManager = None

import requests
import logging
from PyQt6 import QtCore

logger = logging.getLogger("Core.Controller")

from core.config_handler import config_handler
from core.audio_capture import AudioCaptureManager
from engines import ctranslate2_engine
from core.constants import (
    DEFAULT_LIBRETRANSLATE_URL, DEFAULT_SOURCE_LANGUAGE,
    DEFAULT_TRANSLATOR_ENGINE
)

class ApplicationController(QtCore.QObject):
    start_translation_signal = QtCore.pyqtSignal()
    stop_translation_signal = QtCore.pyqtSignal()
    copy_translation_signal = QtCore.pyqtSignal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.overlay_window = None
        self.audio_manager = AudioCaptureManager(config_handler)
        self.last_translated_text = ""
        
        self.hotkey_manager = PynputHotkeyManager(self) if PynputHotkeyManager else None
        
        self.executor = ThreadPoolExecutor(max_workers=2)

        self.audio_manager.status_signal.connect(self.on_audio_status)
        self.audio_manager.transcription_signal.connect(self.on_transcription_received)
        
        self.start_translation_signal.connect(self.start_translation_process)
        self.stop_translation_signal.connect(self.stop_translation_process)
        self.copy_translation_signal.connect(self.copy_last_translation)

    def set_overlay_window(self, window):
        self.overlay_window = window

    def request_translation_start(self):
        self.start_translation_signal.emit()

    def request_translation_stop(self):
        self.stop_translation_signal.emit()

    def request_copy_translation(self):
        self.copy_translation_signal.emit()

    @QtCore.pyqtSlot()
    def stop_translation_process(self):
        if self.audio_manager.is_listening:
            logger.info("Manual stop triggered.")
            self.audio_manager.stop_listening()
        elif config_handler.get("enable_manual_mode", False):
            logger.info("Manual Control hotkey pressed (Start).")
            self.start_translation_process()

    @QtCore.pyqtSlot()
    def start_translation_process(self):
        if not self.overlay_window: return
        
        if self.audio_manager.is_listening:
            logger.info("Toggle: Stopping translation process.")
            self.audio_manager.stop_listening()
            self.overlay_window.hide_overlay_and_clear_text()
            return

        self.overlay_window.update_settings_from_config(config_handler.config)
        self.overlay_window.hide_overlay_and_clear_text()
        
        manual_mode = config_handler.get("enable_manual_mode", False)
        self.audio_manager.start_listening(manual=manual_mode)

    def on_audio_status(self, message, is_error, is_final, duration_ms=0):
        if self.overlay_window:
            self.overlay_window.show_text_signal.emit(message, is_error, is_final, duration_ms)

    def on_transcription_received(self, text):
        self.executor.submit(self._translate_worker, text)

    def _translate_worker(self, text):
        try:
            config = config_handler.config
            engine = config.get("translator_engine", DEFAULT_TRANSLATOR_ENGINE)
            target_lang = config.get("target_language", "en")
            source_lang = config.get("source_language", DEFAULT_SOURCE_LANGUAGE)
            
            if source_lang == target_lang:
                logger.warning("Source and target languages are the same.")
                self.on_audio_status("Source and target languages are the same.", False, True)
                return

            translated_text = None
            
            if engine == "ctranslate2":
                self.on_audio_status("Translating (CTranslate2)...", False, False)
                model_dir = config.get("ctranslate2_model_dir", "models")
                device = "cpu" #force cpu
                compute_type = config.get("ctranslate2_compute_type", "int8")
                model_name = config.get("ctranslate2_model", "")
                
                logger.debug(f"CTranslate2 config: dir='{model_dir}', model='{model_name}'")
                
                if not model_name:
                    logger.warning("CTranslate2: No model selected.")
                    self.on_audio_status("Error: No model selected. Please select a model in Settings.", False, True)
                    return

                translator = ctranslate2_engine.get_translator(model_dir, device, compute_type)
                try:
                    translated_text = translator.translate(text, model_name=model_name)
                except Exception as e:
                    logger.error(f"Translation failed: {e}")
                    self.on_audio_status(f"Translation error: {e}", False, True)
                    return

            else:
                self.on_audio_status("Translating (LibreTranslate)...", False, False)
                url = config.get("libretranslate_url", DEFAULT_LIBRETRANSLATE_URL)
                
                src = "pl" if source_lang.startswith("pl") else ("en" if source_lang.startswith("en") else source_lang)
                
                translated_text = self._translate_libretranslate(text, src, target_lang, url)
                
            if translated_text:
                self.last_translated_text = translated_text
                self.on_audio_status(translated_text, False, True)
            elif translated_text is None and engine != "ctranslate2":
                 self.on_audio_status("Translation failed (Server error?)", False, True)

        except Exception as e:
            err_msg = str(e) if str(e) else f"Unknown error ({type(e).__name__})"
            logger.error(f"Translation worker error: {err_msg}")
            self.on_audio_status(f"Error: {err_msg}", False, True)

    def _translate_libretranslate(self, text, source, target, url):
        retries = 3
        backoff = 1
        for i in range(retries):
            try:
                payload = {"q": text, "source": source, "target": target}
                resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
                if resp.status_code == 200:
                    return resp.json().get("translatedText", "")
                else:
                    logger.error(f"LibreTranslate error: {resp.status_code} - {resp.text}")
            except requests.exceptions.Timeout:
                logger.warning(f"LibreTranslate timeout (attempt {i+1}/{retries})")
            except Exception as e:
                logger.error(f"LibreTranslate request error: {e}")
            
            if i < retries - 1:
                time.sleep(backoff)
                backoff *= 2
        
        return None

    def copy_last_translation(self):
        if self.last_translated_text and self.overlay_window:
            self.overlay_window.copy_to_clipboard_signal.emit(self.last_translated_text)
            self.on_audio_status("Copied to clipboard!", False, True, 2000)
        elif self.overlay_window:
            self.on_audio_status("No text to copy.", False, True, 2000)

    def register_hotkeys(self):
        if not self.hotkey_manager:
            logger.warning("Hotkey Manager unavailable (pynput missing?)")
            return False

        logger.info("Registering hotkeys using Pynput...")
        
        hotkey = config_handler.get("hotkey_translate")
        if hotkey:
            self.hotkey_manager.register_hotkey("translate", hotkey, self.request_translation_start)
            logger.info(f"Registered translation hotkey: {hotkey}")

        copy_hotkey = config_handler.get("hotkey_copy")
        if copy_hotkey:
            self.hotkey_manager.register_hotkey("copy", copy_hotkey, self.request_copy_translation)
            logger.info(f"Registered copy hotkey: {copy_hotkey}")

        stop_hotkey = config_handler.get("hotkey_stop", "ctrl+shift+s")
        if stop_hotkey:
            self.hotkey_manager.register_hotkey("stop", stop_hotkey, self.request_translation_stop)
            logger.info(f"Registered stop hotkey: {stop_hotkey}")
            
        self.hotkey_manager.start()
        return True
    def register_hotkeys_pynput(self):
        pass

    def update_hotkeys(self, new_trans_hotkey=None, new_copy_hotkey=None, new_stop_hotkey=None):
        if new_trans_hotkey:
            config_handler.set("hotkey_translate", new_trans_hotkey)
        if new_copy_hotkey:
            config_handler.set("hotkey_copy", new_copy_hotkey)
        if new_stop_hotkey:
            config_handler.set("hotkey_stop", new_stop_hotkey)
        self.register_hotkeys()
