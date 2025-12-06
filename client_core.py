import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import socket
import threading
import os
import base64
from datetime import datetime

from client_config import HOST, PORT, THEMES, TYPING_START, TYPING_STOP
from client_assets import play_notification_sound, EmojiPicker
from client_auth import AuthMixin
from client_main_ui import MainUIMixin

class ClientApp(AuthMixin, MainUIMixin):
    """
    Main Application Core.
    Inherits from Mixins to compose functionality.
    """
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

    # --- SHARED HELPERS (Used by Mixins) ---
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

    def clear_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

    def show_emoji_picker(self):
        EmojiPicker(self.root, lambda e: self.msg_entry.insert(tk.INSERT, e), self.current_theme_name)

    def add_to_private_cache(self, partner, sender, content, mtype="TEXT", timestamp=None):
        if content in [TYPING_START, TYPING_STOP]: return 
        if partner not in self.private_history_cache:
            self.private_history_cache[partner] = []
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.private_history_cache[partner].append((sender, content, mtype, timestamp))

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
                        
                        if content == TYPING_START:
                            if receiver == "ALL":
                                if sender != self.nickname:
                                    self.typing_users.add(sender)
                                    self.root.after(0, self.update_public_typing_lbl)
                            else:
                                if sender in self.private_windows:
                                    self.root.after(0, lambda s=sender: self.private_windows[s].set_typing_status(True))
                            continue 

                        elif content == TYPING_STOP:
                            if receiver == "ALL":
                                if sender in self.typing_users:
                                    self.typing_users.remove(sender)
                                    self.root.after(0, self.update_public_typing_lbl)
                            else:
                                if sender in self.private_windows:
                                    self.root.after(0, lambda s=sender: self.private_windows[s].set_typing_status(False))
                            continue 

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
