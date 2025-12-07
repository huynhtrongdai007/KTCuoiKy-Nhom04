import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import base64
import os
import time
from datetime import datetime
import winsound  

HOST = '127.0.0.1'
PORT = 55555

# --- CONSTANTS ---
TYPING_START = "__TYPING_START__"
TYPING_STOP = "__TYPING_STOP__"

# --- THEMES ---
THEMES = {
    "light": {
        "bg": "#f0f2f5",
        "card": "#ffffff",
        "text": "#050505",
        "gray": "#65676b",
        "sent_bg": "#0084ff",
        "sent_fg": "#ffffff",
        "recv_bg": "#e4e6eb",
        "recv_fg": "#050505",
        "input_bg": "#f0f2f5",
        "primary": "#0084ff",
        "hover": "#f2f2f2"
    },
    "dark": {
        "bg": "#18191a",
        "card": "#242526",
        "text": "#e4e6eb",
        "gray": "#b0b3b8",
        "sent_bg": "#0084ff",
        "sent_fg": "#ffffff",
        "recv_bg": "#3a3b3c",
        "recv_fg": "#e4e6eb",
        "input_bg": "#3a3b3c",
        "primary": "#2D88FF",
        "hover": "#3e4042"
    }
}

FONT_MAIN = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SMALL = ("Segoe UI", 8)

# Extended Emoji List
EMOJI_LIST = [
    "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
    "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚",
    "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩",
    "🥳", "😏", "😒", "😞", "😔", "ww", "😕", "🙁", "☹️", "😣",
    "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡", "🤬",
    "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗",
    "🤔", "🤭", "🤫", "🤥", "😶", "😐", "😑", "😬", "🙄", "😯",
    "😦", "😧", "😮", "😲", "🥱", "😴", "🤤", "😪", "😵", "🤐",
    "🥴", "🤢", "🤮", "🤧", "😷", "🤒", "🤕", "🤑", "🤠", "😈",
    "👋", "🤚", "🖐", "✋", "🖖", "👌", "🤏", "✌️", "🤞", "🤟",
    "🤘", "🤙", "👈", "👉", "👆", "👇", "👍", "👎", "✊", "👊",
    "👏", "🙌", "👐", "🤲", "🤝", "🙏", "❤️", "🧡", "💛", "💚",
    "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓",
    "💗", "💖", "💘", "💝", "🔥", "✨", "🌟", "💫", "💥", "💢",
    "💦", "💧", "💤", "💨", "👂", "👀", "👃", "👅", "👄", "🧠",
    "🦷", "🦴", "💪", "🦵", "🦶", "🧚", "🧜", "🧞", "🧟", "🧛"
]

# --- HELPER: SOUND ---
def play_notification_sound():
    try: winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except: pass

# --- CUSTOM WIDGETS ---
class EmojiPicker(tk.Toplevel):
    def __init__(self, parent, callback, theme_name):
        super().__init__(parent)
        self.callback = callback
        self.theme = THEMES[theme_name]
        self.overrideredirect(True) # Borderless
        self.attributes("-topmost", True)
        self.configure(bg=self.theme["card"], highlightthickness=1, highlightbackground=self.theme["gray"])
        
        # Grid Layout
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

        # Close on click outside
        self.bind("<FocusOut>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())
        
        # Position near mouse
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

# --- CLASS CỬA SỔ CHAT RIÊNG ---
class PrivateChatWindow:
    def __init__(self, parent_app, partner_name):
        self.parent = parent_app
        self.partner = partner_name
        self.client = parent_app.client
        self.my_name = parent_app.nickname
        self.current_theme = parent_app.current_theme_name
        
        # Typing logic
        self.is_typing = False
        self.last_typing_time = 0
        
        self.window = tk.Toplevel(parent_app.root)
        self.window.title(f"Nhắn riêng: {partner_name}")
        self.window.geometry("450x600")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_ui()
        self.apply_theme(self.current_theme)
        self.load_history()

    def setup_ui(self):
        # 1. Header
        self.header = tk.Frame(self.window, pady=10)
        self.header.pack(fill='x', side='top')
        self.lbl_name = tk.Label(self.header, text=self.partner, font=("Segoe UI", 16, "bold"))
        self.lbl_name.pack()
        self.lbl_status = tk.Label(self.header, text="Đang hoạt động", font=("Segoe UI", 9))
        self.lbl_status.pack()
        # Typing Label
        self.lbl_typing = tk.Label(self.header, text="", font=("Segoe UI", 9, "italic"))
        self.lbl_typing.pack()

        # 2. Input Area
        self.input_frame = tk.Frame(self.window, pady=10)
        self.input_frame.pack(side='bottom', fill='x')
        
        self.input_container = tk.Frame(self.input_frame)
        self.input_container.pack(fill='x', padx=15, pady=5)

        self.msg_entry = PlaceholderEntry(self.input_container, placeholder="Nhập tin nhắn...", font=("Segoe UI", 11), bd=0, highlightthickness=0)
        self.msg_entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(10, 5))
        self.msg_entry.bind("<Return>", self.send)
        self.msg_entry.bind("<KeyRelease>", self.on_key_release) # Detect Typing
        
        # Tools
        tk.Button(self.input_container, text="😀", command=self.show_emoji_picker, bd=0, cursor="hand2", font=("Segoe UI", 12)).pack(side='left', padx=2)
        tk.Button(self.input_container, text="📎", command=self.send_file, bd=0, cursor="hand2", font=("Segoe UI", 12)).pack(side='left', padx=2)

        self.btn_send = tk.Button(self.input_container, text="Gửi", command=self.send, font=("Segoe UI", 10, "bold"), bd=0, relief="flat", cursor="hand2")
        self.btn_send.pack(side='right', padx=(5, 0), ipadx=15, ipady=5)

        # 3. Chat Area
        self.text_area = scrolledtext.ScrolledText(self.window, font=FONT_MAIN, bd=0, padx=15, pady=15)
        self.text_area.pack(side='top', fill='both', expand=True)
        self.text_area.config(state='disabled')

    def apply_theme(self, theme_name):
        colors = THEMES[theme_name]
        self.window.configure(bg=colors["bg"])
        self.header.configure(bg=colors["primary"])
        self.lbl_name.configure(bg=colors["primary"], fg=colors["sent_fg"])
        self.lbl_status.configure(bg=colors["primary"], fg="#e0e0e0")
        self.lbl_typing.configure(bg=colors["primary"], fg=colors["sent_fg"])
        
        self.input_frame.configure(bg=colors["card"])
        self.input_container.configure(bg=colors["input_bg"])
        
        self.msg_entry.configure(bg=colors["input_bg"], insertbackground=colors["text"])
        self.msg_entry.default_fg_color = colors["text"]
        self.msg_entry.placeholder_color = colors["gray"]
        if self.msg_entry.get() == self.msg_entry.placeholder:
             self.msg_entry['fg'] = colors["gray"]
        else:
             self.msg_entry['fg'] = colors["text"]

        for child in self.input_container.winfo_children():
            if isinstance(child, tk.Button):
                if child['text'] == "Gửi":
                    child.configure(bg=colors["primary"], fg="white", activebackground=colors["sent_bg"])
                else:
                    child.configure(bg=colors["input_bg"], fg=colors["text"], activebackground=colors["recv_bg"])

        self.text_area.configure(bg=colors["bg"], fg=colors["text"])
        self.text_area.tag_config("me", justify='right', foreground=colors["primary"], spacing1=2, spacing3=2)
        self.text_area.tag_config("other", justify='left', foreground=colors["text"], spacing1=2, spacing3=2)
        self.text_area.tag_config("time", justify='center', foreground=colors["gray"], font=FONT_SMALL, spacing1=5)

    def show_emoji_picker(self):
        EmojiPicker(self.window, lambda e: self.msg_entry.insert(tk.INSERT, e), self.current_theme)

    # --- TYPING LOGIC ---
    def on_key_release(self, event):
        if self.msg_entry.get_actual().strip():
            self.last_typing_time = time.time()
            if not self.is_typing:
                self.is_typing = True
                self.client.send(f"MSG|{self.partner}|{TYPING_START}\n".encode('utf-8'))
                threading.Thread(target=self.check_typing_pause, daemon=True).start()

    def check_typing_pause(self):
        while self.is_typing:
            time.sleep(0.5)
            if time.time() - self.last_typing_time > 1.5: # 1.5s silence
                self.is_typing = False
                self.client.send(f"MSG|{self.partner}|{TYPING_STOP}\n".encode('utf-8'))
                break

    def set_typing_status(self, is_typing):
        if is_typing:
            self.lbl_typing.config(text=f"{self.partner} đang soạn tin...")
        else:
            self.lbl_typing.config(text="")

    def load_history(self):
        if self.partner in self.parent.private_history_cache:
            for item in self.parent.private_history_cache[self.partner]:
                sender, content, mtype, timestamp = item
                if content in [TYPING_START, TYPING_STOP]: continue # Filter logic
                if mtype == "TEXT":
                    self.display_text(sender, content, timestamp)

    def display_text(self, sender, content, timestamp=None):
        if content in [TYPING_START, TYPING_STOP]: return # Double Safety

        self.text_area.config(state='normal')
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        elif " " in timestamp: 
            timestamp = timestamp.split(" ")[1]

        if sender == self.my_name:
            tag = "me"
            name_disp = "" 
        else:
            tag = "other"
            name_disp = f"{sender}:\n"

        self.text_area.insert('end', f"\n{timestamp}\n", "time")
        
        if content.startswith("FILE_PRIVATE|"):
            try:
                _, fname, fdata = content.split("|", 2)
                self.text_area.insert('end', f"{name_disp}", tag)
                btn_text = f"📄 File: {fname} (Nhấn để tải)"
                btn = tk.Button(self.text_area, text=btn_text, font=("Segoe UI", 9, "bold"), 
                                bg="#e4e6eb", fg="black", bd=0, cursor="hand2",
                                command=lambda f=fname, d=fdata: self.parent.save_file_dialog(f, d))
                self.text_area.window_create('end', window=btn)
                self.text_area.insert('end', "\n", tag)
            except:
                self.text_area.insert('end', f"{name_disp}[Lỗi hiển thị file]\n", tag)
        else:
            self.text_area.insert('end', f"{name_disp}{content}", tag)
        
        self.text_area.yview('end')
        self.text_area.config(state='disabled')

    def send_file(self):
        fp = filedialog.askopenfilename()
        if fp:
            name = os.path.basename(fp)
            if os.path.getsize(fp) > 10*1024*1024: 
                messagebox.showwarning("Cảnh báo", "File quá lớn (>10MB)")
                return
            try:
                with open(fp, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                payload = f"FILE_PRIVATE|{name}|{data}"
                self.client.send(f"MSG|{self.partner}|{payload}\n".encode('utf-8'))
                self.display_text(self.my_name, payload)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.parent.add_to_private_cache(self.partner, self.my_name, payload, "TEXT", now_str)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể gửi file: {e}")

    def send(self, event=None):
        msg = self.msg_entry.get_actual().strip()
        if msg:
            self.client.send(f"MSG|{self.partner}|{msg}\n".encode('utf-8'))
            self.display_text(self.my_name, msg) 
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.parent.add_to_private_cache(self.partner, self.my_name, msg, "TEXT", now_str)
            self.msg_entry.delete(0, 'end')

    def on_close(self):
        if self.partner in self.parent.private_windows:
            del self.parent.private_windows[self.partner]
        self.window.destroy()

# --- CLASS CHÍNH ---
class ClientApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chat App")
        self.root.geometry("400x600")
        
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: self.client.connect((HOST, PORT))
        except: 
            messagebox.showerror("Lỗi", "Không kết nối được Server")
            return
        
        self.nickname = ""
        self.private_windows = {}
        self.private_history_cache = {} 
        self.running = True
        self.current_theme_name = "light"
        
        # Typing
        self.is_typing_public = False
        self.last_typing_public = 0
        self.typing_users = set()
        
        self.style = ttk.Style()
        self.style.theme_use('clam') 
        
        self.build_login_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    # --- THEME MANAGER ---
    def toggle_theme(self):
        self.current_theme_name = "dark" if self.current_theme_name == "light" else "light"
        self.apply_theme(self.current_theme_name) 
        for win in self.private_windows.values():
            win.apply_theme(self.current_theme_name)

    def apply_theme(self, theme_name):
        c = THEMES[theme_name]
        self.root.configure(bg=c["bg"])
        if hasattr(self, 'main_area'): 
            self.update_main_ui_theme(c)
        elif hasattr(self, 'login_card'): 
            self.update_login_ui_theme(c)

    def update_login_ui_theme(self, c):
        if not hasattr(self, 'login_card'): return
        self.login_card.configure(bg=c["card"])
        for w in self.login_card.winfo_children():
            if isinstance(w, tk.Label):
                if "Chat App" in w.cget("text"): 
                    w.configure(bg=c["bg"], fg=c["primary"]) 
                elif "Đăng nhập" in w.cget("text"):
                    w.configure(bg=c["card"], fg=c["text"])
                else: 
                    w.configure(bg=c["card"], fg=c["gray"])
            elif isinstance(w, tk.Entry):
                w.configure(bg=c["bg"], fg=c["text"], insertbackground=c["text"])
            elif isinstance(w, tk.Button):
                if w.cget("text").upper() == "ĐĂNG NHẬP":
                    w.configure(bg=c["primary"], fg="white")
                else:
                    w.configure(bg=c["card"], fg=c["primary"])

        for w in self.main_frame.winfo_children():
            if isinstance(w, tk.Label) and "Chat App" in w.cget("text"):
                w.configure(bg=c["bg"], fg=c["primary"])
        self.main_frame.configure(bg=c["bg"])

    def update_main_ui_theme(self, c):
        if not hasattr(self, 'main_area'): return
        
        self.sidebar.configure(bg=c["card"])
        for w in self.sidebar.winfo_children():
            if isinstance(w, tk.Label): w.configure(bg=c["card"], fg=c["gray"])
            if isinstance(w, tk.Listbox): w.configure(bg=c["card"], fg=c["text"], selectbackground=c["bg"], selectforeground=c["text"])
        
        self.main_area.configure(bg=c["bg"])
        self.header_frame.configure(bg=c["card"])
        self.header_label.configure(bg=c["card"], fg=c["text"])
        self.theme_btn.configure(bg=c["card"], fg=c["text"])
        self.lbl_typing_public.configure(bg=c["card"], fg=c["primary"]) # Update Typing Lbl
        
        self.chat_frame.configure(bg=c["bg"])
        self.text_area.configure(bg=c["card"], fg=c["text"])
        
        self.text_area.tag_config("me", foreground=c["primary"])
        self.text_area.tag_config("other", foreground=c["text"])
        self.text_area.tag_config("time_tag", foreground=c["gray"])
        
        self.input_container.configure(bg=c["card"])
        
        self.msg_entry.configure(bg=c["bg"], insertbackground=c["text"])
        self.msg_entry.default_fg_color = c["text"]
        self.msg_entry.placeholder_color = c["gray"]
        if self.msg_entry.get() == self.msg_entry.placeholder:
             self.msg_entry['fg'] = c["gray"]
        else:
             self.msg_entry['fg'] = c["text"]
        
        self.btn_send.configure(bg=c["primary"], fg=c["sent_fg"])
        self.btn_file.configure(bg=c["card"], fg=c["text"])
        self.btn_emoji.configure(bg=c["card"], fg=c["text"])

    def clear_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

    def add_to_private_cache(self, partner, sender, content, mtype="TEXT", timestamp=None):
        if content in [TYPING_START, TYPING_STOP]: return # Don't save typing signals to history
        if partner not in self.private_history_cache:
            self.private_history_cache[partner] = []
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.private_history_cache[partner].append((sender, content, mtype, timestamp))

    def build_login_ui(self):
        self.clear_ui()
        self.root.geometry("400x500")
        
        self.main_frame = tk.Frame(self.root, bg=THEMES["light"]["bg"])
        self.main_frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(self.main_frame, text="Chat App", font=("Segoe UI", 28, "bold"), fg=THEMES["light"]["primary"], bg=THEMES["light"]["bg"]).pack(pady=(0, 30))

        self.login_card = tk.Frame(self.main_frame, bg=THEMES["light"]["card"], padx=30, pady=30, relief='flat')
        self.login_card.pack(fill='both')

        tk.Label(self.login_card, text="Đăng nhập", font=("Segoe UI", 16, "bold")).pack(pady=(0, 20))
        
        tk.Label(self.login_card, text="Tài khoản", font=FONT_BOLD, anchor='w').pack(fill='x')
        self.entry_user = tk.Entry(self.login_card, font=("Segoe UI", 11), bd=0, highlightthickness=1, highlightbackground="#ddd")
        self.entry_user.pack(fill='x', ipady=5, pady=(5, 15))

        tk.Label(self.login_card, text="Mật khẩu", font=FONT_BOLD, anchor='w').pack(fill='x')
        self.entry_pass = tk.Entry(self.login_card, font=("Segoe UI", 11), show="•", bd=0, highlightthickness=1, highlightbackground="#ddd")
        self.entry_pass.pack(fill='x', ipady=5, pady=(5, 20))

        tk.Button(self.login_card, text="ĐĂNG NHẬP", command=self.login, bd=0, relief='flat', cursor='hand2', font=("Segoe UI", 10, "bold")).pack(fill='x', ipady=5, pady=5)
        tk.Button(self.login_card, text="Đăng ký tài khoản mới", command=self.register, bd=0, relief='flat', cursor='hand2', font=("Segoe UI", 9)).pack(pady=10)

        self.apply_theme(self.current_theme_name)

    def login(self):
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        if user and pwd:
            self.client.send(f"LOGIN|{user}|{pwd}\n".encode('utf-8'))
            try:
                resp = self.client.recv(1024).decode()
                if "LOGIN_OK" in resp:
                    self.nickname = user
                    self.build_main_ui()
                    threading.Thread(target=self.receive_loop, daemon=True).start()
                else: messagebox.showerror("Lỗi", "Thông tin đăng nhập không đúng!")
            except: pass

    def register(self):
        user = self.entry_user.get()
        pwd = self.entry_pass.get()
        if user and pwd:
            self.client.send(f"REGISTER|{user}|{pwd}\n".encode('utf-8'))
            try:
                resp = self.client.recv(1024).decode()
                if "REG_OK" in resp: messagebox.showinfo("Thành công", "Đăng ký thành công! Hãy đăng nhập.")
                else: messagebox.showerror("Lỗi", "Tên tài khoản đã tồn tại!")
            except: pass

    def show_emoji_picker(self):
        EmojiPicker(self.root, lambda e: self.msg_entry.insert(tk.INSERT, e), self.current_theme_name)

    def build_main_ui(self):
        self.clear_ui()
        self.root.geometry("900x650")
        self.root.title(f"Chat App - {self.nickname}")
        
        self.sidebar = tk.Frame(self.root, width=220)
        self.sidebar.pack(side='right', fill='y')
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="TRỰC TUYẾN", font=("Segoe UI", 10, "bold"), anchor='w').pack(fill='x', padx=15, pady=15)
        
        self.user_listbox = tk.Listbox(self.sidebar, font=FONT_MAIN, bd=0, highlightthickness=0, activestyle='none')
        self.user_listbox.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.user_listbox.bind('<Double-1>', self.open_private_chat)

        self.main_area = tk.Frame(self.root)
        self.main_area.pack(side='left', fill='both', expand=True)

        self.header_frame = tk.Frame(self.main_area, height=70) # Taller for status
        self.header_frame.pack(fill='x')
        
        # Title
        self.header_label = tk.Label(self.header_frame, text="Phòng Chat Chung", font=("Segoe UI", 12, "bold"))
        self.header_label.pack(side='left', padx=20, pady=(15,0))
        
        # Theme Button
        self.theme_btn = tk.Button(self.header_frame, text="🌙/☀️", command=self.toggle_theme, bd=0, cursor="hand2", font=("Segoe UI", 12))
        self.theme_btn.pack(side='right', padx=20, pady=15)

        # Typing Label (Under Title)
        self.lbl_typing_public = tk.Label(self.header_frame, text="", font=("Segoe UI", 9, "italic"))
        self.lbl_typing_public.place(x=20, y=45) 

        self.chat_frame = tk.Frame(self.main_area)
        self.chat_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.text_area = scrolledtext.ScrolledText(self.chat_frame, font=FONT_MAIN, bd=0, padx=15, pady=15)
        self.text_area.pack(fill='both', expand=True)
        self.text_area.config(state='disabled')
        
        self.text_area.tag_config("sys", foreground="red", font=("Segoe UI", 9, "italic"))
        self.text_area.tag_config("content_line", spacing3=5)

        self.input_container = tk.Frame(self.main_area, pady=10, padx=20)
        self.input_container.pack(fill='x')

        self.msg_entry = PlaceholderEntry(self.input_container, placeholder="Nhập tin nhắn chung...", font=("Segoe UI", 11), bd=0, highlightthickness=1, highlightbackground="#ddd")
        self.msg_entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(0, 10))
        self.msg_entry.bind("<Return>", self.send_public)
        self.msg_entry.bind("<KeyRelease>", self.on_public_key_release)

        self.btn_emoji = tk.Button(self.input_container, text="😀", command=self.show_emoji_picker, bd=0, cursor="hand2", font=("Segoe UI", 12))
        self.btn_emoji.pack(side='left', padx=2)
        
        self.btn_file = tk.Button(self.input_container, text="📎", command=self.send_file, bd=0, cursor="hand2", font=("Segoe UI", 12))
        self.btn_file.pack(side='left', padx=2)

        self.btn_send = tk.Button(self.input_container, text="Gửi", command=self.send_public, font=("Segoe UI", 10, "bold"), bd=0, relief="flat", cursor="hand2")
        self.btn_send.pack(side='left', padx=(5, 0), ipady=5, ipadx=15)
        
        self.apply_theme(self.current_theme_name)

    # --- PUBLIC TYPING ---
    def on_public_key_release(self, event):
        if self.msg_entry.get_actual().strip():
            self.last_typing_public = time.time()
            if not self.is_typing_public:
                self.is_typing_public = True
                self.client.send(f"MSG|ALL|{TYPING_START}\n".encode('utf-8'))
                threading.Thread(target=self.check_public_pause, daemon=True).start()

    def check_public_pause(self):
        while self.is_typing_public:
            time.sleep(0.5)
            if time.time() - self.last_typing_public > 1.5:
                self.is_typing_public = False
                self.client.send(f"MSG|ALL|{TYPING_STOP}\n".encode('utf-8'))
                break

    def update_public_typing_lbl(self):
        if not self.typing_users:
            self.lbl_typing_public.config(text="")
        else:
            names = ", ".join(list(self.typing_users)[:3])
            ext = "..." if len(self.typing_users) > 3 else ""
            self.lbl_typing_public.config(text=f"{names}{ext} đang soạn tin...")

    def save_file_dialog(self, filename, file_data):
        save_path = filedialog.asksaveasfilename(initialfile=filename, title="Lưu tệp")
        if save_path:
            try:
                with open(save_path, "wb") as f:
                    f.write(base64.b64decode(file_data))
                messagebox.showinfo("Thành công", f"Đã lưu: {save_path}")
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

    def send_public(self, event=None):
        msg = self.msg_entry.get_actual().strip()
        if msg:
            self.client.send(f"MSG|ALL|{msg}\n".encode('utf-8'))
            self.msg_entry.delete(0, 'end')

    def send_file(self):
        fp = filedialog.askopenfilename()
        if fp:
            name = os.path.basename(fp)
            if os.path.getsize(fp) > 10*1024*1024: 
                messagebox.showwarning("Cảnh báo", "File quá lớn (>10MB)")
                return
            with open(fp, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            self.client.send(f"FILE|{name}|{data}\n".encode('utf-8'))

    def open_private_chat(self, event):
        sel = self.user_listbox.curselection()
        if sel:
            val = self.user_listbox.get(sel[0])
            if " " in val:
                target = val.split(" ", 1)[1]
                if target != self.nickname: self.create_private_window(target)

    def create_private_window(self, target):
        if target not in self.private_windows:
            win = PrivateChatWindow(self, target)
            self.private_windows[target] = win
        else: self.private_windows[target].window.lift()

    def receive_loop(self):
        while self.running:
            try:
                raw_data = self.client.recv(1024*1024*10).decode('utf-8')
                if not raw_data: break
                messages = raw_data.split("\n")
                
                for msg in messages:
                    if not msg: continue

                    if msg.startswith("LIST|"):
                        self.update_list(msg.split("|", 1)[1])

                    elif msg.startswith("MSG|"):
                        _, sender, receiver, content = msg.split("|", 3)
                        
                        # --- TYPING HANDLING ---
                        if content == TYPING_START:
                            if receiver == "ALL":
                                if sender != self.nickname:
                                    self.typing_users.add(sender)
                                    self.root.after(0, self.update_public_typing_lbl)
                            else:
                                if sender in self.private_windows:
                                    self.root.after(0, lambda s=sender: self.private_windows[s].set_typing_status(True))
                            continue # Skip msg processing

                        elif content == TYPING_STOP:
                            if receiver == "ALL":
                                if sender in self.typing_users:
                                    self.typing_users.remove(sender)
                                    self.root.after(0, self.update_public_typing_lbl)
                            else:
                                if sender in self.private_windows:
                                    self.root.after(0, lambda s=sender: self.private_windows[s].set_typing_status(False))
                            continue # Skip msg processing

                        # Normal Message
                        if sender != self.nickname:
                            play_notification_sound()
                            
                        if receiver == "ALL":
                            self.display_public_text(sender, content)
                        else:
                            partner = sender
                            self.add_to_private_cache(partner, sender, content)
                            if partner in self.private_windows:
                                self.root.after(0, lambda p=partner, s=sender, c=content: 
                                                self.private_windows[p].display_text(s, c))

                    elif msg.startswith("HISTORY|"):
                        parts = msg.split("|", 5)
                        if len(parts) < 6: continue
                        _, sender, receiver, content, timestamp, mtype = parts
                        
                        if content in [TYPING_START, TYPING_STOP]: continue

                        short_time = timestamp.split(" ")[1] if " " in timestamp else timestamp

                        if mtype == "FILE":
                            try:
                                if "|" in content:
                                    f_name, f_data = content.split("|", 1)
                                    if receiver == "ALL":
                                        self.display_public_file(sender, f_name, f_data, is_history=True)
                            except: pass
                        else:
                            if receiver == "ALL":
                                self.display_public_text(sender, f"[History] {content}", short_time)
                            else:
                                partner = sender if sender != self.nickname else receiver
                                self.add_to_private_cache(partner, sender, f"[History] {content}", "TEXT", timestamp)

                    elif msg.startswith("FILE|"):
                        _, sender, fname, fdata = msg.split("|", 3)
                        if sender != self.nickname: play_notification_sound()
                        self.display_public_file(sender, fname, fdata)

            except: break

    def display_public_text(self, sender, content, timestamp=None):
        if content in [TYPING_START, TYPING_STOP]: return

        self.text_area.config(state='normal')
        
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        elif " " in timestamp:
             timestamp = timestamp.split(" ")[1]
            
        time_str = f"[{timestamp}] "
        
        if sender == "System":
            prefix = "Hệ thống: "
            tag = "sys"
        elif sender == self.nickname:
            prefix = "Tôi: "
            tag = "me"
        else:
            prefix = f"{sender}: "
            tag = "other"
        
        self.text_area.insert('end', time_str, "time_tag")
        self.text_area.insert('end', prefix, tag)
        self.text_area.insert('end', content + '\n', "content_line")
        self.text_area.yview('end')
        self.text_area.config(state='disabled')

    def display_public_file(self, sender, filename, file_data, is_history=False):
        self.text_area.config(state='normal')
        prefix_text = "Tôi" if sender == self.nickname else sender
        
        info = "đã gửi file:" if not is_history else "File (Lịch sử):"
        
        self.text_area.insert('end', f"\n[{prefix_text} {info}]\n", "sys")
        
        btn = tk.Button(self.text_area, text=f"📎 Tải về: {filename}", font=("Segoe UI", 9, "bold"), bg="#ddd", bd=0, cursor="hand2",
                        command=lambda f=filename, d=file_data: self.save_file_dialog(f, d))
        self.text_area.window_create('end', window=btn)
        self.text_area.insert('end', '\n\n')
        self.text_area.yview('end')
        self.text_area.config(state='disabled')

    def update_list(self, data):
        self.user_listbox.delete(0, 'end')
        for u in data.split(","):
            if ":" in u:
                name, st = u.split(":")
                icon = "●" if st == "ON" else "○"
                color = "#4cd137" if st == "ON" else THEMES[self.current_theme_name]["gray"]
                self.user_listbox.insert('end', f"{icon} {name}")
                self.user_listbox.itemconfig('end', {'fg': color})

    def on_closing(self):
        self.running = False
        try: self.client.send(f"MSG|ALL|{TYPING_STOP}\n".encode('utf-8'))
        except: pass
        try: self.client.close()
        except: pass
        self.root.destroy()

if __name__ == "__main__":
    ClientApp()