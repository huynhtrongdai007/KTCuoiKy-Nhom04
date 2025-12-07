import tkinter as tk
from tkinter import scrolledtext
import threading
import time

from client_config import THEMES, FONT_MAIN, TYPING_START, TYPING_STOP
from client_assets import PlaceholderEntry
from client_private import PrivateChatWindow

class MainUIMixin:
    """Mixin responsible for Main Chat Interface UI."""

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
