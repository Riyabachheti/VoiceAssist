"""VoiceAssist: a small voice-controlled desktop automation prototype."""

import os
import tempfile
import time
import webbrowser
from pathlib import Path

import docx
import easyocr
import pyautogui
import pyttsx3
import speech_recognition as sr
from fuzzywuzzy import fuzz
from PyPDF2 import PdfReader

from assistant_utils import contains_any, get_latest_supported_file, select_best_ocr_match
from config import (
    AMBIENT_NOISE_DURATION_SECONDS,
    LISTEN_TIMEOUT_SECONDS,
    OCR_MATCH_THRESHOLD,
    PHRASE_TIME_LIMIT_SECONDS,
    POSITIONS,
    URLS,
)

engine = pyttsx3.init()
recognizer = sr.Recognizer()
ocr_reader = None


def speak(text: str) -> None:
    """Print and speak a response."""
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()


def listen(prompt: str = "") -> str:
    """Listen for one command and return normalized text.

    A timeout prevents the application from waiting forever when no one speaks.
    """
    if prompt:
        speak(prompt)

    try:
        with sr.Microphone() as source:
            print("🎙️ Listening...")
            recognizer.adjust_for_ambient_noise(
                source, duration=AMBIENT_NOISE_DURATION_SECONDS
            )
            audio = recognizer.listen(
                source,
                timeout=LISTEN_TIMEOUT_SECONDS,
                phrase_time_limit=PHRASE_TIME_LIMIT_SECONDS,
            )
    except sr.WaitTimeoutError:
        speak("I did not hear anything. Please try again.")
        return ""
    except (OSError, AttributeError) as error:
        print(f"Microphone error: {error}")
        speak("I could not access the microphone.")
        return ""

    try:
        command = recognizer.recognize_google(audio).strip().lower()
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
    except sr.RequestError as error:
        print(f"Speech recognition error: {error}")
        speak("The speech recognition service is unavailable.")
    return ""


def voice_to_type(prompt: str = "What should I type?") -> bool:
    """Dictate text into the currently focused input."""
    text = listen(prompt)
    if not text:
        return False
    speak("Typing now.")
    time.sleep(1)
    pyautogui.write(text, interval=0.02)
    return True


def read_file_aloud(file_path: str) -> None:
    """Extract and speak text from a TXT, PDF, or DOCX document."""
    path = Path(file_path)
    try:
        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8")
        elif path.suffix.lower() == ".pdf":
            text = " ".join(page.extract_text() or "" for page in PdfReader(path).pages)
        elif path.suffix.lower() == ".docx":
            document = docx.Document(path)
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        else:
            speak("I can only read text, PDF, or Word files.")
            return
    except (OSError, ValueError) as error:
        print(f"File reading error: {error}")
        speak("I could not read that file.")
        return

    cleaned_text = " ".join(text.split())
    speak(cleaned_text if cleaned_text else "The document does not contain readable text.")


def get_ocr_reader():
    """Create the relatively expensive OCR reader only when it is first used."""
    global ocr_reader
    if ocr_reader is None:
        speak("Preparing screen text recognition.")
        ocr_reader = easyocr.Reader(["en"], gpu=False)
    return ocr_reader


def click_by_title(target_title: str) -> bool:
    """Use OCR and fuzzy matching to click visible text resembling a title."""
    if not target_title:
        speak("No title was provided.")
        return False

    screenshot_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            screenshot_path = temp_file.name
        pyautogui.screenshot().save(screenshot_path)
        results = get_ocr_reader().readtext(screenshot_path)
        match = select_best_ocr_match(target_title, results, fuzz.token_set_ratio)
    except Exception as error:  # GUI/OCR libraries expose several platform errors.
        print(f"Screen recognition error: {error}")
        speak("I could not inspect the screen.")
        return False
    finally:
        if screenshot_path:
            try:
                os.unlink(screenshot_path)
            except OSError:
                pass

    if match is None or match[2] < OCR_MATCH_THRESHOLD:
        speak("I could not find matching text on the screen.")
        return False

    bounding_box, detected_text, score = match
    top_left, _top_right, bottom_right, _bottom_left = bounding_box
    center_x = int((top_left[0] + bottom_right[0]) / 2)
    center_y = int((top_left[1] + bottom_right[1]) / 2)
    pyautogui.click(center_x, center_y)
    print(f"Clicked '{detected_text}' with match score {score}.")
    speak("Clicking the best match.")
    return True


def handle_browser_navigation(command: str) -> bool:
    """Handle navigation shared by the Google, YouTube, and WhatsApp modes."""
    if contains_any(command, ["scroll down"]):
        pyautogui.scroll(-1000)
    elif contains_any(command, ["scroll up"]):
        pyautogui.scroll(1000)
    elif contains_any(command, ["go back"]):
        pyautogui.hotkey("alt", "left")
    elif contains_any(command, ["go forward"]):
        pyautogui.hotkey("alt", "right")
    elif contains_any(command, ["close tab"]):
        pyautogui.hotkey("ctrl", "w")
    else:
        return False
    speak("Done.")
    return True


def youtube_mode() -> None:
    """Process commands while YouTube is active."""
    while True:
        command = listen("YouTube is ready. What should I do?")
        if not command:
            continue
        if contains_any(command, ["stop", "bye", "leave youtube"]):
            speak("Leaving YouTube mode.")
            return
        if contains_any(command, ["search", "find"]):
            pyautogui.click(*POSITIONS["youtube_search"])
            if voice_to_type("What should I search for?"):
                if contains_any(listen("Should I submit the search?"), ["yes", "ok"]):
                    pyautogui.press("enter")
        elif contains_any(command, ["click", "video"]):
            click_by_title(listen("Which title should I click?"))
        elif contains_any(command, ["play", "pause"]):
            pyautogui.press("space")
        elif contains_any(command, ["mute", "sound"]):
            pyautogui.press("m")
        elif contains_any(command, ["full screen", "fullscreen"]):
            pyautogui.press("f")
        elif command == "forward":
            pyautogui.press("right")
        elif command == "back":
            pyautogui.press("left")
        elif not handle_browser_navigation(command):
            speak("I don't recognize that YouTube command.")


def google_mode(initial_search: bool = True) -> None:
    """Process Google search and navigation commands."""
    if initial_search:
        time.sleep(2)
        pyautogui.click(*POSITIONS["google_search"])
        if voice_to_type("What should I search for?"):
            if contains_any(listen("Should I submit the search?"), ["yes", "ok"]):
                pyautogui.press("enter")

    while True:
        command = listen("Google is ready. What should I do?")
        if not command:
            continue
        if contains_any(command, ["stop", "bye", "leave google"]):
            speak("Leaving Google mode.")
            return
        if contains_any(command, ["search", "find", "search again"]):
            pyautogui.hotkey("ctrl", "l")
            if voice_to_type("What should I search for?"):
                pyautogui.press("enter")
        elif contains_any(command, ["click", "link"]):
            click_by_title(listen("Which visible title should I click?"))
        elif not handle_browser_navigation(command):
            speak("I don't recognize that Google command.")


def whatsapp_mode() -> None:
    """Send confirmed text messages through WhatsApp Web."""
    time.sleep(8)
    contact = listen("Who do you want to message?")
    if not contact:
        speak("No contact was selected.")
        return
    pyautogui.click(*POSITIONS["whatsapp_search"])
    pyautogui.write(contact, interval=0.03)
    time.sleep(2)
    pyautogui.press("enter")
    speak(f"Selected {contact}.")

    while True:
        command = listen("What should I do in WhatsApp?")
        if not command:
            continue
        if contains_any(command, ["stop", "bye", "leave whatsapp"]):
            speak("Leaving WhatsApp mode.")
            return
        if contains_any(command, ["message", "send"]):
            message = listen("What message should I type?")
            if not message:
                continue
            pyautogui.write(message, interval=0.03)
            confirmation = listen("Should I send this message?")
            if contains_any(confirmation, ["yes", "send", "ok"]):
                pyautogui.press("enter")
                speak("Message sent.")
            else:
                pyautogui.hotkey("ctrl", "a")
                pyautogui.press("backspace")
                speak("Message cancelled.")
        elif contains_any(command, ["change contact", "new contact"]):
            speak("Leaving this chat. Say open WhatsApp to select another contact.")
            return
        elif not handle_browser_navigation(command):
            speak("I don't recognize that WhatsApp command.")


def calendar_mode() -> None:
    """Create a basic Google Calendar task using keyboard navigation."""
    time.sleep(4)
    speak("Calendar is open. The task form must be visible for this prototype.")
    title = listen("What is the task title?")
    if not title:
        speak("Task creation cancelled.")
        return
    pyautogui.write(title, interval=0.03)
    if not contains_any(listen("Should I save this task?"), ["yes", "save", "ok"]):
        speak("Task creation cancelled.")
        return
    pyautogui.hotkey("ctrl", "enter")
    speak("The task was submitted.")


def execute(command: str) -> bool:
    """Dispatch a top-level command. Return False when the app should exit."""
    if contains_any(command, ["open youtube"]):
        speak("Opening YouTube.")
        webbrowser.open(URLS["youtube"])
        youtube_mode()
    elif contains_any(command, ["open google"]):
        speak("Opening Google.")
        webbrowser.open(URLS["google"])
        google_mode()
    elif contains_any(command, ["open whatsapp"]):
        speak("Opening WhatsApp Web.")
        webbrowser.open(URLS["whatsapp"])
        whatsapp_mode()
    elif contains_any(command, ["reminder", "open calendar"]):
        speak("Opening Google Calendar.")
        webbrowser.open(URLS["calendar"])
        calendar_mode()
    elif contains_any(command, ["type something", "write something"]):
        voice_to_type()
    elif contains_any(command, ["read latest file", "read downloads"]):
        latest_file = get_latest_supported_file(str(Path.home() / "Downloads"))
        if latest_file:
            speak(f"Reading {Path(latest_file).name}.")
            read_file_aloud(latest_file)
        else:
            speak("I could not find a supported document in Downloads.")
    elif contains_any(command, ["close tab"]):
        pyautogui.hotkey("ctrl", "w")
        speak("Tab closed.")
    elif contains_any(command, ["copy link", "copy url"]):
        pyautogui.click(*POSITIONS["browser_address_bar"], clicks=3, interval=0.1)
        pyautogui.hotkey("ctrl", "c")
        speak("URL copied.")
    elif contains_any(command, ["exit", "stop assistant", "goodbye"]):
        speak("Goodbye!")
        return False
    else:
        speak("Sorry, I don't recognize that command.")
    return True


def main() -> None:
    """Run the assistant until the user asks it to exit."""
    sleeping = False
    speak("Voice assistant ready. Say a command.")

    while True:
        command = listen("What can I do for you?")
        if not command:
            continue
        if sleeping:
            if contains_any(command, ["wake up", "resume"]):
                sleeping = False
                speak("I'm awake again.")
            continue
        if contains_any(command, ["sleep", "wait"]):
            sleeping = True
            speak("Going to sleep. Say wake up when you need me.")
            continue
        if not execute(command):
            return


if __name__ == "__main__":
    main()
