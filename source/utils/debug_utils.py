import sys
import os
import logging
import requests
import time
import traceback
import importlib

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("VoxlayDebug")

def verbose_import(module_name):
    logger.info(f"[LOAD] Loading module: {module_name}...")
    try:
        start_time = time.time()
        mod = importlib.import_module(module_name)
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"[LOAD] Module {module_name} loaded successfully ({elapsed:.1f}ms)")
        return mod
    except ImportError as e:
        logger.error(f"[FAIL] Failed to load module {module_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"[FAIL] Unexpected error loading {module_name}: {e}")
        return None

def check_libretranslate(url):
    logger.info(f"[NET] Checking LibreTranslate connection: {url}")
    try:
        if not url.endswith('/translate'):
            check_url = url.rstrip('/') + '/translate'
        else:
            check_url = url
            
        payload = {"q": "test", "source": "auto", "target": "en"}
        headers = {"Content-Type": "application/json"}
        
        start = time.time()
        resp = requests.post(check_url, json=payload, headers=headers, timeout=3)
        latency = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            logger.info(f"[OK] LibreTranslate OK (Latency: {latency:.0f}ms)")
            return True
        elif resp.status_code == 400:
            logger.warning(f"[WARN] Got 400 on {check_url}, trying base URL {url}...")
            resp = requests.post(url, json=payload, headers=headers, timeout=3)
            if resp.status_code == 200:
                logger.info(f"[OK] LibreTranslate OK on base URL")
                return True
            else:
                logger.error(f"[ERROR] LibreTranslate Error: HTTP {resp.status_code}")
                return False
        else:
            logger.error(f"[ERROR] LibreTranslate Error: HTTP {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"[ERROR] LibreTranslate Unreachable: Connection refused. Is Docker running?")
        return False
    except Exception as e:
        logger.error(f"[ERROR] LibreTranslate Check Failed: {e}")
        return False

def exception_hook(exctype, value, tb):
    logger.critical("[CRITICAL] Uncaught exception occurred!")
    traceback.print_exception(exctype, value, tb)

sys.excepthook = exception_hook

def main_debug():
    logger.info("[INIT] Starting Voxlay Debugger...")
    
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    logger.info("--- Loading Core Libraries ---")
    verbose_import("sys")
    verbose_import("os")
    verbose_import("json")
    verbose_import("threading")
    verbose_import("time")
    
    logger.info("--- Loading 3rd Party Libraries ---")
    verbose_import("PyQt6.QtWidgets")
    verbose_import("PyQt6.QtCore")
    verbose_import("PyQt6.QtGui")
    verbose_import("speech_recognition")
    verbose_import("keyboard")
    verbose_import("requests")
    verbose_import("sounddevice")
    
    logger.info("--- Loading Application Modules ---")
    verbose_import("core.constants")
    verbose_import("gui.overlay_window")
    verbose_import("gui.tray_application")
    
    logger.info("--- Importing Main Application ---")
    try:
        import main as translator_main
        from core.constants import DEFAULT_LIBRETRANSLATE_URL
    except ImportError as e:
        logger.critical(f"[FATAL] Failed to import main: {e}")
        return

    logger.info("[CONFIG] Loading configuration...")

    from core.config_handler import config_handler
    config_handler.load_config()
    config = config_handler.config
    
    logger.info(f"   - Source Language: {config.get('source_language')}")
    logger.info(f"   - Target Language: {config.get('target_language')}")
    logger.info(f"   - LibreTranslate URL: {config.get('libretranslate_url')}")
    
    lt_url = config.get("libretranslate_url", DEFAULT_LIBRETRANSLATE_URL)
    if check_libretranslate(lt_url):
        logger.info("   - Translation Service: AVAILABLE")
    else:
        logger.warning("   - Translation Service: UNAVAILABLE (Check settings or Docker)")
    
    logger.info("[START] Starting Application Main Loop...")
    try:
        translator_main.main()
    except KeyboardInterrupt:
        logger.info("[STOP] Application stopped by user.")
    except Exception as e:
        logger.critical(f"[CRASH] Application crashed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main_debug()
