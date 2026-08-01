# VAANI : Voice Activated Assistance and Navigation Interface

VoiceAssist is a macOS-focused Python voice assistant for navigating Google
Chrome. It combines speech recognition, native text-to-speech, keyboard/browser
automation, and OCR-based visible-text matching.

The project deliberately keeps its interview demo small: YouTube and Chrome
navigation are the primary flow, while WhatsApp messages require confirmation
and Calendar events open as reviewable drafts.

## Features

- Continuous speech-command loop with spoken responses.
- Contextual and interactive command help.
- Chrome navigation: scrolling, history, reload, tabs, page position, and URL copy.
- Same-tab navigation by default, with explicit new-tab and new-window commands.
- YouTube search, visible-title selection, playback, seeking, mute, and full screen.
- Temporary YouTube muting while the assistant listens, preventing video audio
  from being recognized as a command.
- WhatsApp Web contact confirmation, spoken contact correction/spelling, message
  read-back, and confirmation before sending.
- URL-based Google search without resolution-dependent mouse coordinates.
- Dated Google Calendar event drafts with a pre-filled title and manual review
  before save.
- Confirmed Calendar saving through the visible Save button.
- Tests for command routing and safety-sensitive behavior.

## Safety and reliability

- WhatsApp never types before the chats screen and contact are verified.
- Messages are read back and require confirmation before Enter is pressed.
- Calendar events are opened as drafts; VoiceAssist does not claim they were saved.
- Exiting YouTube, Google, WhatsApp, or Calendar asks whether to close the tab.
- OCR clicks are restricted to the active Chrome window.

## Requirements

- macOS with Google Chrome
- Python 3.13 (the tested interview environment)
- A working microphone and internet connection
- Chrome signed in to WhatsApp Web/Google services when those flows are used

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

On Apple Silicon, install a native FLAC executable for SpeechRecognition if
audio conversion reports `Bad CPU type in executable`:

```bash
conda install -c conda-forge libflac
```

Grant the terminal or VS Code these macOS permissions when requested:

- Microphone
- Accessibility
- Screen Recording

## Run

```bash
conda activate interview
python voice.py
```

VoiceAssist measures ambient noise once, announces that it is ready, and then
waits for commands.

## Useful commands

| Context | Example command | Result |
| --- | --- | --- |
| Assistant | `list commands` | Prints the complete guide |
| Assistant | `help youtube` | Explains YouTube commands |
| Assistant | `quit assistant` | Terminates VoiceAssist |
| Chrome | `scroll down` | Scrolls the active page |
| Chrome | `go back` | Uses Chrome history |
| Chrome | `dismiss popup` | Presses Escape to dismiss the active popup |
| YouTube | `search Python DSA tutorial` | Opens YouTube results |
| YouTube | `open DSA using Python` | Clicks matching visible text |
| YouTube | `pause` | Toggles playback |
| YouTube | `forward` / `back` | Seeks ten seconds |
| YouTube | `exit youtube` | Leaves mode and asks about closing the tab |
| WhatsApp | `change contact to Riya` | Corrects the recognized contact |
| WhatsApp | `spell contact` | Accepts a letter-by-letter contact name |
| WhatsApp | `text where are you` | Types, reads back, then asks before sending |
| Google | `search Java collections` | Opens an encoded Google results URL |
| Calendar | `create event Cognizant interview` | Asks for a date, then opens a draft |
| Calendar | `save it` | Confirms, then clicks the visible Save button |

Sites use the active Chrome tab unless the opening command includes `in a new
tab` or `in a new window`.

## Command help

- Say `help` inside a mode for a short contextual overview.
- Say `detailed help` to hear commands one at a time.
- During detailed help, say `next`, `repeat`, or `stop help`.
- Ask about one command directly, for example `explain forward command`.

## Tests

Run the full suite:

```bash
python -m unittest discover -s tests -v
```

Run static validation:

```bash
python -m py_compile voice.py command_guide.py
ruff check voice.py command_guide.py tests
```

## Project structure

- `voice.py` — assistant loop, speech, Chrome controls, and application modes.
- `command_guide.py` — data-driven contextual command documentation.
- `tests/` — mocked unit tests that do not control the developer's live Chrome.

## Limitations

- Speech recognition uses Google's online recognizer and therefore needs internet.
- OCR can only select text currently visible in the active Chrome window.
- Website layout changes may affect OCR-based WhatsApp interaction.
- The Calendar flow requires a spoken date and opens an all-day draft; the user
  reviews its details and saves it.
- Automated tests validate command logic with mocks. Microphone and live website
  behavior must still be checked on the interview laptop before the demo.
