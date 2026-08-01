"""Data-driven command guide for VoiceAssist."""

import re


COMMANDS = {
    "youtube": [
        {
            "name": "Open YouTube",
            "say": "open youtube",
            "description": (
                "Open YouTube in the current tab. Add 'in a new tab' or "
                "'in a new window' only when needed."
            ),
            "triggers": [
                "open youtube",
                "open youtube in a new tab",
                "open youtube in a new window",
            ],
        },
        {
            "name": "Search YouTube",
            "say": "search Python DSA tutorial",
            "description": "Search immediately, or say only 'search' to be prompted.",
            "triggers": ["search", "find", "search youtube"],
        },
        {
            "name": "Open a visible video",
            "say": "open DSA using Python in Hindi",
            "description": "Use OCR to find and click a visible video title.",
            "triggers": ["open video", "click video", "open title", "click title"],
        },
        {
            "name": "Play or pause",
            "say": "pause",
            "description": "Toggle YouTube video playback.",
            "triggers": ["play", "pause", "pause video", "play video"],
        },
        {
            "name": "Seek forward",
            "say": "forward",
            "description": "Move the video forward ten seconds.",
            "triggers": ["forward", "skip forward", "video forward", "seek forward"],
        },
        {
            "name": "Rewind",
            "say": "back",
            "description": "Move the video back ten seconds.",
            "triggers": ["back", "rewind", "video back", "seek back"],
        },
        {
            "name": "YouTube sound and display",
            "say": "mute or fullscreen video",
            "description": "Toggle mute or video full screen.",
            "triggers": ["mute", "fullscreen video", "full screen video"],
        },
        {
            "name": "Leave YouTube",
            "say": "exit",
            "description": (
                "Leave YouTube mode, then choose whether its Chrome tab should close."
            ),
            "triggers": ["exit youtube", "leave youtube", "stop youtube"],
        },
    ],
    "chrome": [
        {
            "name": "Scroll",
            "say": "scroll down or scroll up",
            "description": "Move the active Chrome page vertically.",
            "triggers": ["scroll down", "scroll up"],
        },
        {
            "name": "Browser history",
            "say": "go back or go forward",
            "description": "Navigate Chrome history. Keep 'go' to distinguish it from video seeking.",
            "triggers": ["go back", "go forward", "previous page", "next page"],
        },
        {
            "name": "Reload",
            "say": "reload",
            "description": "Ask Chrome to reload the active tab.",
            "triggers": ["reload", "refresh", "reload page"],
        },
        {
            "name": "Dismiss a popup",
            "say": "dismiss popup",
            "description": "Press Escape in Chrome to dismiss the active popup.",
            "triggers": [
                "dismiss popup",
                "close popup",
                "dismiss notification",
                "not now",
            ],
        },
        {
            "name": "Window",
            "say": "maximize window",
            "description": "Maximize the active Chrome window.",
            "triggers": ["maximize window", "full browser"],
        },
        {
            "name": "Tabs",
            "say": (
                "open YouTube in a new tab, open WhatsApp in a new window, "
                "close tab, next tab, or previous tab"
            ),
            "description": (
                "Sites reuse the active tab by default. Explicitly request a new "
                "tab or window, or close and switch tabs."
            ),
            "triggers": [
                "new tab",
                "new window",
                "close tab",
                "next tab",
                "previous tab",
            ],
        },
        {
            "name": "Page position",
            "say": "go to top or go to bottom",
            "description": "Jump to the beginning or end of the page.",
            "triggers": [
                "go to top",
                "go to bottom",
                "scroll to top",
                "scroll to bottom",
            ],
        },
        {
            "name": "Copy page link",
            "say": "copy link",
            "description": "Copy the active tab URL.",
            "triggers": ["copy link", "copy url"],
        },
    ],
    "whatsapp": [
        {
            "name": "Open WhatsApp",
            "say": "open whatsapp",
            "description": "Open WhatsApp Web and wait until the chats interface is verified.",
            "triggers": ["open whatsapp"],
        },
        {
            "name": "Type a message",
            "say": "text where are you",
            "description": "Type a message, read it back, and ask before sending.",
            "triggers": ["text", "message", "send message"],
        },
        {
            "name": "Correct a contact",
            "say": "change contact to Riya, or spell contact",
            "description": (
                "Correct the recognized name before WhatsApp searches, or switch "
                "to another contact after a chat opens."
            ),
            "triggers": [
                "change contact",
                "change contact to",
                "spell contact",
                "switch contact",
            ],
        },
        {
            "name": "Leave WhatsApp",
            "say": "leave whatsapp",
            "description": (
                "Leave WhatsApp mode and choose whether its Chrome tab should close."
            ),
            "triggers": ["leave whatsapp", "exit whatsapp", "stop whatsapp"],
        },
    ],
    "google": [
        {
            "name": "Open Google",
            "say": "open google",
            "description": "Open Google and begin a search workflow.",
            "triggers": ["open google"],
        },
        {
            "name": "Google search",
            "say": "search",
            "description": "Start another Google search while in Google mode.",
            "triggers": ["google search", "search google"],
        },
        {
            "name": "Leave Google",
            "say": "leave google",
            "description": (
                "Return to the main assistant and choose whether its tab should close."
            ),
            "triggers": ["leave google", "exit google", "stop google"],
        },
    ],
    "calendar": [
        {
            "name": "Calendar event draft",
            "say": "create event Cognizant interview",
            "description": (
                "Open a Google Calendar event draft with the title filled in. "
                "VoiceAssist asks for the date, then you review before saving."
            ),
            "triggers": [
                "reminder",
                "open calendar",
                "set reminder",
                "create event",
                "new event",
            ],
        },
        {
            "name": "Save Calendar draft",
            "say": "save it",
            "description": (
                "Ask for confirmation, then click the visible Calendar Save button."
            ),
            "triggers": ["save it", "save event", "save reminder"],
        },
        {
            "name": "Leave Calendar",
            "say": "exit calendar",
            "description": (
                "Leave Calendar mode and choose whether its Chrome tab should close."
            ),
            "triggers": [
                "exit calendar",
                "leave calendar",
                "leave calendar mode",
                "stop calendar",
            ],
        },
    ],
    "assistant": [
        {
            "name": "Command help",
            "say": "help YouTube or how do I go back",
            "description": "Ask for a category or one particular command.",
            "triggers": ["help", "list commands", "what can you do"],
        },
        {
            "name": "Voice typing",
            "say": "type something",
            "description": "Dictate text into the currently focused input.",
            "triggers": ["type something", "write something"],
        },
        {
            "name": "Sleep and wake",
            "say": "sleep or wake up",
            "description": "Pause command processing and resume it later.",
            "triggers": ["sleep", "wake up", "resume"],
        },
        {
            "name": "Quit assistant",
            "say": "quit assistant",
            "description": "Terminate VoiceAssist completely.",
            "triggers": ["quit assistant", "close assistant", "goodbye"],
        },
    ],
}

CATEGORY_ALIASES = {
    "video": "youtube",
    "videos": "youtube",
    "browser": "chrome",
    "web": "chrome",
    "message": "whatsapp",
    "messages": "whatsapp",
    "reminder": "calendar",
    "reminders": "calendar",
    "calender": "calendar",
}

BROAD_HELP = {
    "help",
    "commands",
    "list commands",
    "show commands",
    "what can you do",
    "what commands can i use",
}

CATEGORY_SUMMARIES = {
    "youtube": (
        "For YouTube, you can say search, open a visible title, play, pause, "
        "forward, back, mute, maximize window, fullscreen video, or exit. "
        "Say detailed help for a step-by-step guide, or say explain followed "
        "by a command, for example, explain forward command."
    ),
}

CONTEXT_CATEGORIES = {
    "youtube": ["youtube", "chrome", "assistant"],
    "google": ["google", "chrome", "assistant"],
    "whatsapp": ["whatsapp", "chrome", "assistant"],
    "calendar": ["calendar", "chrome", "assistant"],
}


def normalize(text):
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def is_help_request(command):
    normalized = normalize(command)
    return (
        normalized in BROAD_HELP
        or normalized.startswith("help ")
        or normalized.startswith("health ")
        or normalized.startswith("how do i ")
        or normalized.startswith("how to ")
        or normalized.startswith("explain ")
        or normalized.startswith("detailed help")
        or (normalized.startswith("what") and "command" in normalized)
    )


def category_from_query(query):
    words = set(normalize(query).split())
    for category in COMMANDS:
        if category in words:
            return category
    for alias, category in CATEGORY_ALIASES.items():
        if alias in words:
            return category
    return None


def category_help_request(query, context=None):
    """Return the category when a request asks to browse a whole category."""
    normalized = normalize(query)
    if normalized in BROAD_HELP and context in COMMANDS:
        return context
    category = category_from_query(query)
    if category and (
        (normalized.startswith("help ") and len(normalized.split()) == 2)
        or "commands" in normalized.split()
    ):
        return category
    return None


def find_command(query, context=None):
    normalized = normalize(query)
    candidates = []
    categories = CONTEXT_CATEGORIES.get(context, list(COMMANDS))
    for category in categories:
        for entry in COMMANDS[category]:
            score = 0
            for trigger in entry["triggers"]:
                normalized_trigger = normalize(trigger)
                if normalized_trigger and normalized_trigger in normalized:
                    score += len(normalized_trigger.split())
            if score:
                candidates.append((score, category, entry))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])


def format_category(category):
    title = category.title()
    lines = [f"{title} commands:"]
    for entry in COMMANDS[category]:
        lines.append(f"- {entry['say']}: {entry['description']}")
    return "\n".join(lines)


def format_full_guide():
    return "\n\n".join(format_category(category) for category in COMMANDS)


def overview_response():
    return (
        "I can help with YouTube, Chrome, WhatsApp, Google, Calendar, and "
        "assistant controls. Say help followed by a category, or ask a "
        "question such as, how do I move a video forward. I printed the full "
        "command guide in the terminal."
    )


def help_response(query, context=None):
    normalized = normalize(query)
    if normalized in BROAD_HELP:
        if context in COMMANDS:
            return CATEGORY_SUMMARIES.get(context, format_category(context))
        return overview_response()

    category = category_from_query(query)
    requested_category = category_help_request(query, context=context)
    if requested_category:
        return CATEGORY_SUMMARIES.get(
            requested_category,
            format_category(requested_category),
        )

    match = find_command(query, context=context)
    if match:
        _score, category, entry = match
        return (
            f"For {entry['name']} in {category.title()}, say: {entry['say']}. "
            f"{entry['description']}"
        )

    category = category or context
    if category in COMMANDS:
        return format_category(category)

    return (
        "I could not identify that command. Say list commands to see every "
        "category, or ask help followed by YouTube, Chrome, WhatsApp, Google, "
        "Calendar, or Assistant."
    )
