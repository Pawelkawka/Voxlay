import threading
import time
import logging
import speech_recognition as sr
from PyQt6 import QtCore
from core.sd_microphone import SoundDeviceMicrophone

logger = logging.getLogger("Core.Audio")

class AudioCaptureManager(QtCore.QObject):
    status_signal = QtCore.pyqtSignal(str, bool, bool)
    transcription_signal = QtCore.pyqtSignal(str)

    def __init__(self, config_handler):
        super().__init__()
        self.config_handler = config_handler
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.2
        self.recognizer.non_speaking_duration = 0.8
        self.is_listening = False
        self.stop_event = threading.Event()
        self.speech_prompt_timer = None
        
        self.current_session_id = 0
        self.session_lock = threading.Lock()

    def start_listening(self, manual=False):
        with self.session_lock:
            self.current_session_id += 1
            session_id = self.current_session_id
            
        self.stop_listening()
        
        self.is_listening = True
        self.stop_event.clear()
        
        threading.Thread(target=self._listen_loop, args=(session_id, manual), daemon=True).start()

    def stop_listening(self):
        self.stop_event.set()
        self._finish_listening()

    def _finish_listening(self):
        self.is_listening = False
        if self.speech_prompt_timer:
            self.speech_prompt_timer.cancel()
            self.speech_prompt_timer = None

    def _show_speak_now_prompt(self, engine_name, session_id):
        if self.is_listening and not self.stop_event.is_set() and session_id == self.current_session_id:
            self.status_signal.emit(f"Speak now ({engine_name})...", False, False)

    def _refresh_speech_prompt(self, engine_name, session_id):
        if self.is_listening and not self.stop_event.is_set() and session_id == self.current_session_id:
            self._show_speak_now_prompt(engine_name, session_id)
            
            if self.speech_prompt_timer:
                self.speech_prompt_timer.cancel()
                
            self.speech_prompt_timer = threading.Timer(4.5, self._refresh_speech_prompt, [engine_name, session_id])
            self.speech_prompt_timer.daemon = True
            self.speech_prompt_timer.start()

    def _listen_loop(self, session_id, manual=False):
        config = self.config_handler.config
        
        try:
            if session_id != self.current_session_id or self.stop_event.is_set(): return

            self.status_signal.emit("Calibrating noise (Google)...", False, False)
            
            try:
                with SoundDeviceMicrophone() as source:
                    if session_id != self.current_session_id or self.stop_event.is_set(): return
                    
                    try:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.7)
                    except sr.WaitTimeoutError:
                        logger.warning("Ambient noise adjustment timed out")
                    
                    logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")
                    
                    min_thresh = 500 if manual else 300
                    
                    if self.recognizer.energy_threshold > 4000:
                        logger.warning("Energy threshold too high, clamping to 4000")
                        self.recognizer.energy_threshold = 4000
                    elif self.recognizer.energy_threshold < min_thresh:
                        logger.warning(f"Energy threshold too low, clamping to {min_thresh}")
                        self.recognizer.energy_threshold = min_thresh
                    
                    if session_id != self.current_session_id or self.stop_event.is_set(): return
                    
                    if manual:
                        self.status_signal.emit("Speak now (Manual mode)...", False, False)
                    else:
                        self.status_signal.emit("Speak now (Google)...", False, False)
                        if self.speech_prompt_timer: self.speech_prompt_timer.cancel()
                        self.speech_prompt_timer = threading.Timer(4.5, self._refresh_speech_prompt, ["Google", session_id])
                        self.speech_prompt_timer.daemon = True
                        self.speech_prompt_timer.start()
                     
                    max_total_time = 300 if manual else config.get("phrase_time_limit", 30)
                    initial_silence = 300 if manual else config.get("initial_silence_timeout", 4.0)

                    try:
                        logger.debug(f"Listening with timeout={initial_silence}, phrase_limit={max_total_time}, manual={manual}")
                        
                        if manual:
                            frames = []
                            start_time = time.time()
                            chunk_size = source.CHUNK
                            
                            while not self.stop_event.is_set():
                                if session_id != self.current_session_id: break
                                
                                try:
                                    buffer = source.stream.read(chunk_size)
                                    if len(buffer) == 0: break
                                    frames.append(buffer)
                                except Exception as e:
                                    logger.error(f"Error reading stream: {e}")
                                    break
                                
                                if time.time() - start_time > max_total_time:
                                    logger.info("Manual recording reached time limit")
                                    break
                            
                            frame_data = b"".join(frames)
                            combined_audio = sr.AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                            logger.debug(f"Manual recording finished. Frames: {len(frames)}")
                            
                        else:
                            self.recognizer.pause_threshold = 1.2
                            self.recognizer.non_speaking_duration = 0.8
                            
                            combined_audio = self.recognizer.listen(
                                source,
                                timeout=initial_silence,
                                phrase_time_limit=max_total_time
                            )
                        
                        logger.debug("Listen completed successfully")
                    except sr.WaitTimeoutError:
                        if session_id == self.current_session_id and not self.stop_event.is_set():
                            self.status_signal.emit("No speech detected.", False, True)
                            self.stop_listening()
                        return

                    if self.stop_event.is_set() and not manual: return

                    if session_id == self.current_session_id:
                        self._finish_listening()
                    
                    if session_id != self.current_session_id: return
                    if self.stop_event.is_set() and not manual: return

                    self.status_signal.emit("Processing speech (Google)...", False, False)
                    
                    final_transcription = self.recognizer.recognize_google(
                        combined_audio, 
                        language=config.get("source_language", "pl-PL")
                    )
                    
                    if final_transcription and session_id == self.current_session_id:
                        if manual or not self.stop_event.is_set():
                            self.status_signal.emit(f"Recognized: {final_transcription}", False, False)
                            self.transcription_signal.emit(final_transcription)

            except sr.UnknownValueError:
                if session_id == self.current_session_id:
                    self.status_signal.emit("Could not understand audio.", False, True)
            except sr.RequestError as e:
                logger.error(f"Google Speech API error: {e}")
                if session_id == self.current_session_id:
                    self.status_signal.emit(f"Google Speech API error: {e}", True, True)
            except OSError as e:
                logger.error(f"Microphone error: {e}")
                self.status_signal.emit("Error: No microphone found or access denied.", True, True)
                return
            except Exception as e:
                logger.error(f"Unexpected error in listen loop: {e}", exc_info=True)
                self.status_signal.emit(f"Error: {e}", True, True)
                return
                
        except Exception as e:
            logger.error(f"General error in listen loop: {e}", exc_info=True)
            if session_id == self.current_session_id:
                self.status_signal.emit(f"Error: {e}", True, True)
