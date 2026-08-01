"""Pure utility functions for VoiceAssist.

Keeping these functions free from microphone and GUI dependencies makes them
easy to understand and unit test.
"""

from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def is_supported_file(path: str) -> bool:
    """Return whether *path* has a supported document extension."""
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def get_latest_supported_file(directory: str) -> Optional[str]:
    """Return the most recently modified supported file in *directory*."""
    folder = Path(directory).expanduser()
    if not folder.is_dir():
        return None

    files = [path for path in folder.iterdir() if path.is_file() and is_supported_file(str(path))]
    if not files:
        return None
    return str(max(files, key=lambda path: path.stat().st_mtime))


def contains_any(command: str, phrases: Iterable[str]) -> bool:
    """Return True when any phrase occurs in a normalized command."""
    normalized = command.strip().lower()
    return any(phrase.lower() in normalized for phrase in phrases)


def select_best_ocr_match(
    target: str,
    results: Sequence[Tuple[object, str, float]],
    scorer,
):
    """Return ``(bounding_box, text, score)`` for the best OCR text match."""
    if not target.strip():
        return None

    best = None
    for bounding_box, detected_text, _confidence in results:
        score = scorer(target.lower(), detected_text.lower())
        if best is None or score > best[2]:
            best = (bounding_box, detected_text, score)
    return best
