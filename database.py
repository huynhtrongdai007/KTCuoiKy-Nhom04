import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "chat.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tạo bảng users
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (sender TEXT, receiver TEXT, content TEXT, timestamp TEXT, type TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, _hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
              (username, _hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def save_message(sender, receiver, content, msg_type="TEXT"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", 
              (sender, receiver, content, time_now, msg_type))
    conn.commit()
    conn.close()

def get_history(user):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT * FROM messages WHERE receiver='ALL' OR receiver=? OR sender=?''', (user, user))
    rows = c.fetchall()
    conn.close()
    return rows