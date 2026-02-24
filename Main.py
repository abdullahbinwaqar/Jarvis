from kivy.app import App
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager
import subprocess
import messagebox
from google import genai
import re

api_key = "Your_API_Key"

client = genai.Client(api_key=api_key)

BLACKLIST_COMMANDS = {
    "del",        # delete files
    "erase",      # delete files
    "format",     # format drives
    "rd",         # remove directories
    "shutdown",   # shutdown or restart
    "reboot",     # restart system
    "taskkill",   # kill processes
    "attrib",     # modify system file attributes
    "reg delete", # delete registry keys
    "mklink",     # dangerous symbolic links
    ":(){",       # fork bomb
    ">",          # overwrite files
    "copy con",   # overwrite files
}

PREDEFINED_COMMANDS = {
    "smss": [
        'cmd /c start chrome --profile-directory="Profile 1"',
        'cmd /c start chrome "https://classroom.google.com/"',
        'cmd /c start chrome "https://chat.openai.com/"',
        'cmd /c start chrome "https://web.whatsapp.com/"',
        'cmd /c start chrome "https://www.youtube.com/"'
    ],
    "classroom": ['cmd /c start chrome "https://classroom.google.com/"'],
    "chatgpt": ['cmd /c start chrome "https://chat.openai.com/"'],
    "whatsapp": ['cmd /c start chrome "https://web.whatsapp.com/"'],
    "chrome": ['cmd /c start chrome'],
    "edge": ['cmd /c start msedge'],
    "spotify": ['cmd /c start spotify'],
    "youtube": ['cmd /c start chrome "https://www.youtube.com/"']
}

def is_safe_command(cmd):
    cmd_clean = cmd.lower().strip()
    for blackCMD in BLACKLIST_COMMANDS:
        if blackCMD in cmd_clean:
            return False
    return True

POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

def clean_command(gemini_text):
    # Lowercase, remove quotes, remove extra punctuation
    cmd = gemini_text.lower()
    cmd = cmd.replace('"', '').replace("'", "")
    cmd = re.sub(r'[^a-z0-9:/?&.= ]', '', cmd)  # keep only safe chars
    return cmd.strip()

def run_command(command):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Only give the CMD command to " + command + " nothing else."
        )
        gemini_text = response.text.strip()
        cmd = clean_command(gemini_text)
        find = "cmdstart "
        if find in cmd:
            cmd.removeprefix(find)

        # Check against blacklist
        if is_safe_command(cmd):
            # Use cmd /c to ensure CMD internal commands like 'start' work
            subprocess.run(f"cmd /c {cmd}", shell=True)
        else:
            messagebox.showerror("Blocked!", "Harmful command blocked!")
            speak("This command has been blocked by the system for safety.")

    except Exception as e:
        messagebox.showerror("Error", f"Command not recognized.\n{e}")
        speak("The command could not be executed.")

def speak(text):
    command = f'''
    Add-Type -AssemblyName System.Speech
    $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $speak.Speak("{text}")
    '''
    subprocess.run(
        [POWERSHELL, "-NoProfile", "-Command", command],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

Window.size = (360, 640)

class ChatListScreen(Screen):
    pass

class ChatScreen(Screen):
    pass


class MainApp(App):
    menu_open = False

    def toggle_menu(self):
        menu = self.root.get_screen("home").ids.side_menu
        if self.menu_open:
            Animation(x=-menu.width, duration=0.25).start(menu)
        else:
            Animation(x=0, duration=0.25).start(menu)
        self.menu_open = not self.menu_open
        

    def touched(self):
        print("Button touched!")

    def open_chat(self):
        self.root.current = "chat"

    def go_home(self):
        self.root.current = "home"
        
    def command(self, text):
        text_lower = text.lower()
        if text_lower in PREDEFINED_COMMANDS:
            for cmd in PREDEFINED_COMMANDS[text_lower]:
                try:
                    subprocess.run(cmd, shell=True)
                except:
                    speak(f"Failed to open {text_lower}")
        else:
            run_command(text)
            

Builder.load_file("main.kv")

if __name__ == "__main__":
    speak("Jarvis Activated")
    MainApp().run()
    
