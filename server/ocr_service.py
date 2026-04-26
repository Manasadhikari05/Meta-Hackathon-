"""OCR for memes / images.

Primary engine: **EasyOCR** — DL-based, robust on stylized meme text and
natural images.
Fallback: **pytesseract** (the Homebrew `tesseract` binary on macOS) — fast
and offline; less accurate on stylized fonts but a safe last resort.

The EasyOCR reader is initialized lazily and cached so the first OCR request
isn't slowed by the ~120 MB model download every time.
"""

from __future__ import annotations

import io
import os
import threading
from typing import Optional, Tuple

_easyocr_reader = None
_easyocr_unavailable_reason: Optional[str] = None
_lock = threading.Lock()


def _get_easyocr():
    global _easyocr_reader, _easyocr_unavailable_reason
    if _easyocr_reader is not None:
        return _easyocr_reader
    if _easyocr_unavailable_reason is not None:
        return None
    with _lock:
        if _easyocr_reader is not None:
            return _easyocr_reader
        if _easyocr_unavailable_reason is not None:
            return None
        try:
            import easyocr  # type: ignore

            langs = [
                s.strip() for s in os.getenv("OCR_LANGS", "en").split(",") if s.strip()
            ] or ["en"]
            print(f"[ocr] initializing EasyOCR (langs={langs}, gpu=False)…")
            _easyocr_reader = easyocr.Reader(langs, gpu=False, verbose=False)
            print("[ocr] EasyOCR ready.")
            return _easyocr_reader
        except Exception as exc:
            _easyocr_unavailable_reason = str(exc)
            print(f"[ocr] EasyOCR unavailable: {exc}. Will fall back to tesseract.")
            return None


def _bytes_to_pil(image_bytes: bytes):
    from PIL import Image  # type: ignore

    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def _extract_with_easyocr(image_bytes: bytes) -> Optional[str]:
    reader = _get_easyocr()
    if reader is None:
        return None
    try:
        import numpy as np  # type: ignore

        img = _bytes_to_pil(image_bytes)
        arr = np.array(img)
        # paragraph=True merges short lines that belong together (helps memes)
        results = reader.readtext(arr, detail=0, paragraph=True)
        text = "\n".join(s.strip() for s in results if s and s.strip())
        return text or None
    except Exception as exc:
        print(f"[ocr] EasyOCR run failed: {exc}")
        return None


def _extract_with_tesseract(image_bytes: bytes) -> Optional[str]:
    try:
        import pytesseract  # type: ignore

        img = _bytes_to_pil(image_bytes)
        # psm 6: assume a uniform block of text (typical meme caption)
        text = pytesseract.image_to_string(img, config="--psm 6").strip()
        return text or None
    except Exception as exc:
        print(f"[ocr] tesseract failed: {exc}")
        return None


def extract_text(image_bytes: bytes) -> Tuple[str, str]:
    """Return (text, engine). engine in {easyocr, tesseract, none}."""
    txt = _extract_with_easyocr(image_bytes)
    if txt:
        return txt, "easyocr"
    txt = _extract_with_tesseract(image_bytes)
    if txt:
        return txt, "tesseract"
    return "", "none"


def warm() -> None:
    """Best-effort prewarm of EasyOCR so the first request isn't slow."""
    try:
        _get_easyocr()
    except Exception as exc:
        print(f"[ocr] warm failed: {exc}")


def status() -> dict:
    return {
        "easyocr_loaded": _easyocr_reader is not None,
        "easyocr_unavailable_reason": _easyocr_unavailable_reason,
        "tesseract_available": _which_tesseract(),
        "langs": os.getenv("OCR_LANGS", "en"),
    }


def _which_tesseract() -> bool:
    try:
        import pytesseract  # type: ignore

        return bool(pytesseract.get_tesseract_version())
    except Exception:
        return False
