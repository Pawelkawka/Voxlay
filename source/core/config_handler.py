import sys
import os
import json
import logging
from pathlib import Path
from copy import deepcopy
from core.constants import APP_NAME, DEFAULT_CONFIG_STRUCT, DEFAULT_CTRANSLATE2_MODEL_DIR

logger = logging.getLogger("Core.Config")

class ConfigHandler:
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_file_path = self.config_dir / "settings.json" if self.config_dir else None
        self.config = deepcopy(DEFAULT_CONFIG_STRUCT)

    def _get_config_dir(self):
        path = Path.home() / ".config" / APP_NAME
        
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Cannot create config folder {path}: {e}")
            path = Path(".") / APP_NAME
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e_fallback:
                logger.warning(f"Cannot create fallback config folder {path}: {e_fallback}")
                return None
        return path

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def _migrate_config(self):
        if self.config.get("border_color") == "#00FF00":
            self.config["border_color"] = "#4c4c4c"
            logger.info("Migrated old border color from #00FF00 to #4c4c4c")

    def load_config(self):
        logger.info("Loading configuration file...")
        if self.config_file_path and self.config_file_path.exists():
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                if isinstance(cfg, dict):
                    self.config = deepcopy(DEFAULT_CONFIG_STRUCT)
                    self.config.update(cfg)
                    
                    if self.config.get("ctranslate2_model_dir") == "models":
                        self.config["ctranslate2_model_dir"] = DEFAULT_CTRANSLATE2_MODEL_DIR
                        
                    try:
                        self.config["initial_silence_timeout"] = float(self.config.get("initial_silence_timeout", 4.0))
                    except (ValueError, TypeError):
                        logger.warning("Invalid initial_silence_timeout, using default 4.0")
                        self.config["initial_silence_timeout"] = 4.0

                    try:
                        self.config["silence_timeout"] = float(self.config.get("silence_timeout", 0.2))
                    except (ValueError, TypeError):
                        logger.warning("Invalid silence_timeout, using default 0.2")
                        self.config["silence_timeout"] = 0.2
                    
                    self._migrate_config()

                    logger.info("Configuration loaded successfully")
                else:
                    logger.warning("Invalid config format, using defaults")
                    self.config = deepcopy(DEFAULT_CONFIG_STRUCT)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self.config = deepcopy(DEFAULT_CONFIG_STRUCT)
        else:
            logger.info("No config file found, using defaults")
            self.config = deepcopy(DEFAULT_CONFIG_STRUCT)
        
        return self.config

    def save_config(self):
        if self.config_file_path:
            try:
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                logger.info("Configuration saved successfully")
            except Exception as e:
                logger.error(f"Error saving config: {e}")
        else:
            logger.warning("Cannot save configuration, file path is not available")

    def get(self, key, default=None):
        return self.config.get(key, default)

config_handler = ConfigHandler()
