import tkinter as tk
from tkinter import messagebox
import threading
from client_config import THEMES, FONT_BOLD

class AuthMixin:
    """Mixin responsible for Authentication (Login/Register) UI and Logic."""
    
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
