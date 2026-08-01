# VoiceAssist interview notes

## 20-second introduction

VoiceAssist is a Python desktop-automation prototype that converts spoken
commands into browser and keyboard actions. It combines speech recognition,
text-to-speech, PyAutoGUI, OCR, and fuzzy matching, and can also extract and read
text from PDF, Word, and text documents.

## 60-second explanation

I built VoiceAssist to explore hands-free desktop interaction. The microphone
input is converted to lowercase text using Google's speech-recognition service.
A rule-based dispatcher sends the command to an application-specific workflow,
and PyAutoGUI performs the mouse or keyboard action. The most interesting part
is screen-aware clicking: the assistant captures a temporary screenshot,
EasyOCR returns visible text with bounding boxes, and fuzzy matching selects the
text closest to the spoken title. If its score crosses a threshold, the
assistant clicks the centre of that box. It can also extract and speak text from
TXT, PDF, and DOCX files. The current version is a prototype because a few
browser actions still use fixed coordinates. For production I would replace
those actions with browser locators and add broader mocked integration tests.

## Resume entry

**Voice-Controlled Desktop Assistant | Python**

- Built a voice-controlled desktop automation prototype integrating speech
  recognition, text-to-speech, OCR, and keyboard/mouse control.
- Implemented fuzzy matching over OCR-detected screen text to locate and click
  visible UI elements using spoken titles.
- Added text extraction and read-aloud support for TXT, PDF, and DOCX files.
- Improved reliability with speech timeouts, error handling, temporary-file
  cleanup, confirmation for messages, configuration, and unit tests.

## Likely questions

### Why fuzzy matching?

Speech recognition and OCR may produce slightly different strings. Fuzzy
matching tolerates small spelling, spacing, and word-order differences.

### Why `token_set_ratio`?

It compares the important word tokens and is relatively tolerant of word order
and extra words in a long page title.

### Why is the OCR threshold 70?

It is currently a configurable heuristic. In a mature version I would create a
labelled set of spoken and OCR strings, measure false clicks and missed clicks,
and select the threshold from those results.

### Is this an AI project?

It integrates trained speech-recognition and OCR models, while the command
orchestration itself is intentionally rule-based. I did not train a new model.

### What is the biggest limitation?

Fixed screen coordinates are dependent on display resolution, browser layout,
and website changes. OCR-based title clicking is more adaptable, but also
depends on visible text quality.

### Why not use Selenium or Playwright?

The project began as a desktop-wide automation experiment, so PyAutoGUI could
control both browser and non-browser inputs. For production browser workflows,
I would use Playwright locators and retain PyAutoGUI only where native desktop
control was necessary.

### What did you improve when revisiting the project?

I removed duplicate and unused code, corrected command and loop bugs, added
speech timeouts and microphone error handling, made OCR screenshots temporary,
added message confirmation, moved settings into one place, added tests for pure
logic, and documented the design and limitations honestly.

### How would you test microphone and GUI functionality?

I would separate external interfaces behind small adapters, mock them in unit
tests, and use a limited set of manual end-to-end scenarios on supported
platforms. The pure command, file, and match-selection logic is already tested
without moving a real mouse.

## Demo checklist

- Use the tested screen resolution and browser zoom.
- Confirm microphone, accessibility, and screen-recording permissions.
- Close private tabs and disable notifications.
- Run the YouTube search and OCR-click flow once before the interview.
- Keep a 60–90 second backup recording ready.
- Do not make code changes on Monday morning.

## Honest scope statement

VoiceAssist is a learning and accessibility-oriented prototype. Spend Smart can
remain the primary backend project in the interview; VoiceAssist is a smaller
integration project that demonstrates Python, external libraries, automation,
error handling, and the ability to revisit and improve earlier code.
