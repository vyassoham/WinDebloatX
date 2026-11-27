"""
WinDebloatX - Internationalization & Localization Engine (i18n)
Provides dictionary-driven multi-language translation support with fallback caching.
"""

import json
import os
from typing import Dict, List, Optional
from core.logger import log_debug

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "es": "Español",
    "de": "Deutsch",
    "zh": "简体中文"
}

_current_lang = "en"
_translations: Dict[str, str] = {}
_fallback_translations: Dict[str, str] = {}

def load_locale(lang_code: str) -> Dict[str, str]:
    """Loads a translation JSON file from locales/."""
    path = os.path.join(LOCALES_DIR, f"{lang_code}.json")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log_debug(f"Error reading locale file {path}: {e}")
    return {}

def init_i18n(lang_code: str = "en"):
    """Initializes translation dictionaries."""
    global _current_lang, _translations, _fallback_translations
    _fallback_translations = load_locale("en")
    set_language(lang_code)

def set_language(lang_code: str):
    """Switches active application language."""
    global _current_lang, _translations
    if lang_code not in SUPPORTED_LANGUAGES:
        lang_code = "en"
    _current_lang = lang_code
    _translations = load_locale(lang_code)

def get_current_language() -> str:
    """Returns active language code."""
    return _current_lang

def t(key: str, default: Optional[str] = None) -> str:
    """Translates a string key into the active language."""
    if not _translations and not _fallback_translations:
        init_i18n(_current_lang)

    val = _translations.get(key)
    if val is not None:
        return val

    # Fallback to English
    val = _fallback_translations.get(key)
    if val is not None:
        return val

    return default if default is not None else key

# Initialize on import
init_i18n("en")
