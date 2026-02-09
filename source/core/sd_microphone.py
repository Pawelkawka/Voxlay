try:
    import sounddevice as sd
except OSError:
    sd = None
import speech_recognition as sr
import logging

logger = logging.getLogger("SoundDeviceMic")

class SoundDeviceStreamWrapper:
    def __init__(self, sd_stream, sample_width):
        self.sd_stream = sd_stream
        self.sample_width = sample_width
    
    def read(self, size):
        frames = size // self.sample_width
        data, overflowed = self.sd_stream.read(frames)
        return bytes(data)

class SoundDeviceMicrophone(sr.AudioSource):
    def __init__(self, device=None, sample_rate=16000, chunk_size=1024):
        self.device_index = device
        self.SAMPLE_RATE = sample_rate
        self.CHUNK = chunk_size
        self.SAMPLE_WIDTH = 2
        self.stream = None
        self._audio_stream = None

    def __enter__(self):
        if sd is None:
            msg = "PortAudio library not found. Please install 'portaudio19-dev' (Ubuntu/Debian) or equivalent."
            logger.critical(msg)
            raise OSError(msg)
            
        self._audio_stream = sd.RawInputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.CHUNK,
            device=self.device_index,
            channels=1,
            dtype='int16',
            latency='low'
        )
        self._audio_stream.start()
        self.stream = SoundDeviceStreamWrapper(self._audio_stream, self.SAMPLE_WIDTH)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._audio_stream:
            self._audio_stream.stop()
            self._audio_stream.close()
            self._audio_stream = None
        self.stream = None
