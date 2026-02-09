import os
import logging
from pathlib import Path
import shutil
import subprocess
import sys

logger = logging.getLogger("CTranslate2Engine")

ctranslate2 = None
transformers = None
HAS_CTRANSLATE2 = None

def _import_libs():
    global ctranslate2, transformers, HAS_CTRANSLATE2
    if HAS_CTRANSLATE2 is not None:
        return HAS_CTRANSLATE2
        
    try:
        import torch
        import ctranslate2 as ct2
        import transformers as tf
        try:
            from transformers import MarianConfig, MarianTokenizer, AutoTokenizer
            try:
               AutoTokenizer.register(MarianConfig, slow_tokenizer_class=MarianTokenizer)
            except Exception:
               pass
        except ImportError:
            pass
            
        ctranslate2 = ct2
        transformers = tf
        HAS_CTRANSLATE2 = True
    except ImportError as e:
        HAS_CTRANSLATE2 = False
        logger.warning(f"Required libraries not installed ({e}). Please install them with: pip install torch ctranslate2 transformers sentencepiece")
    return HAS_CTRANSLATE2

class CTranslate2Wrapper:
    def __init__(self, model_dir="models", device="cpu", compute_type="int8"):
        self.model_dir = Path(model_dir)
        self.device = device
        self.compute_type = compute_type
        self.models = {}
        self.tokenizers = {}
        
        if not self.model_dir.exists():
            try:
                self.model_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create model directory {self.model_dir}: {e}")

    def _get_model_name(self, source_lang, target_lang):
        src = source_lang.split('-')[0].lower()
        tgt = target_lang.split('-')[0].lower()
        return f"Helsinki-NLP/opus-mt-{src}-{tgt}", src, tgt

    def _get_local_model_path(self, model_name):
        safe_name = model_name.replace("/", "_")
        return self.model_dir / safe_name

    def ensure_model(self, source_lang, target_lang):
        if not _import_libs():
            return False, "CTranslate2 libraries not installed."

        model_name, src, tgt = self._get_model_name(source_lang, target_lang)
        local_path = self._get_local_model_path(model_name)

        if local_path.exists() and (local_path / "model.bin").exists():
            return True, str(local_path)

        logger.info(f"Model {model_name} not found locally at {local_path}. Attempting to download and convert...")
        
        try:
            converter = ctranslate2.converters.TransformersConverter(model_name)
            converter.convert(str(local_path), force=True)
            logger.info(f"Model {model_name} converted and saved to {local_path}")
            return True, str(local_path)
        except Exception as e:
            logger.error(f"Failed to download/convert model {model_name}: {e}")
            return False, str(e)

    def list_models(self):
        if not self.model_dir.exists():
            return []
        
        models = []
        for item in self.model_dir.iterdir():
            if item.is_dir() and (item / "model.bin").exists():
                models.append(item.name)
        return models

    def load_model(self, source_lang, target_lang):
        model_name, src, tgt = self._get_model_name(source_lang, target_lang)
        local_path = self._get_local_model_path(model_name)
        
        if not local_path.exists() or not (local_path / "model.bin").exists():
            found = False
            for item in self.model_dir.iterdir():
                if item.is_dir() and f"{src}-{tgt}" in item.name:
                    local_path = item
                    found = True
                    break
            
            if not found:
                raise RuntimeError(f"Model for {src}-{tgt} not found at {local_path}. Please download it using the 'Download New Model' button.")
        
        return self.load_model_by_name(local_path.name)

    def load_model_by_name(self, model_name):
        if not _import_libs():
            raise RuntimeError("CTranslate2 libraries not installed.")

        if model_name in self.models:
            return self.models[model_name], self.tokenizers[model_name]

        if self.models:
            logger.info("Unloading previous models to free memory...")
            self.models.clear()
            self.tokenizers.clear()
            import gc
            gc.collect()

        local_path = self.model_dir / model_name
        if not local_path.exists() or not (local_path / "model.bin").exists():
             raise RuntimeError(f"Model {model_name} not found at {local_path}")

        logger.info(f"Loading model {model_name} from {local_path}...")
        
        try:
            translator = ctranslate2.Translator(str(local_path), device=self.device, compute_type=self.compute_type)
            
            candidates = [str(local_path), model_name.replace("_", "/")]
            if "opus-mt" in model_name and not model_name.startswith("Helsinki-NLP"):
                 candidates.append(f"Helsinki-NLP/{model_name.replace('_', '/')}")
            
            tokenizer = None
            last_err = None
            for candidate in candidates:
                try:
                    logger.debug(f"Attempting to load tokenizer from candidate: {candidate}")
                    tokenizer = transformers.AutoTokenizer.from_pretrained(candidate, local_files_only=True if candidate == str(local_path) else False)
                    if tokenizer:
                        logger.info(f"Successfully loaded tokenizer from: {candidate}")
                        break
                except Exception as ex:
                    last_err = ex
                    continue
            
            if tokenizer is None:
                logger.warning(f"Could not load tokenizer for {model_name}. Last error: {last_err}")
                if last_err:
                    raise last_err
                else:
                    raise RuntimeError(f"Failed to load tokenizer for {model_name}")

                    if (local_path / "source.spm").exists() and (local_path / "target.spm").exists():
                        try:
                            from transformers import MarianTokenizer
                            tokenizer = MarianTokenizer.from_pretrained(str(local_path))
                        except Exception:
                            pass
                    
                    if tokenizer is None:
                        logger.warning(f"Could not load tokenizer for {model_name}: {e}")
                        raise e
            
            self.models[model_name] = translator
            self.tokenizers[model_name] = tokenizer
            
            return translator, tokenizer
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            raise

    def translate(self, text, source_lang=None, target_lang=None, model_name=None):
        if not _import_libs():
            raise RuntimeError("CTranslate2 libraries not installed.")

        if model_name:
            translator, tokenizer = self.load_model_by_name(model_name)
        elif source_lang and target_lang:
            translator, tokenizer = self.load_model(source_lang, target_lang)
        else:
            raise ValueError("Translate called without model_name or source/target pair")
        
        source = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
        results = translator.translate_batch([source])
        target = results[0].hypotheses[0]
        translated_text = tokenizer.decode(tokenizer.convert_tokens_to_ids(target))
        
        return translated_text

def install_model(model_name, output_dir):
    if not _import_libs():
        return False, "Required libraries (torch, ctranslate2, transformers) are not installed. Model conversion requires torch."

    logger.info(f"Installing model {model_name} to {output_dir}...")
    
    try:
        output_path = Path(output_dir)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            
        target_dir = output_path / model_name.split("/")[-1]
        
        model_source = model_name
        try:
            from huggingface_hub import snapshot_download
            logger.info(f"Downloading {model_name} via huggingface_hub...")
            import tempfile
            
            downloaded_path = snapshot_download(repo_id=model_name, allow_patterns=["*.bin", "*.json", "*.spm", "*.txt", "*.safetensors"])
            if downloaded_path:
                model_source = downloaded_path
                logger.info(f"Model downloaded to {model_source}")
        except ImportError:
            logger.warning("huggingface_hub not installed or failed. Relying on default ctranslate2 download.")
        except Exception as e:
            logger.warning(f"huggingface_hub download failed: {e}. Trying default ctranslate2 download.")

        try:
            import sentencepiece
        except ImportError:
             return False, "Library 'sentencepiece' is missing. Please install it: pip install sentencepiece"

        import ctranslate2.converters
        converter = ctranslate2.converters.TransformersConverter(model_source)
        converter.convert(str(target_dir), force=True)
        
        if os.path.isdir(model_source):
            logger.info("Copying tokenizer files to target directory...")
            for f in os.listdir(model_source):
                if f.endswith(('.json', '.txt', '.spm', '.model')) and not f.startswith('model'):
                    source_f = os.path.join(model_source, f)
                    target_f = os.path.join(str(target_dir), f)
                    if not os.path.exists(target_f):
                        shutil.copy2(source_f, target_f)
            
        logger.info(f"Model {model_name} installed successfully.")
        return True, str(target_dir)
    except Exception as e:
        error_msg = str(e)
        if "Repository Not Found" in error_msg or "401 Client Error" in error_msg or "valid model identifier" in error_msg:
             return False, f"Model '{model_name}' does not exist on Hugging Face. Many direct language pairs are not available. Please try using the LibreTranslate engine (requires Docker) or use English as a main language."
        
        logger.error(f"Failed to install model {model_name}: {error_msg}")
        return False, f"Installation failed: {error_msg}"

_instance = None

def get_translator(model_dir="models", device="cpu", compute_type="int8"):
    global _instance
    if _instance is None:
        _instance = CTranslate2Wrapper(model_dir, device, compute_type)
    else:
        if str(_instance.model_dir) != str(model_dir):
             _instance.model_dir = Path(model_dir)
        _instance.device = device
        _instance.compute_type = compute_type
        
    return _instance
