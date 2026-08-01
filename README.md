# VoiceAssist

VoiceAssist is a Python desktop-automation prototype controlled with spoken
commands. It combines speech recognition, text-to-speech, OCR, fuzzy string
matching, document extraction, and mouse/keyboard automation.

The project explores a simple accessibility idea: letting a user operate common
browser tasks and hear local documents without relying entirely on a mouse and
keyboard.

## What it can do

- Recognize commands spoken through a microphone.
- Speak confirmations and errors aloud.
- Open and control basic YouTube and Google workflows.
- Dictate text into the currently focused input.
- Detect visible screen text with EasyOCR and click the closest fuzzy match.
- Read text from `.txt`, `.pdf`, and `.docx` documents.
- Send a WhatsApp Web message only after spoken confirmation.
- Enter and leave a sleep mode.

WhatsApp Web and Google Calendar support are experimental because those pages
change frequently and some actions still depend on screen coordinates.

## Architecture

```text
Microphone
    |
    v
Google Speech Recognition
    |
    v
Rule-based command dispatcher
    |--------------------|--------------------|
    v                    v                    v
Browser/GUI actions   OCR + fuzzy match   Document extraction
    |                    |                    |
    |--------------------|--------------------|
                         v
                 Spoken confirmation
```

The implementation is intentionally small:

```text
voice.py             Main loop, speech, command flows, and desktop actions
assistant_utils.py   Pure file, command, and OCR-selection utilities
config.py            URLs, timing values, OCR threshold, and screen positions
tests/                Fast tests that do not use a real microphone or mouse
```

## How OCR-based clicking works

When the user asks to click a visible title, VoiceAssist:

1. Saves a temporary screenshot.
2. Uses EasyOCR to detect text and bounding boxes.
3. Compares each detected string with the spoken title using fuzzy matching.
4. Selects the highest-scoring result.
5. Clicks the centre of its bounding box if the score meets the configured
   threshold.
6. Deletes the temporary screenshot.

This is the most important technical workflow in the project. Fuzzy matching
helps when speech recognition and OCR produce strings that are similar but not
identical.

## Requirements

- Python 3.9 or newer
- A microphone and speakers
- Internet access for Google Speech Recognition
- OS permission for microphone, accessibility, and screen capture
- An active graphical desktop session

## Installation

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/Riyabachheti/VoiceAssist.git
cd VoiceAssist
python -m venv .venv
```

Activate it:

```bash
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the Python packages:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Microphone dependency

`SpeechRecognition` uses PyAudio for microphone input. Its installation depends
on the operating system.

macOS:

```bash
brew install portaudio
pip install PyAudio
```

Debian/Ubuntu:

```bash
sudo apt-get install portaudio19-dev
pip install PyAudio
```

On Windows, a compatible PyAudio wheel may be required.

EasyOCR also installs PyTorch. The first OCR operation can take longer because
the OCR reader and its models are initialized at that point.

## Run

```bash
python voice.py
```

Example top-level commands:

```text
open youtube
open google
open whatsapp
open calendar
type something
copy link
close tab
sleep
wake up
stop assistant
```

## Recommended demo

The most representative demo is:

1. Run `python voice.py`.
2. Say **open YouTube**.
3. Say **search** and dictate a query.
4. Say **click** and speak part of a visible video title.
5. VoiceAssist captures the screen, finds the closest OCR match, and clicks it.

Before demonstrating, use the same display resolution, browser size, and zoom
level used during testing. A short screen recording is recommended as a backup
when presenting in an environment with uncertain microphone or network access.

## Tests

The utility tests deliberately avoid real microphone and GUI operations:

```bash
python -m unittest discover -s tests -v
```

They cover supported file types, latest-file selection, normalized command
matching, and selection of the best OCR result.

## Safety and reliability improvements

- Listening has both a start timeout and a phrase-length limit.
- Microphone and recognition failures receive understandable feedback.
- OCR screenshots are deleted after processing.
- Empty contact names and titles are rejected.
- WhatsApp messages require confirmation before being sent.
- Constants and screen positions are kept in `config.py`.
- OCR is initialized only when screen recognition is first requested.

## Known limitations

- Google Speech Recognition requires an internet connection.
- PyAutoGUI controls whichever window currently has focus.
- Several browser actions depend on coordinates calibrated for the original
  machine and can break at other resolutions or after website redesigns.
- OCR can misread stylized, small, or low-contrast text.
- Scanned PDFs may not contain extractable text.
- This is a rule-based automation prototype, not a general conversational AI.

## Future improvements

- Replace coordinate-based browser actions with Playwright or Selenium locators.
- Add a calibration flow for screen positions.
- Add structured logging and more mocked tests.
- Support offline speech recognition.
- Introduce a command registry if the number of commands grows substantially.

The project intentionally avoids these additions for now so its core workflow
remains small, understandable, and easy to demonstrate.

## Technology stack

Python, SpeechRecognition, pyttsx3, PyAutoGUI, EasyOCR, FuzzyWuzzy, PyPDF2,
python-docx, Pillow, and `unittest`.
