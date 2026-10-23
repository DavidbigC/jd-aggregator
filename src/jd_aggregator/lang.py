import re

from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0

NAMES = {
    "en": "English", "zh": "中文", "ja": "日本語", "ko": "한국어", "ru": "Русский", "uk": "Українська",
    "pl": "Polski", "de": "Deutsch", "fr": "Français", "es": "Español", "pt": "Português", "it": "Italiano",
    "nl": "Nederlands", "tr": "Türkçe", "vi": "Tiếng Việt", "id": "Bahasa Indonesia", "th": "ไทย", "ar": "العربية",
}
_HANGUL = re.compile(r"[가-힯]")
_KANA = re.compile(r"[぀-ヿ]")
_HAN = re.compile(r"[一-鿿]")


def detect_lang(title: str | None, description: str | None = None) -> str | None:
    text = f"{title or ''}\n{(description or '')[:2000]}"
    cjk = len(_HAN.findall(text)) + len(_KANA.findall(text)) + len(_HANGUL.findall(text))
    if cjk >= 4:
        if len(_HANGUL.findall(text)) * 3 >= cjk:
            return "ko"
        return "ja" if _KANA.search(text) else "zh"
    if len(description or "") < 150 and text.isascii():
        return "en"
    try:
        return detect(text).split("-")[0]
    except LangDetectException:
        return None
