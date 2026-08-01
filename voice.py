import speech_recognition as sr
import pyttsx3
import pyautogui
import webbrowser
import time
import subprocess
import sys
import warnings
from datetime import date, timedelta
from urllib.parse import quote_plus, urlencode
import easyocr
from fuzzywuzzy import fuzz
import re

from command_guide import (
    COMMANDS,
    category_help_request,
    format_category,
    format_full_guide,
    help_response,
    is_help_request,
)

reader = None
IS_MACOS = sys.platform == "darwin"
engine = None if IS_MACOS else pyttsx3.init()
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8
recognizer.phrase_threshold = 0.2

# YouTube is muted only while the assistant is speaking/listening. This keeps
# video dialogue out of speech recognition without muting macOS narration.
youtube_muted_by_user = False
youtube_temporarily_muted = False


def provide_command_help(command, context=None):
    """Speak targeted help and print the full guide for broad requests."""
    normalized = " ".join(command.lower().split())
    if normalized.startswith("detailed help"):
        category = category_help_request("help", context=context)
        if category:
            run_interactive_help(category)
        else:
            speak("Say detailed help while inside an application mode.")
        return
    if context is None and normalized in (
        "help",
        "commands",
        "list commands",
        "show commands",
        "what can you do",
        "what commands can i use",
    ):
        print("\n" + format_full_guide() + "\n")
    response = help_response(command, context=context)
    speak(response)


def run_interactive_help(category):
    """Read category commands one at a time with an exit between entries."""
    entries = COMMANDS[category]
    print("\n" + format_category(category) + "\n")
    speak(
        f"I found {len(entries)} {category} command groups. "
        "I will read them one at a time. After each one, say next, repeat, "
        "or stop help."
    )

    index = 0
    while index < len(entries):
        entry = entries[index]
        speak(
            f"Command {index + 1} of {len(entries)}. {entry['name']}. "
            f"Say: {entry['say']}. {entry['description']}"
        )
        speak("Say next, repeat, or stop help.")
        choice = listen()

        if any(
            phrase in choice
            for phrase in (
                "stop help",
                "exit help",
                "found it",
                "done",
                "stop",
                "exit",
            )
        ):
            speak("Leaving command help.")
            return
        if "repeat" in choice:
            continue
        if "next" in choice or "continue" in choice:
            index += 1
            continue
        speak("Please say next, repeat, or stop help.")

    speak("That was the last command. Leaving command help.")


def speak(text):
    print("Assistant:", text)
    spoken_text = " ".join(str(text).split())
    if IS_MACOS:
        try:
            subprocess.run(["/usr/bin/say", spoken_text], check=False)
            return
        except OSError as error:
            print("macOS speech error:", error)
    if engine is not None:
        engine.say(spoken_text)
        engine.runAndWait()


def calibrate_microphone():
    """Measure room noise once instead of recalibrating before every command."""
    print("Calibrating microphone for ambient noise...")
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
    except (OSError, AttributeError) as error:
        print("Microphone calibration error:", error)


# Capture voice command
def listen(timeout=7, phrase_time_limit=12, report_errors=True):
    try:
        with sr.Microphone() as source:
            print("🎙️ Listening...")
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
            )
    except sr.WaitTimeoutError:
        if report_errors:
            speak("I did not hear anything. Please try again.")
        return ""
    except (OSError, AttributeError) as error:
        print("Microphone error:", error)
        speak("I could not access the microphone.")
        return ""

    try:
        command = recognizer.recognize_google(audio).strip().lower()
        print("You said:", command)
        return command
    except sr.UnknownValueError:
        if report_errors:
            speak("Sorry, I didn't catch that.")
    except sr.RequestError as error:
        print("Speech recognition error:", error)
        speak("Speech recognition API unavailable.")
    except OSError as error:
        print("Audio conversion error:", error)
        speak("I could not convert the recorded audio.")
    return ""


def listen_for_short_response(retries=2, phrase_time_limit=8, ready_prompt="Ready"):
    """Clearly mark when recording begins and retry short answers once."""
    for attempt in range(retries):
        if ready_prompt != "Ready":
            speak(ready_prompt)
        speak("Ready")
        response = listen(
            timeout=6,
            phrase_time_limit=phrase_time_limit,
            report_errors=False,
        )
        if response:
            return response
        if attempt < retries - 1:
            speak("I did not hear that. Please answer once more after Ready.")
    return ""


# Voice-to-type functionality
def voice_to_type():
    speak("What should I type?")
    text = listen()
    time.sleep(0.5)
    if not text:
        speak("No text was detected. Please say search and try again.")
        return False
    speak("Typing now.")
    time.sleep(2)
    pyautogui.typewrite(text)
    return True


def chrome_disposition_from_command(command):
    """Choose same tab by default unless the user explicitly requests otherwise."""
    normalized = " ".join(command.lower().split())
    if "new window" in normalized:
        return "new_window"
    if "new tab" in normalized:
        return "new_tab"
    return "same_tab"


def escape_applescript_string(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def open_in_chrome(url, disposition="same_tab"):
    """Load a URL in the active Chrome tab unless another target is requested."""
    if sys.platform == "darwin":
        safe_url = escape_applescript_string(url)
        if disposition == "new_window":
            navigation = (
                "make new window\n"
                f'set URL of active tab of front window to "{safe_url}"'
            )
        elif disposition == "new_tab":
            navigation = (
                f"make new tab at end of tabs of front window with properties "
                f'{{URL:"{safe_url}"}}\n'
                "set active tab index of front window to count of tabs of front window"
            )
        else:
            navigation = f'set URL of active tab of front window to "{safe_url}"'
        window_guard = (
            ""
            if disposition == "new_window"
            else "if (count of windows) = 0 then make new window\n"
        )
        script = (
            'tell application "Google Chrome"\n'
            "activate\n"
            f"{window_guard}"
            f"{navigation}\n"
            "end tell"
        )
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            time.sleep(4)
            return True
        print("Chrome open error:", result.stderr.strip())
    webbrowser.open(url)
    time.sleep(4)
    return True


def activate_chrome():
    """Bring Chrome to the foreground before sending navigation keys."""
    if sys.platform == "darwin":
        subprocess.run(
            ["/usr/bin/open", "-a", "Google Chrome"],
            check=False,
        )
        time.sleep(0.5)


def get_ocr_reader():
    """Load EasyOCR only when a screen-reading command actually needs it."""
    global reader
    if reader is None:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*torch.quantize_per_tensor.*deprecated.*",
                category=UserWarning,
            )
            reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return reader


def read_ocr(image_path):
    """Run OCR while hiding only known harmless PyTorch MPS warnings."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*pin_memory.*not supported on MPS.*",
            category=UserWarning,
        )
        return get_ocr_reader().readtext(image_path)


def get_youtube_search_query(command):
    """Extract an optional query from commands such as 'search Python'."""
    normalized = command.strip().lower()
    for prefix in ("search for ", "search ", "find "):
        if normalized.startswith(prefix):
            return strip_chrome_disposition_suffix(normalized[len(prefix) :].strip())
    return ""


def strip_chrome_disposition_suffix(text):
    """Remove navigation instructions from spoken search/title content."""
    normalized = " ".join(text.lower().split())
    for suffix in (
        " in a new window",
        " in new window",
        " in a new tab",
        " in new tab",
    ):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)].strip()
    return normalized


def get_google_search_query(command):
    """Extract a query from commands such as 'search Google for Java OOP'."""
    normalized = command.strip().lower()
    for prefix in (
        "search google for ",
        "search google ",
        "search for ",
        "search ",
        "find ",
    ):
        if normalized.startswith(prefix):
            return strip_chrome_disposition_suffix(normalized[len(prefix) :].strip())
    return ""


def get_visible_target(command):
    """Extract text to open from commands such as 'open Python tutorial'."""
    normalized = command.strip().lower()
    for prefix in (
        "open video ",
        "click video ",
        "play video ",
        "open ",
        "click ",
        "select ",
    ):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return ""


def is_visible_open_command(command):
    """Return whether a command asks to open visible text on the page."""
    normalized = command.strip().lower()
    if normalized in ("open", "click", "video", "open video", "click video"):
        return True
    return normalized.startswith(
        ("open video ", "click video ", "play video ", "open ", "click ", "select ")
    )


def chrome_hotkey(*keys):
    """Activate Chrome before sending a keyboard shortcut."""
    activate_chrome()
    pyautogui.hotkey(*keys)


def run_chrome_applescript(command):
    """Run a Chrome command and return (success, output_or_error)."""
    if not IS_MACOS:
        return False, "Chrome scripting is only configured for macOS."
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, result.stdout.strip()


def send_key_to_chrome(key_code):
    """Activate Chrome and send a macOS hardware key code via System Events."""
    if not IS_MACOS:
        return False, "System Events scrolling is only configured for macOS."
    script = (
        'tell application "Google Chrome" to activate\n'
        "delay 0.3\n"
        'tell application "System Events"\n'
        f"key code {key_code}\n"
        "end tell"
    )
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, ""


def get_active_chrome_url():
    """Return the current Chrome tab URL, or an empty string on failure."""
    success, output = run_chrome_applescript(
        'tell application "Google Chrome" to get URL of active tab of front window'
    )
    return output if success else ""


def is_affirmative(response):
    words = set(re.findall(r"[a-z]+", response.lower()))
    return bool(words & {"yes", "yeah", "yep", "sure", "okay", "ok"})


def is_negative(response):
    words = set(re.findall(r"[a-z]+", response.lower()))
    return bool(words & {"no", "nope", "keep", "leave"})


def is_quit_assistant_command(command):
    normalized = " ".join(command.lower().split())
    return normalized in (
        "quit assistant",
        "close assistant",
        "exit assistant",
        "goodbye",
    )


def quit_assistant():
    speak("Goodbye!")
    raise SystemExit


def ask_to_close_active_tab(app_name):
    """Ask before closing the tab when leaving an application mode."""
    response = listen_for_short_response(
        ready_prompt=f"Close the {app_name} tab? Say yes or no."
    )
    if is_affirmative(response):
        return True
    if not is_negative(response):
        speak("I could not confirm yes, so I will leave the tab open.")
    return False


def close_active_chrome_tab():
    """Close only Chrome's active tab and report whether Chrome accepted it."""
    if IS_MACOS:
        success, error = run_chrome_applescript(
            'tell application "Google Chrome" to close active tab of front window'
        )
        if not success:
            print("Chrome close-tab error:", error)
        return success
    activate_chrome()
    pyautogui.hotkey("ctrl", "w")
    return True


def exit_chrome_mode(app_name):
    """Confirm optional tab closure, then leave the current command mode."""
    if ask_to_close_active_tab(app_name):
        if close_active_chrome_tab():
            speak(f"Closed the {app_name} tab.")
        else:
            speak(f"I could not close the {app_name} tab.")
    else:
        speak(f"Leaving the {app_name} tab open.")
    speak(f"Exiting {app_name} command mode.")
    return "exit"


def change_chrome_history(direction):
    """Move through Chrome history and verify that the URL changed."""
    before_url = get_active_chrome_url()
    action = "go back" if direction == "back" else "go forward"
    success, error = run_chrome_applescript(
        f'tell application "Google Chrome" to {action} active tab of front window'
    )
    if not success:
        print("Chrome navigation error:", error)
        return False
    time.sleep(1)
    after_url = get_active_chrome_url()
    return bool(before_url and after_url and before_url != after_url)


def handle_chrome_navigation(command):
    """Handle navigation commands shared by Chrome-based workflows."""
    normalized = command.strip().lower()
    command_key = "command" if IS_MACOS else "ctrl"

    if normalized == "scroll down":
        if IS_MACOS:
            success, error = send_key_to_chrome(121)
            if success:
                speak("Page down command accepted by Chrome")
            else:
                print("Chrome scroll error:", error)
                speak("Chrome could not scroll down")
        else:
            activate_chrome()
            pyautogui.press("pagedown")
            speak("Scrolling down")
    elif normalized == "scroll up":
        if IS_MACOS:
            success, error = send_key_to_chrome(116)
            if success:
                speak("Page up command accepted by Chrome")
            else:
                print("Chrome scroll error:", error)
                speak("Chrome could not scroll up")
        else:
            activate_chrome()
            pyautogui.press("pageup")
            speak("Scrolling up")
    elif normalized in ("go back", "previous page"):
        if IS_MACOS:
            if change_chrome_history("back"):
                speak("Went back to the previous page")
            else:
                speak("I could not go back. There may be no previous page.")
        else:
            chrome_hotkey("alt", "left")
            speak("Going back")
    elif normalized in ("go forward", "next page"):
        if IS_MACOS:
            if change_chrome_history("forward"):
                speak("Went forward to the next page")
            else:
                speak("I could not go forward. There may be no next page.")
        else:
            chrome_hotkey("alt", "right")
            speak("Going forward")
    elif normalized in ("refresh", "reload", "reload page"):
        if IS_MACOS:
            success, error = run_chrome_applescript(
                'tell application "Google Chrome" to reload active tab of front window'
            )
            if success:
                speak("Reload command accepted by Chrome")
            else:
                print("Chrome reload error:", error)
                speak("Chrome could not reload the page")
        else:
            chrome_hotkey(command_key, "r")
            speak("Reloading the page")
    elif normalized in ("new tab", "open new tab"):
        chrome_hotkey(command_key, "t")
        speak("Opening a new tab")
    elif normalized == "close tab":
        chrome_hotkey(command_key, "w")
        speak("Closing the tab")
    elif normalized in ("next tab", "switch tab"):
        chrome_hotkey("ctrl", "tab")
        speak("Moving to the next tab")
    elif normalized in ("previous tab", "last tab"):
        chrome_hotkey("ctrl", "shift", "tab")
        speak("Moving to the previous tab")
    elif normalized in ("go to top", "scroll to top", "top"):
        chrome_hotkey(command_key, "up")
        speak("Going to the top of the page")
    elif normalized in ("go to bottom", "scroll to bottom", "bottom"):
        chrome_hotkey(command_key, "down")
        speak("Going to the bottom of the page")
    elif normalized in ("copy link", "copy url"):
        chrome_hotkey(command_key, "l")
        pyautogui.hotkey(command_key, "c")
        pyautogui.press("esc")
        speak("Page link copied")
    elif normalized in ("maximize window", "full browser"):
        if IS_MACOS:
            success, error = run_chrome_applescript(
                'tell application "Google Chrome" to set zoomed of front window to true'
            )
            if success:
                speak("Chrome window maximized")
            else:
                print("Chrome maximize error:", error)
                speak("Chrome could not maximize the window")
        else:
            activate_chrome()
            pyautogui.hotkey("win", "up")
            speak("Chrome window maximized")
    elif normalized in (
        "dismiss popup",
        "close popup",
        "dismiss notification",
        "not now",
    ):
        activate_chrome()
        pyautogui.press("esc")
        speak("Pressed Escape to dismiss the popup")
    else:
        return False
    return True


def get_chrome_bounds():
    """Return Chrome's front-window bounds as (left, top, right, bottom)."""
    if not IS_MACOS:
        return None
    result = subprocess.run(
        [
            "/usr/bin/osascript",
            "-e",
            'tell application "Google Chrome" to get bounds of front window',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("Could not read Chrome window bounds:", result.stderr.strip())
        return None
    try:
        values = [int(value.strip()) for value in result.stdout.split(",")]
        if len(values) != 4:
            return None
        left, top, right, bottom = values
        if right <= left or bottom <= top:
            return None
        return left, top, right, bottom
    except ValueError:
        return None


def match_word_coverage(target, detected_text):
    """Return the fraction of requested words present in detected OCR text."""
    target_words = set(re.findall(r"[a-z0-9]+", target.lower()))
    detected_words = set(re.findall(r"[a-z0-9]+", detected_text.lower()))
    if not target_words:
        return 0.0
    return len(target_words & detected_words) / len(target_words)


def read_visible_chrome_text():
    """Return OCR text visible inside Chrome's front window."""
    chrome_bounds = get_chrome_bounds()
    if chrome_bounds:
        left, top, right, bottom = chrome_bounds
        screenshot = pyautogui.screenshot(
            region=(left, top, right - left, bottom - top)
        )
    else:
        screenshot = pyautogui.screenshot()
    screenshot.save("screen.png")
    return [text for _bbox, text, _probability in read_ocr("screen.png")]


def whatsapp_is_ready():
    """Return True only when the WhatsApp chats interface is visible."""
    texts = read_visible_chrome_text()
    normalized = [" ".join(text.lower().split()) for text in texts]
    return any(text == "chats" for text in normalized) or any(
        fuzz.token_set_ratio("search or start new chat", text) >= 85
        and match_word_coverage("search or start new chat", text) >= 0.5
        for text in normalized
    )


def wait_for_whatsapp_ready(timeout=30):
    """Wait until WhatsApp shows chats instead of its loading screen."""
    attempts = max(1, timeout // 5)
    for attempt in range(attempts):
        if whatsapp_is_ready():
            return True
        if attempt == 0:
            speak("WhatsApp is still loading. I will wait for the chats screen.")
        time.sleep(5)
    return False


def chrome_text_is_visible(target, minimum_score=80):
    """Check whether target text is currently visible inside Chrome."""
    for text in read_visible_chrome_text():
        score = fuzz.token_set_ratio(target.lower(), text.lower())
        coverage = match_word_coverage(target, text)
        if score >= minimum_score and coverage >= 0.5:
            return True
    return False


def click_by_title(target_title, ignore_header=True):
    # Restrict OCR to Chrome so terminal echoes cannot win the text match.
    chrome_bounds = get_chrome_bounds()
    if chrome_bounds:
        left, top, right, bottom = chrome_bounds
        logical_width = right - left
        logical_height = bottom - top
        screenshot = pyautogui.screenshot(
            region=(left, top, logical_width, logical_height)
        )
        origin_x, origin_y = left, top
    else:
        origin_x, origin_y = 0, 0
        logical_width, logical_height = pyautogui.size()
        screenshot = pyautogui.screenshot()
    screenshot.save("screen.png")

    # OCR the screenshot
    results = read_ocr("screen.png")

    best_score = 0
    best_coverage = 0
    best_probability = 0
    best_result = None
    best_text = ""

    screenshot_width, screenshot_height = screenshot.size
    content_start_y = screenshot_height * 0.18 if ignore_header else 0

    for bbox, text, prob in results:
        center_y = sum(point[1] for point in bbox) / len(bbox)
        if center_y < content_start_y:
            continue
        score = fuzz.token_set_ratio(target_title.lower(), text.lower())
        coverage = match_word_coverage(target_title, text)
        if (coverage, score, prob) > (
            best_coverage,
            best_score,
            best_probability,
        ):
            best_coverage = coverage
            best_score = score
            best_probability = prob
            best_result = bbox
            best_text = text
    # If a good match is found
    if best_result and best_score > 70 and best_coverage >= 0.25:
        # bbox is a list of 4 points
        (x1, y1), (_, _), (x2, y2), (_, _) = best_result
        scale_x = logical_width / screenshot_width
        scale_y = logical_height / screenshot_height
        center_x = origin_x + int(((x1 + x2) / 2) * scale_x)
        center_y = origin_y + int(((y1 + y2) / 2) * scale_y)
        pyautogui.moveTo(center_x, center_y)
        pyautogui.click()
        print(
            f"✅ Clicked OCR text: {best_text!r} "
            f"(score: {best_score}, coverage: {best_coverage:.0%}, "
            f"position: {center_x}, {center_y})"
        )
        speak("clicking")
        return True
    else:
        print(f"❌ No matching visible text found for: {target_title!r}")
        return False


def get_calendar_event_title(command):
    """Extract a title from 'create event team meeting' style commands."""
    normalized = " ".join(command.lower().split())
    for prefix in (
        "create calendar event ",
        "create event ",
        "new event ",
        "set reminder ",
        "reminder ",
    ):
        if normalized.startswith(prefix):
            return strip_chrome_disposition_suffix(normalized[len(prefix) :].strip())
    return ""


def parse_spoken_date(spoken, today=None):
    """Parse common spoken dates without silently defaulting to today."""
    if not spoken:
        return None
    reference = today or date.today()
    normalized = " ".join(spoken.lower().split())
    normalized = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", normalized)

    if "day after tomorrow" in normalized:
        return reference + timedelta(days=2)
    if "tomorrow" in normalized:
        return reference + timedelta(days=1)
    if normalized in ("today", "on today", "date today"):
        return reference

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    for weekday, weekday_number in weekdays.items():
        if weekday in normalized:
            days_ahead = (weekday_number - reference.weekday()) % 7
            return reference + timedelta(days=days_ahead)

    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    month_number = next(
        (number for name, number in months.items() if name in normalized),
        None,
    )
    numbers = [int(value) for value in re.findall(r"\b\d{1,4}\b", normalized)]
    if month_number is not None:
        day_number = next((value for value in numbers if 1 <= value <= 31), None)
        year_number = next(
            (value for value in numbers if value >= 1000), reference.year
        )
        if day_number is None:
            return None
        try:
            parsed = date(year_number, month_number, day_number)
            if all(value < 1000 for value in numbers) and parsed < reference:
                parsed = date(reference.year + 1, month_number, day_number)
            return parsed
        except ValueError:
            return None

    if len(numbers) == 3:
        day_number, month_number, year_number = numbers
        try:
            return date(year_number, month_number, day_number)
        except ValueError:
            return None
    return None


def build_calendar_event_url(title, event_date):
    """Build a dated all-day Google Calendar draft URL."""
    end_date = event_date + timedelta(days=1)
    query = urlencode(
        {
            "action": "TEMPLATE",
            "text": title,
            "dates": (
                event_date.strftime("%Y%m%d") + "/" + end_date.strftime("%Y%m%d")
            ),
        }
    )
    return "https://calendar.google.com/calendar/render?" + query


def save_calendar_draft():
    """Confirm and click Calendar's visible Save button without overclaiming."""
    current_url = get_active_chrome_url().lower()
    if "calendar.google.com" not in current_url or not (
        "eventedit" in current_url or "action=template" in current_url
    ):
        speak("I cannot verify that a Calendar event draft is open.")
        return False

    response = listen_for_short_response(
        ready_prompt="Save this Calendar event? Say yes or no."
    )
    if not is_affirmative(response):
        speak("The Calendar event was not saved.")
        return False

    before_url = current_url
    activate_chrome()
    if not click_by_title("save", ignore_header=False):
        speak("I could not locate the Calendar Save button.")
        return False
    time.sleep(2)
    after_url = get_active_chrome_url().lower()
    if after_url and after_url != before_url:
        speak("Calendar accepted the Save command. Please verify the event.")
    else:
        speak("I clicked Save, but please verify that the event appears in Calendar.")
    return True


def execute_reminder():
    """Create a reviewable Calendar event draft or handle Calendar controls."""
    speak("What should I do in Calendar?")
    command = listen()
    time.sleep(0.5)
    if is_help_request(command):
        provide_command_help(command, context="calendar")
        return None
    if is_quit_assistant_command(command):
        quit_assistant()
    if command in (
        "exit",
        "stop",
        "bye",
        "exit calendar",
        "leave calendar",
        "leave calendar mode",
        "stop calendar",
    ):
        return exit_chrome_mode("Calendar")
    if command in (
        "save it",
        "save event",
        "save reminder",
        "save calendar event",
    ):
        save_calendar_draft()
        return None
    if command == "yes" or command.startswith(
        (
            "create event",
            "create calendar event",
            "new event",
            "set reminder",
            "reminder",
        )
    ):
        title = get_calendar_event_title(command)
        if not title:
            speak("What is the event title?")
            title = listen()
        if not title:
            speak("Calendar draft cancelled because I could not hear a title.")
            return None
        event_date = None
        for attempt in range(2):
            speak(
                "What date is the event? Say for example, 3 August 2026, "
                "tomorrow, or Monday."
            )
            event_date = parse_spoken_date(listen())
            if event_date:
                break
            if attempt == 0:
                speak("I could not understand that date. Please say it again.")
        if not event_date:
            speak("Calendar draft cancelled because the date was not understood.")
            return None
        spoken_event_date = (
            f"{event_date.day} {event_date.strftime('%B')} {event_date.year}"
        )
        speak("Opening a Calendar draft for " + title + " on " + spoken_event_date)
        open_in_chrome(
            build_calendar_event_url(title, event_date),
            chrome_disposition_from_command(command),
        )
        speak("Review the event details, then save it in Calendar.")
        return None
    if handle_chrome_navigation(command):
        return None
    speak("I don't recognize that Calendar command.")
    return None


def get_inline_message(command):
    """Extract text from commands such as 'message where are you'."""
    normalized = command.strip().lower()
    for prefix in ("send message ", "message ", "text ", "send "):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return ""


def normalize_spelled_contact(spoken):
    """Turn speech such as 'a n u space s h' into a searchable name."""
    words = re.findall(r"[a-z0-9]+", spoken.lower())
    words = [word for word in words if word not in ("spell", "spelling", "contact")]
    if not words:
        return ""

    parts = []
    letters = []
    for word in words:
        if word == "space":
            if letters:
                parts.append("".join(letters))
                letters = []
        elif len(word) == 1:
            letters.append(word)
        else:
            if letters:
                parts.append("".join(letters))
                letters = []
            parts.append(word)
    if letters:
        parts.append("".join(letters))
    return " ".join(parts).strip()


def extract_contact_correction(command):
    """Extract an inline correction such as 'change contact to Riya'."""
    normalized = " ".join(command.lower().split())
    for prefix in ("change contact to ", "change to ", "correct it to "):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :].strip()
    return ""


def get_confirmed_whatsapp_contact(max_attempts=4):
    """Hear, read back, and allow correction of a WhatsApp contact name."""
    candidate = ""
    for _ in range(max_attempts):
        if not candidate:
            speak("Who do you want to message?")
            candidate = listen()
        if candidate in (
            "exit",
            "stop",
            "exit whatsapp",
            "leave whatsapp",
            "stop whatsapp",
        ):
            return "__exit__"
        if is_quit_assistant_command(candidate):
            return "__quit__"
        if "spell" in candidate:
            speak("Say the letters of the contact name. Say space between words.")
            candidate = normalize_spelled_contact(listen())
        if is_help_request(candidate):
            provide_command_help(candidate, context="whatsapp")
            candidate = ""
            continue
        if not candidate:
            speak("I could not hear the contact name. Please try again.")
            continue

        speak(
            "I heard "
            + candidate
            + ". Say yes to use it, change contact to followed by the name, "
            "or spell contact."
        )
        answer = listen_for_short_response()
        if answer in ("correct", "that's correct", "use it") or is_affirmative(answer):
            return candidate

        correction = extract_contact_correction(answer)
        if correction:
            candidate = correction
            continue
        if "spell" in answer:
            speak("Say the letters of the contact name. Say space between words.")
            candidate = normalize_spelled_contact(listen())
            continue
        if any(word in answer for word in ("no", "change", "wrong", "again")):
            candidate = ""
            continue

        speak("I did not hear a confirmation. Let us try the contact name again.")
        candidate = ""

    speak("The contact was not confirmed, so I will not search or type anything.")
    return ""


def focus_whatsapp_message_field():
    """Focus the composer using OCR, with a window-relative fallback."""
    if click_by_title("type a message", ignore_header=False):
        return True

    bounds = get_chrome_bounds()
    if not bounds:
        return False
    left, top, right, bottom = bounds
    # WhatsApp's composer occupies the bottom of the active chat pane. This
    # fallback is used only after the requested contact has been verified.
    pyautogui.click(
        left + int((right - left) * 0.72),
        top + int((bottom - top) * 0.94),
    )
    return True


def whatsapp_execute_safe():
    """Operate WhatsApp only after verifying each required UI state."""
    if not wait_for_whatsapp_ready():
        speak("WhatsApp did not finish loading, so I will not type or send anything.")
        return "exit"

    contact = ""
    for selection_attempt in range(3):
        contact = get_confirmed_whatsapp_contact()
        if contact == "__quit__":
            quit_assistant()
        if contact == "__exit__":
            return exit_chrome_mode("WhatsApp")
        if not contact:
            speak("Leaving WhatsApp mode without selecting a contact.")
            return "exit"

        activate_chrome()
        if not click_by_title("search or start new chat", ignore_header=False):
            speak("I could not locate the WhatsApp chat search field.")
            return "exit"
        pyautogui.hotkey("command" if IS_MACOS else "ctrl", "a")
        pyautogui.press("backspace")
        pyautogui.write(contact, interval=0.04)
        time.sleep(2)
        pyautogui.press("enter")
        time.sleep(2)

        if chrome_text_is_visible(contact):
            speak("Verified contact " + contact)
            break

        if selection_attempt < 2:
            speak(
                "I could not find or verify "
                + contact
                + ". Let us try again. Say spell contact if the name is "
                "often recognized incorrectly."
            )
        else:
            speak("I could not verify a contact after three attempts.")
            return "exit"

    while True:
        speak("What can I do for you?")
        command = listen()
        if not command:
            continue
        if is_help_request(command):
            provide_command_help(command, context="whatsapp")
            continue
        if is_quit_assistant_command(command):
            quit_assistant()
        if command in (
            "exit",
            "stop",
            "bye",
            "exit whatsapp",
            "leave whatsapp",
            "stop whatsapp",
        ):
            return exit_chrome_mode("WhatsApp")
        if command in ("change contact", "another contact", "switch contact"):
            speak("Okay, choose another contact.")
            return "change contact"
        if handle_chrome_navigation(command):
            continue
        if command.startswith(("message", "text", "send")):
            message = get_inline_message(command)
            if not message:
                speak("What message do you want me to type?")
                message = listen()
            if not message:
                speak("No message was detected.")
                continue

            activate_chrome()
            if not focus_whatsapp_message_field():
                speak("I could not locate the WhatsApp message field.")
                continue
            pyautogui.write(message, interval=0.04)
            speak(
                "I typed: " + message + ". Should I send it? Answer after I say ready."
            )
            confirmation = listen_for_short_response()
            if not (is_affirmative(confirmation) or "send" in confirmation):
                pyautogui.hotkey("command" if IS_MACOS else "ctrl", "a")
                pyautogui.press("backspace")
                speak("Message cancelled and cleared.")
                continue

            pyautogui.press("enter")
            time.sleep(2)
            if chrome_text_is_visible(message, minimum_score=75):
                speak(
                    "The message text is visible after the send command. "
                    "Please verify its delivery status."
                )
            else:
                speak(
                    "The send command was submitted, but I could not verify delivery."
                )
        elif "media" in command or "file" in command:
            speak("Media automation is disabled until the chat controls are verified.")
        else:
            speak("I don't recognize that WhatsApp command.")


def begin_youtube_quiet_mode():
    """Mute an active YouTube video while VoiceAssist speaks and listens."""
    global youtube_temporarily_muted
    youtube_temporarily_muted = False
    url = get_active_chrome_url().lower()
    is_video_page = "youtube.com/watch" in url or "youtube.com/shorts/" in url
    if not is_video_page or youtube_muted_by_user:
        return False

    activate_chrome()
    pyautogui.press("m")
    youtube_temporarily_muted = True
    time.sleep(0.15)
    return True


def end_youtube_quiet_mode():
    """Restore video audio unless the user asked for YouTube to stay muted."""
    global youtube_temporarily_muted
    if youtube_temporarily_muted and not youtube_muted_by_user:
        activate_chrome()
        pyautogui.press("m")
    youtube_temporarily_muted = False


def set_youtube_user_mute():
    """Toggle persistent YouTube mute without fighting temporary quiet mode."""
    global youtube_muted_by_user
    if youtube_muted_by_user:
        youtube_muted_by_user = False
        activate_chrome()
        pyautogui.press("m")
        speak("YouTube sound is on")
        return

    youtube_muted_by_user = True
    if not youtube_temporarily_muted:
        activate_chrome()
        pyautogui.press("m")
    speak("YouTube is muted")


def pause_youtube_video_if_playing():
    """Pause an active YouTube video without toggling an already-paused video."""
    url = get_active_chrome_url().lower()
    if "youtube.com/watch" not in url and "youtube.com/shorts/" not in url:
        return False

    javascript = (
        "(() => { const video = document.querySelector('video'); "
        "if (!video) return 'no-video'; "
        "if (video.paused) return 'already-paused'; "
        "video.pause(); return 'paused'; })()"
    )
    safe_javascript = escape_applescript_string(javascript)
    success, output = run_chrome_applescript(
        'tell application "Google Chrome" to execute active tab of front window '
        f'javascript "{safe_javascript}"'
    )
    if not success:
        print("Could not inspect YouTube playback state:", output)
        return False
    if output.strip() == "paused":
        speak("Paused the YouTube video before leaving.")
    return output.strip() in ("paused", "already-paused")


def exit_youtube_mode():
    """Leave YouTube safely, optionally closing its tab."""
    global youtube_muted_by_user
    pause_youtube_video_if_playing()
    should_close = ask_to_close_active_tab("YouTube")
    if should_close:
        # Restore temporary player state before destroying the tab; otherwise
        # the final cleanup key could affect whichever tab becomes active.
        end_youtube_quiet_mode()
        if close_active_chrome_tab():
            speak("Closed the YouTube tab.")
        else:
            speak("I could not close the YouTube tab.")
    else:
        if youtube_temporarily_muted:
            youtube_muted_by_user = True
            speak("Leaving the YouTube tab open with the video muted.")
        else:
            speak("Leaving the YouTube tab open.")
    speak("Exiting YouTube command mode.")
    return "exit"


def execute_yt():
    """Run one YouTube command while keeping video sound out of the mic."""
    begin_youtube_quiet_mode()
    try:
        speak("Do you have any command?")
        command = listen()
        time.sleep(0.5)
        return execute_yt_command(command)
    finally:
        end_youtube_quiet_mode()


def execute_yt_command(command):
    if is_help_request(command):
        provide_command_help(command, context="youtube")
        return None
    if is_quit_assistant_command(command):
        quit_assistant()
    if command in ("exit", "leave youtube", "exit youtube", "stop youtube", "stop"):
        return exit_youtube_mode()
    if "open whatsapp" in command:
        pause_youtube_video_if_playing()
        end_youtube_quiet_mode()
        speak("Leaving YouTube and switching to WhatsApp")
        return command
    if "open google" in command:
        pause_youtube_video_if_playing()
        end_youtube_quiet_mode()
        speak("Leaving YouTube and switching to Google")
        return command
    if "open calendar" in command or "set reminder" in command:
        pause_youtube_video_if_playing()
        end_youtube_quiet_mode()
        speak("Leaving YouTube and switching to Calendar")
        return command
    if "maximize window" in command or "full browser" in command:
        if IS_MACOS:
            success, error = run_chrome_applescript(
                'tell application "Google Chrome" to set zoomed of front window to true'
            )
            if success:
                speak("Chrome window maximized")
            else:
                print("Chrome maximize error:", error)
                speak("Chrome could not maximize the window")
        else:
            activate_chrome()
            pyautogui.hotkey("win", "up")
            speak("Chrome window maximized")
    elif "fullscreen video" in command or "full screen video" in command:
        activate_chrome()
        pyautogui.press("f")
        speak("Toggling video full screen")
    elif "search" in command or "find" in command:
        query = get_youtube_search_query(command)
        if not query:
            for _ in range(2):
                speak("What should I search for?")
                query = listen()
                if query:
                    break
                speak("Please say the search query again.")
        if query:
            speak("Searching YouTube for " + query)
            end_youtube_quiet_mode()
            open_in_chrome(
                "https://www.youtube.com/results?search_query=" + quote_plus(query)
            )
        else:
            speak("Search cancelled because I could not hear a query.")
    elif command in (
        "go back",
        "previous page",
        "go forward",
        "next page",
        "refresh",
        "reload",
        "reload page",
    ):
        end_youtube_quiet_mode()
        handle_chrome_navigation(command)
    elif handle_chrome_navigation(command):
        pass
    elif is_visible_open_command(command):
        spoken_title = get_visible_target(command)
        if not spoken_title:
            speak("Which visible title should I open?")
            spoken_title = listen()
        if spoken_title:
            speak("Looking for " + spoken_title)
            end_youtube_quiet_mode()
            activate_chrome()
            if not click_by_title(spoken_title):
                speak("I could not find that visible title. Try a shorter title.")
        else:
            speak("I could not hear a title to open.")
    elif "play" in command or "pause" in command or "poz" in command:
        activate_chrome()
        pyautogui.press("k")
        speak("Toggling video playback")
    elif "mute" in command or "sound" in command:
        set_youtube_user_mute()
    elif command in ("forward", "skip forward", "video forward", "seek forward"):
        activate_chrome()
        pyautogui.press("right", presses=2, interval=0.1)
        speak("Moving the video forward ten seconds")
    elif command in ("back", "rewind", "video back", "seek back"):
        activate_chrome()
        pyautogui.press("left", presses=2, interval=0.1)
        speak("Moving the video back ten seconds")


def execute_google():
    speak("What should I do in Google?")
    command = listen()
    time.sleep(0.5)
    if is_help_request(command):
        provide_command_help(command, context="google")
        return None
    if is_quit_assistant_command(command):
        quit_assistant()
    if command in (
        "exit",
        "stop",
        "bye",
        "exit google",
        "leave google",
        "stop google",
    ):
        return exit_chrome_mode("Google")
    if command == "yes" or "search" in command or "find" in command:
        query = get_google_search_query(command)
        if not query:
            speak("What should I search Google for?")
            query = listen()
        if not query:
            speak("Google search cancelled because I could not hear a query.")
            return None
        speak("Searching Google for " + query)
        open_in_chrome(
            "https://www.google.com/search?q=" + quote_plus(query),
            chrome_disposition_from_command(command),
        )
        return None
    if handle_chrome_navigation(command):
        return None
    if is_visible_open_command(command) or "link" in command:
        spoken_title = get_visible_target(command)
        if not spoken_title:
            speak("Which visible title should I open?")
            spoken_title = listen()
        if spoken_title:
            activate_chrome()
            if not click_by_title(spoken_title):
                speak("I could not find that visible Google result.")
        return None
    speak("I don't recognize that Google command.")
    return None


def execute(command):
    global youtube_muted_by_user, youtube_temporarily_muted
    disposition = chrome_disposition_from_command(command)
    if is_quit_assistant_command(command):
        quit_assistant()
    if is_help_request(command):
        provide_command_help(command)
    elif "open youtube" in command or "youtube" in command:
        youtube_muted_by_user = False
        youtube_temporarily_muted = False
        speak("Opening YouTube")
        open_in_chrome("https://www.youtube.com", disposition)
        while True:
            result = execute_yt()
            if result == "exit":
                break
            if result and any(
                phrase in result
                for phrase in (
                    "open whatsapp",
                    "open google",
                    "open calendar",
                    "set reminder",
                )
            ):
                return execute(result)
    elif command == "google" or (
        command.startswith("open google") and "calendar" not in command
    ):
        speak("Opening Google")
        open_in_chrome("https://www.google.com", disposition)
        speak("Google is ready. Say search followed by your query.")
        while True:
            result = execute_google()
            if result == "exit":
                break
    elif "open whatsapp" in command or "whatsapp" in command:
        speak("Opening WhatsApp Web")
        open_in_chrome("https://web.whatsapp.com", disposition)
        while True:
            result = whatsapp_execute_safe()
            if result == "exit":
                break
    elif "reminder" in command or "calendar" in command:
        speak("Opening Google Calendar")
        open_in_chrome("https://calendar.google.com", disposition)
        while True:
            result = execute_reminder()
            if result == "exit":
                break
    # elif "calendar"in command or "calender" in command:
    #     speak("Opening Google Calender")
    #     webbrowser.open("https://calendar.google.com/calendar/u/0/r")
    #     execute_calender()

    elif "type something" in command or "write something" in command:
        voice_to_type()
    elif handle_chrome_navigation(command):
        pass
    elif "exit" in command or "stop" in command or "bye" in command:
        quit_assistant()
    else:
        speak("Sorry, I don't recognize that command.")


# Main loop with sleep/wake feature
sleeping = False

if __name__ == "__main__":
    calibrate_microphone()
    speak("Voice assistant ready. Say a command.")
    while True:
        speak("What can i do for you?")
        cmd = listen()

        if not cmd:
            continue

        if sleeping:
            if "wake up" in cmd or "resume" in cmd:
                sleeping = False
                speak("I'm awake again!")
            else:
                continue
        else:
            if "sleep" in cmd or "wait" in cmd:
                sleeping = True
                speak("Going to sleep. Say 'wake up' when you need me.")
            else:
                execute(cmd)
