import speech_recognition as sr
import pyttsx3
import pyautogui
import webbrowser
import time
from PIL import Image
import easyocr
from fuzzywuzzy import fuzz
import os
from PyPDF2 import PdfReader
import docx

reader = easyocr.Reader(['en'], gpu=False)
engine = pyttsx3.init()

# Global control flag
running = True

def stop_assistant():
    global running
    running = False

def speak(text):
    print("Assistant:", text)
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\U0001F399️ Listening...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print("You said:", command)
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
            return ""
        except sr.RequestError:
            speak("Speech recognition API unavailable.")
            return ""

def voice_to_type():
    speak("What should I type?")
    text = listen()
    time.sleep(0.5)
    if text:
        speak("Typing now.")
        time.sleep(2)
        pyautogui.typewrite(text)  #start
# Initialize text-to-speech engine



def speak_text(text):
    print("Assistant:", text)
    engine.say(text)        
    engine.runAndWait()

def read_text_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        full_text = f.read()
        speak_text(full_text)

def read_pdf_file(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    text = ' '.join(text.split())  # C
    speak_text(text)

def read_docx_file(path):
    doc = docx.Document(path)
    full_text = '\n'.join([para.text for para in doc.paragraphs])
    speak_text(full_text)

def read_file_aloud(file_path):
    if file_path.endswith('.txt'):
        read_text_file(file_path)
    elif file_path.endswith('.pdf'):
        read_pdf_file(file_path)
    elif file_path.endswith('.docx'):
        read_docx_file(file_path)
    else:
        speak("Sorry, I can only read text, PDF, or Word files.")

def get_latest_supported_file(download_path):
    supported_exts = ('.txt', '.pdf', '.docx')
    files = [
        os.path.join(download_path, f)
        for f in os.listdir(download_path)
        if f.lower().endswith(supported_exts)
    ]
    if not files:
        return None
    return max(files, key=os.path.getctime)


engine = pyttsx3.init()
def speak(text):
    print("Assistant:", text)
    engine.say(text)
    engine.runAndWait()

# Capture voice command
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Listening...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print("You said:", command)
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
            return ""
        except sr.RequestError:
            speak("Speech recognition API unavailable.")
            return ""

# Voice-to-type functionality
def voice_to_type():
    speak("What should I type?")
    text = listen()
    time.sleep(0.5)
    if text:
        speak("Typing now.")
        time.sleep(2)
        pyautogui.typewrite(text)

def click_by_title(target_title):
    # Screenshot the screen
    screenshot = pyautogui.screenshot()
    screenshot.save("screen.png")

    # OCR the screenshot
    results = reader.readtext("screen.png")

    best_score = 0
    best_result = None

    for (bbox, text, prob) in results:
        score = fuzz.token_set_ratio(target_title.lower(), text.lower())
        if score > best_score:
            best_score = score
            best_result = bbox
    # If a good match is found
    if best_result and best_score > 70:
        # bbox is a list of 4 points
        (x1, y1), (_, _), (x2, y2), (_, _) = best_result
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        pyautogui.moveTo(center_x, center_y)
        pyautogui.click()
        print(f"✅ Clicked on: {target_title} (score: {best_score})")
        speak("clicking")
    else:
        speak("not found")
        print("❌ No matching video title found.")

# Execution Functions
# def execute_calender():
#     pyautogui.hotkey('c')
#     speak("Tell the title")
#     title = listen()
#     pyautogui.typewrite(title)
#     pyautogui.hotkey('tab')
#     pyautogui.hotkey('tab')
#     speak("Tell the date")
#     date = listen()
#     pyautogui.typewrite(date)
#     pyautogui.hotkey('tab')
#     speak("Tell the time")
#     time = listen()
#     pyautogui.typewrite(time)
#     for _ in range(14):
#         pyautogui.press('tab')
#     speak("should i put the link copied in google meet ?")
#     meet = listen()
#     if "yes"in meet or "ok" in meet:
#         pyautogui.hotkey('ctrl','v')
#     speak("saving the reminder in google calender")
#     pyautogui.hotkey('ctrl','s')

def execute_reminder():
    speak("Do you want to create task?")
    command= listen()
    time.sleep(0.5)
    pyautogui.moveTo(119,240)
    pyautogui.click()
    c= listen()
    if "yes" in c or "ok" in c:
        pyautogui.moveTo(116,344)
        pyautogui.click()
        speak("creating a task") 
        speak("Add title")
        c2= listen()
        voice_to_type()
        speak("Adding a task")
        speak("want to add description?")
        C3= listen()
        if "yes" in C3 or "ok" in C3:
            pyautogui.hotkey('tab')
            pyautogui.hotkey('tab')
            speak("adding description")
            voice_to_type()
        pyautogui.hotkey('ctrl','enter')
    elif "stop" in command or "bye" in command or "google" in command or "calender" in command:
        speak("Exiting google calender Command!")
        return "exit"

    
def whatsapp_execute():
    time.sleep(10)
    speak("Who do you want to message?")
    contact_selected = False
    while True:
        if not contact_selected:
            name = ""
            while not name:
                pyautogui.moveTo(206, 195)  
                pyautogui.click(clicks=3, interval=0.1)
                speak("Listening for contact name...")
                name = listen()
                if not name:
                    speak("Didn't catch that, trying again...")
            
                pyautogui.typewrite(name)
                time.sleep(2)
                pyautogui.press('enter')  
                contact_selected = True
                speak(f"Selected contact {name}.")
        speak("What can I do for you?")
        command = listen()

        if not command:
            continue

        if "change contact" in command or "new contact" in command:
            contact_selected = False
            speak("Okay, changing contact.")
            continue

        elif "message" in command or "send" in command:
            speak("What message do you want to send?")
            message = listen()
            if message:
                pyautogui.typewrite(message)
                pyautogui.press('enter')
                speak("Message sent.")
            else:
                speak("No message detected.")
        elif "media" in command:
            pyautogui.moveTo(797, 132)  
            pyautogui.click()
            time.sleep(2)
            pyautogui.moveTo(1498, 652)  
            pyautogui.click()
            speak("what do you want me to click doc or links")
            a=1
            while a>0:
                c = listen()
                if "doc" in c or "file" in c or "dog" in c:
                    pyautogui.moveTo(1630, 220)  
                    speak("Clicking") 
                    pyautogui.click()
                    a=0
                elif "link" in c or "links" in c:
                    pyautogui.moveTo(1861, 208)
                    speak("Clicking")  
                    pyautogui.click()
                    a=-1
            if a==0:
                speak("which file do you want me to download ?")
                file = listen()
                click_by_title(file)
                speak("File downloading")
                time.sleep(2)
                pyautogui.moveTo(1789, 999)
                pyautogui.click()
                pyautogui.moveTo(1389, 136)
                pyautogui.click()
                time.sleep(1)
                speak("Do you want me to read the file for you?")
                ans =listen()
                pyautogui.moveTo(1389, 136)
                pyautogui.click()
                if "yes" in ans or "ok" in ans:
                    # Example usage:
                    speak("Okay reading just a few moments")
                    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
                    latest_file = get_latest_supported_file(downloads_folder)

                    if latest_file:
                        speak(f"Reading the file {os.path.basename(latest_file)}")
                        read_file_aloud(latest_file)
                    else:
                        speak("No supported file found in Downloads.")
            elif a==-1:
                speak("which link do you want me to click")
                link=listen()
                click_by_title(link)
                pyautogui.moveTo(1389, 136)
                pyautogui.click()
                time.sleep(1)
                pyautogui.moveTo(1389, 136)
                pyautogui.click()
        elif "scroll down" in command:
            pyautogui.scroll(-1000)
            speak("Scrolling down.")

        elif "scroll up" in command or "up" in command:
            pyautogui.scroll(1000)
            speak("Scrolling up.")

        elif "go back" in command:
            pyautogui.hotkey('alt', 'left')
            speak("Going back.")

        elif "go forward" in command:
            pyautogui.hotkey('alt', 'right')
            speak("Going forward.")

        elif "stop" in command or "bye" in command or "whatsapp" in command:
            speak("Exiting WhatsApp Command!")
            return "exit"

def execute_yt():
    speak("Do you have any command?")
    command = listen()
    time.sleep(0.5)
    if "search" in command or "find" in command:
            speak("Clicking the search bar. ")
            pyautogui.moveTo(612, 138) 
            pyautogui.click(clicks=3, interval=0.1)
            voice_to_type()
            time.sleep(1)
            speak("Do you want me to press the search button?")
            confirmation = listen()
            if "yes" in confirmation or "OK" in confirmation:
                speak("Pressing search.")
                time.sleep(1)
                pyautogui.moveTo(1250, 144)
                pyautogui.click()
                
            else:
                speak("Okay, not pressing search.")
    elif "click" in command or "video" in command:
        speak("Which video do you want me to click?")
        spoken_title = listen()
        click_by_title(spoken_title)

    elif "scroll down" in command:
        pyautogui.scroll(-1000)
        speak("Scrolling down")
    elif "scroll up" in command:
        pyautogui.scroll(1000)
        speak("Scrolling up")
    elif "go back" in command:
        pyautogui.hotkey('alt', 'left')
        speak("Going back")
    elif "go forward" in command:
        pyautogui.hotkey('alt', 'right')
        speak("Going forward")
    elif "close tab" in command:
        pyautogui.hotkey('ctrl', 'w')
        speak("Closing tab")
    elif "stop" in command or "bye" in command or "youtube" in command:
        speak("Exiting Youtube Command!")
        return "exit"
    elif "play" in command or "pause" in command or "poz" in command:
        pyautogui.hotkey('space')
    elif "mute" in command or "sound" in command:
        pyautogui.hotkey('m')
    elif "screen" in command or "full" in command or "exit" in command :
        pyautogui.hotkey('space')
    elif "forward" in command :
        pyautogui.hotkey('right')
    elif "back" in command :
        pyautogui.hotkey('left')

 

def execute_google():
    speak("Do you have any command ,you can say yes if you want to search again?")
    command = listen()
    time.sleep(0.5)
    if "search" in command or "find" in command or "yes" in command:
            speak("Clicking the search bar. ")
            pyautogui.moveTo(338, 164) 
            pyautogui.click(clicks=3, interval=0.1)
            voice_to_type()
            time.sleep(1)
            speak("Do you want me to press the search button?")
            confirmation = listen()
            if "yes" in confirmation or "OK" in confirmation:
                speak("Pressing search.")
                time.sleep(1)
                pyautogui.hotkey('enter')
                
            else:
                speak("Okay, not pressing search.")
    elif "scroll down" in command:
        pyautogui.scroll(-1000)
        speak("Scrolling down")
    elif "scroll up" in command or "up" in command :
        pyautogui.scroll(1000)
        speak("Scrolling up")
    elif "go back" in command:
        pyautogui.hotkey('alt', 'left')
        speak("Going back")
    elif "go forward" in command:
        pyautogui.hotkey('alt', 'right')
        speak("Going forward")
    elif "click" in command or "link" in command:
        speak("Which link do you want me to click?")
        spoken_title = listen()
        click_by_title(spoken_title)
    elif "stop" in command or "bye" in command or "google" in command:
        speak("Exiting google Command!")
        return "exit" 
def execute(command):
    if "open youtube" in command or "youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")
        while True:
            result =execute_yt()
            if result == "exit":
                break
    elif "open google" in command or "google" in command:
        speak("Opening Google")
        webbrowser.open("https://www.google.com")
        speak("Clicking the search bar. ")
        pyautogui.moveTo(638, 479) 
        pyautogui.click()
        voice_to_type()
        time.sleep(1)
        #Confirm if user wants to search
        speak("Do you want me to press the search button?")
        confirmation = listen()
        if "yes" in confirmation or "OK" in confirmation:
            speak("Pressing search.")
            time.sleep(1)
            pyautogui.hotkey('enter')
        else:
            speak("Okay, not pressing search.")
        while True:
            result =execute_google()
            if result == "exit":
                break
    elif "open whatsapp" in command or "whatsapp" in command:
        speak("Opening WhatsApp Web")
        webbrowser.open("https://web.whatsapp.com")
        while True:
            result =whatsapp_execute()
            if result == "exit":
                break
    elif "reminder" in command:
        speak("setting a reminder")
        webbrowser.open_new("https://calendar.google.com")
        while True:
            result =execute_reminder()
            if result == "exit":
                break   
    # elif "calendar"in command or "calender" in command:
    #     speak("Opening Google Calender")
    #     webbrowser.open("https://calendar.google.com/calendar/u/0/r")
    #     execute_calender()

    elif "type something" in command or "write something" in command:
        voice_to_type()
    elif "close tab" in command:
        pyautogui.hotkey('ctrl', 'w')
        speak("Closing tab")
    elif "exit" in command or "stop" in command or "bye" in command:
        speak("Goodbye!")
        exit()
    elif "copy link" in command or "copy URL" in command:
        speak("Copying the URL")
        pyautogui.moveTo(218,66)
        pyautogui.click(clicks=3, interval=0.1)
        pyautogui.hotkey('ctrl','c')
    

    else:
        speak("Sorry, I don't recognize that command.")

# Main loop with sleep/wake feature
sleeping = False  

if __name__ == "__main__":
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
