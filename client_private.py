import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import base64
import os
import time
import threading
from datetime import datetime

from client_config import THEMES, FONT_MAIN, FONT_SMALL, TYPING_START, TYPING_STOP
from client_assets import PlaceholderEntry, EmojiPicker

class PrivateChatWindow:
    def __init__(self, parent_app, partner_name):
        self.parent = parent_app
        self.partner = partner_name
        self.client = parent_app.client
        self.my_name = parent_app.nickname
        self.current_theme = parent_app.current_theme_name
        
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
        self.header = tk.Frame(self.window, pady=10)
        self.header.pack(fill='x', side='top')
        self.lbl_name = tk.Label(self.header, text=self.partner, font=("Segoe UI", 16, "bold"))
        self.lbl_name.pack()
        self.lbl_status = tk.Label(self.header, text="Đang hoạt động", font=("Segoe UI", 9))
        self.lbl_status.pack()
        self.lbl_typing = tk.Label(self.header, text="", font=("Segoe UI", 9, "italic"))
        self.lbl_typing.pack()

        self.input_frame = tk.Frame(self.window, pady=10)
        self.input_frame.pack(side='bottom', fill='x')
        
        self.input_container = tk.Frame(self.input_frame)
        self.input_container.pack(fill='x', padx=15, pady=5)

        self.msg_entry = PlaceholderEntry(self.input_container, placeholder="Nhập tin nhắn...", font=("Segoe UI", 11), bd=0, highlightthickness=0)
        self.msg_entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(10, 5))
        self.msg_entry.bind("<Return>", self.send)
        self.msg_entry.bind("<KeyRelease>", self.on_key_release)
        
        tk.Button(self.input_container, text="😀", command=self.show_emoji_picker, bd=0, cursor="hand2", font=("Segoe UI", 12)).pack(side='left', padx=2)
        tk.Button(self.input_container, text="📎", command=self.send_file, bd=0, cursor="hand2", font=("Segoe UI", 12)).pack(side='left', padx=2)

        self.btn_send = tk.Button(self.input_container, text="Gửi", command=self.send, font=("Segoe UI", 10, "bold"), bd=0, relief="flat", cursor="hand2")
        self.btn_send.pack(side='right', padx=(5, 0), ipadx=15, ipady=5)

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
            if time.time() - self.last_typing_time > 1.5:
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
                if content in [TYPING_START, TYPING_STOP]: continue
                if mtype == "TEXT":
                    self.display_text(sender, content, timestamp)

    def display_text(self, sender, content, timestamp=None):
        if content in [TYPING_START, TYPING_STOP]: return

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
