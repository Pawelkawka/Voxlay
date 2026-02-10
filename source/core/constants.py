import sys
import os

APP_NAME = "Voxlay"

APP_VERSION = "0.3.0"

DEFAULT_HOTKEY = 'ctrl+m'
DEFAULT_COPY_HOTKEY = 'ctrl+shift+c'
DEFAULT_PHRASE_TIME_LIMIT = 30
DEFAULT_OVERLAY_DISPLAY_TIME = 15
DEFAULT_SOURCE_LANGUAGE = "pl-PL" 

DEFAULT_FONT_SIZE = 18
DEFAULT_TEXT_COLOR = "#FFFFFF"
DEFAULT_BACKGROUND_COLOR = "#000000"
DEFAULT_BACKGROUND_OPACITY = 80
DEFAULT_PADDING = 10
DEFAULT_BORDER_WIDTH = 0
DEFAULT_BORDER_COLOR = "#4c4c4c"
DEFAULT_CORNER_RADIUS = 10
DEFAULT_FONT_FAMILY = "Noto Sans Newa"

DEFAULT_FONT_BOLD = False
DEFAULT_OVERLAY_MIN_WIDTH = 250
DEFAULT_OVERLAY_MAX_WIDTH = 800
DEFAULT_OVERLAY_MIN_HEIGHT = 50
DEFAULT_OVERLAY_MAX_HEIGHT = 300
DEFAULT_OVERLAY_SHORT_TEXT_MIN_HEIGHT = 50
DEFAULT_OVERLAY_SHORT_TEXT_MAX_HEIGHT = 70

DEFAULT_OVERLAY_POSITION = "top_center"
DEFAULT_TARGET_LANGUAGE = "en"

DEFAULT_RECOGNIZER_ENGINE = "speech_recognition"

DEFAULT_TRANSLATOR_ENGINE = "ctranslate2"
DEFAULT_LIBRETRANSLATE_URL = "http://localhost:5000/translate"

DEFAULT_INITIAL_SILENCE_TIMEOUT = 4.0
DEFAULT_SILENCE_TIMEOUT = 0.20

OVERLAY_POSITIONS = {
    "top_left": "Top Left",
    "top_center": "Top Center",
    "top_right": "Top Right",
    "bottom_left": "Bottom Left",
    "bottom_center": "Bottom Center",
    "bottom_right": "Bottom Right",
}

TARGET_LANGUAGES = {
    "en": "English",
    "pl": "Polish",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "ru": "Russian",
    "nl": "Dutch",
    "cs": "Czech",
    "pt": "Portuguese",
}

SOURCE_LANGUAGES = {
    "pl-PL": "Polish",
    "en-US": "English (US)",
    "de-DE": "German",
    "es-ES": "Spanish",
    "it-IT": "Italian",
    "ru-RU": "Russian",
    "nl-NL": "Dutch",
    "cs-CZ": "Czech",
    "pt-PT": "Portuguese",
}

TRANSLATOR_ENGINES = {
    "libretranslate_local": "LibreTranslate (Local) [BETA - Experimental]",
    "ctranslate2": "CTranslate2 (Helsinki-NLP)"
}

DEFAULT_CTRANSLATE2_MODEL_DIR = os.path.join(os.path.expanduser("~"), ".config", "Voxlay", "models")

DEFAULT_CTRANSLATE2_COMPUTE_TYPE = "int8"

DEFAULT_CONFIG_STRUCT = {
    "hotkey_translate": DEFAULT_HOTKEY,
    "hotkey_copy": DEFAULT_COPY_HOTKEY,
    "overlay_position": DEFAULT_OVERLAY_POSITION,
    "target_language": DEFAULT_TARGET_LANGUAGE,
    "recognizer_engine": DEFAULT_RECOGNIZER_ENGINE,
    "translator_engine": DEFAULT_TRANSLATOR_ENGINE,
    "libretranslate_url": DEFAULT_LIBRETRANSLATE_URL,
    "libretranslate_api_key": "",
    "ctranslate2_model_dir": DEFAULT_CTRANSLATE2_MODEL_DIR,
    "ctranslate2_model": "",
    "ctranslate2_compute_type": DEFAULT_CTRANSLATE2_COMPUTE_TYPE,
    "source_language": DEFAULT_SOURCE_LANGUAGE,

    "font_size": DEFAULT_FONT_SIZE,
    "text_color": DEFAULT_TEXT_COLOR,
    "background_color": DEFAULT_BACKGROUND_COLOR,
    "background_opacity": DEFAULT_BACKGROUND_OPACITY,
    "padding": DEFAULT_PADDING,
    "border_width": DEFAULT_BORDER_WIDTH,
    "border_color": DEFAULT_BORDER_COLOR,
    "corner_radius": DEFAULT_CORNER_RADIUS,
    "font_family": DEFAULT_FONT_FAMILY,
    "font_bold": DEFAULT_FONT_BOLD,
    "overlay_min_width": DEFAULT_OVERLAY_MIN_WIDTH,
    "overlay_max_width": DEFAULT_OVERLAY_MAX_WIDTH,
    "overlay_min_height": DEFAULT_OVERLAY_MIN_HEIGHT,
    "overlay_max_height": DEFAULT_OVERLAY_MAX_HEIGHT,
    "overlay_short_text_min_height": DEFAULT_OVERLAY_SHORT_TEXT_MIN_HEIGHT,
    "overlay_short_text_max_height": DEFAULT_OVERLAY_SHORT_TEXT_MAX_HEIGHT,
    "overlay_display_time": DEFAULT_OVERLAY_DISPLAY_TIME,
    "phrase_time_limit": DEFAULT_PHRASE_TIME_LIMIT,
    "initial_silence_timeout": DEFAULT_INITIAL_SILENCE_TIMEOUT,
    "silence_timeout": DEFAULT_SILENCE_TIMEOUT,
    "enable_manual_mode": False,
}
