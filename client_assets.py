import tkinter as tk
import winsound
from client_config import THEMES

# --- RESOURCES ---
EMOJI_LIST = [
    "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
    "🙂", "🙃", "😉", "😌", "😍", "🥰", "😗", "😙", "😚", "😋", "😛",
    "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩", "🥳", "😏", "😒",
    "😞", "😔", "ww", "😕", "🙁", "☹️", "😣", "😖", "😫", "😩", "🥺",
    "😢", "😭", "😤", "😠", "😡", "🤬", "🤯", "😳", "🥵", "🥶", "😱",
    "😨", "😰", "😥", "😓", "🤗", "🤔", "🤭", "🤫", "🤥", "😶", "😐",
    "😑", "😬", "🙄", "😯", "😦", "😧", "😮", "😲", "🥱", "😴", "🤤",
    "😪", "😵", "🤐", "🥴", "🤢", "🤮", "🤧", "😷", "🤒", "🤕", "🤑",
    "🤠", "😈", "👋", "🤚", "🖐", "✋", "🖖", "👌", "🤏", "✌️", "🤞",
    "🤟", "🤘", "🤙", "👈", "👉", "👆", "👇", "👍", "👎", "✊", "👊",
    "👏", "🙌", "👐", "🤲", "🤝", "🙏", "❤️", "🧡", "💛", "💚", "💙",
    "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖",
    "💘", "💝", "🔥", "✨", "🌟", "💫", "💥", "💢", "💦", "💧", "💤",
    "💨", "👂", "👀", "👃", "👅", "👄", "🧠", "🦷", "🦴", "💪", "🦵",
    "🦶", "🧚", "🧜", "🧞", "🧟", "🧛"
]

def play_notification_sound():
    try: winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except: pass

# --- WIDGETS ---
class EmojiPicker(tk.Toplevel):
    def __init__(self, parent, callback, theme_name):
        super().__init__(parent)
        self.callback = callback
        self.theme = THEMES[theme_name]
        self.overrideredirect(True) # Borderless
        self.attributes("-topmost", True)
        self.configure(bg=self.theme["card"], highlightthickness=1, highlightbackground=self.theme["gray"])
        
        rows = 8
        cols = 10
        frame = tk.Frame(self, bg=self.theme["card"], padx=5, pady=5)
        frame.pack()

        for idx, emo in enumerate(EMOJI_LIST):
            if idx >= rows * cols: break
            r, c = divmod(idx, cols)
            btn = tk.Button(frame, text=emo, font=("Segoe UI Emoji", 12), bg=self.theme["card"], fg=self.theme["text"],
                            bd=0, relief="flat", activebackground=self.theme["hover"], cursor="hand2",
                            command=lambda e=emo: self.on_select(e))
            btn.grid(row=r, column=c, padx=1, pady=1)

        self.bind("<FocusOut>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())
        x = parent.winfo_pointerx()
        y = parent.winfo_pointery()
        self.geometry(f"+{x-150}+{y-250}") 
        self.focus_force()

    def on_select(self, emoji):
        self.callback(emoji)
        self.destroy()

class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey', **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = kwargs.get('fg', 'black')
        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color and self.get() == self.placeholder:
            self.delete(0, 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()
            
    def get_actual(self):
        if self['fg'] == self.placeholder_color and self.get() == self.placeholder:
            return ''
        return self.get()
