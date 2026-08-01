"""Small collection of settings used by the desktop assistant.

The coordinates are deliberately kept in one place because PyAutoGUI positions
depend on the display resolution and browser layout.
"""

OCR_MATCH_THRESHOLD = 70
LISTEN_TIMEOUT_SECONDS = 5
PHRASE_TIME_LIMIT_SECONDS = 10
AMBIENT_NOISE_DURATION_SECONDS = 0.5

URLS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "calendar": "https://calendar.google.com",
}

# These positions are calibrated for the original development machine.
POSITIONS = {
    "google_search": (638, 479),
    "whatsapp_search": (206, 195),
    "browser_address_bar": (218, 66),
}
