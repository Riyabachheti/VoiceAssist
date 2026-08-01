# VoiceAssist

**Description**

VoiceAssist is a desktop voice-controlled assistant written in Python. It listens for spoken commands (via microphone), speaks back using text‑to‑speech, automates desktop interactions (clicking, typing, scrolling) and can read local text/PDF/Word files aloud. It also includes specific flows for YouTube, Google Search and WhatsApp Web automation.

## Features

* Microphone-based speech recognition and voice responses (speech-to-text / text-to-speech).
* Desktop automation using mouse/keyboard (via `pyautogui`): click, type, scroll, hotkeys.
* OCR-based on-screen text detection (via `easyocr`) with fuzzy matching to click items by title.
* Read aloud local files: `.txt`, `.pdf`, `.docx` using `PyPDF2` and `python-docx`.
* Basic flows for interacting with:

  * YouTube (search, click video, play/pause, mute, navigation)
  * Google Search (type + optional enter)
  * WhatsApp Web (select contact, type/send messages, attach files)
  * Google Calendar (create reminders/tasks — partial implementation)
* Sleep/wake mode and a simple command dispatcher.

---

## Quick demo (what to say)

Run the assistant and say short commands like:

* `open youtube` — opens YouTube and accepts follow-up voice commands.
* `open google` — opens Google and can type a search.
* `open whatsapp` — opens WhatsApp Web (scan QR with your phone first).
* `reminder` — opens Google Calendar to create a reminder/task.
* `type something` or `write something` — voice-to-type into the active input.
* `close tab`, `copy link`, `exit`, `sleep`, `wake up` — control assistant or browser.
* While inside flows you can say `search`, `click <title>`, `scroll down`, `play`, `pause`, `mute`, etc.

---

## Installation

> These steps assume you have Python 3.8+ installed and a working microphone and speakers.

1. **Clone the repository**

```bash
git clone https://github.com/Riyabachheti/VoiceAssist.git
cd VoiceAssist
```

2. **Create and activate a virtual environment (recommended)**

```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

3. **Install Python dependencies**

A minimal set of packages used in the project:

```bash
pip install SpeechRecognition pyttsx3 pyautogui easyocr fuzzywuzzy PyPDF2 python-docx pillow
```

> **Important notes**:
>
> * `easyocr` requires **PyTorch**. Install a CPU/GPU-compatible PyTorch build first following the official instructions for your platform, for example:
>
>   ```bash
>   # example for CPU-only (check https://pytorch.org for the correct command for your system)
>   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
>   pip install easyocr
>   ```
>
> * **Microphone support**: `SpeechRecognition` typically depends on `PyAudio`. Installing `PyAudio` can be system-dependent:
>
>   * Windows: `pip install pipwin && pipwin install pyaudio`
>   * macOS: `brew install portaudio && pip install pyaudio`
>   * Linux (Debian/Ubuntu): `sudo apt-get install portaudio19-dev && pip install pyaudio`
>
> * On some systems `pyautogui` may require additional OS-level accessibility permissions (macOS) or running in an active desktop session (Linux X11). It may not work on Wayland without extra setup.

---

## Running the assistant

Start the assistant from the repository root. The main script in this repo is `voice.py` (the file with `if __name__ == "__main__":`). Run it with:

```bash
python voice.py
```

When it starts the assistant will say it is ready and repeatedly prompt: "What can I do for you?" — speak one of the supported commands.

### Example flow

1. `open youtube` — the assistant opens YouTube in your default browser.
2. Say `search` or `find` and then speak your query — the assistant types it into the search bar and optionally presses search if you confirm.
3. Say `click` and then speak a part of the video title — the assistant uses an OCR snapshot + fuzzy matching to try to click the matching title.
