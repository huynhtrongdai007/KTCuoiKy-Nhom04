import socket
import threading
import database
import time

HOST = '127.0.0.1'
PORT = 55555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = {} 
database.init_db()

def send_to_client(client, message):
    try:
        client.send((message + "\n").encode('utf-8'))
    except: pass

def broadcast(message):
    for client in clients.values():
        send_to_client(client, message)

def broadcast_user_list():
    try:
        all_users = database.get_all_users()
        online_users = list(clients.keys())
        status_list = []
        for user in all_users:
            status = "ON" if user in online_users else "OFF"
            status_list.append(f"{user}:{status}")
        payload = "LIST|" + ",".join(status_list)
        broadcast(payload)
    except: pass
    def handle_client(client):
    nickname = None
    while True:
        try:
            # Buffer lớn để nhận file
            raw_data = client.recv(1024*1024*10).decode('utf-8')
            if not raw_data: break
            messages = raw_data.split("\n")

            for msg in messages:
                if not msg: continue

                if msg.startswith("REGISTER|"):
                    _, user, pwd = msg.split("|")
                    if database.register_user(user, pwd):
                        send_to_client(client, "REG_OK")
                        broadcast_user_list()
                    else: send_to_client(client, "REG_FAIL")
                
                elif msg.startswith("LOGIN|"):
                    _, user, pwd = msg.split("|")
                    if database.check_login(user, pwd):
                        nickname = user
                        clients[nickname] = client
                        send_to_client(client, "LOGIN_OK")
                        print(f"[LOG] {nickname} joined.")
                        
                        # --- GỬI LỊCH SỬ KÈM THỜI GIAN ---
                        history = database.get_history(nickname)
                        for row in history:
                            # row: (sender, receiver, content, timestamp, type)
                            # Gửi: HISTORY | sender | receiver | content | timestamp | type
                            h_msg = f"HISTORY|{row[0]}|{row[1]}|{row[2]}|{row[3]}|{row[4]}"
                            send_to_client(client, h_msg)
                            time.sleep(0.01)
                            
                        broadcast(f"MSG|System|ALL|{nickname} đã tham gia!")
                        broadcast_user_list()
                    else: send_to_client(client, "LOGIN_FAIL")

                elif msg.startswith("MSG|"):
                    _, receiver, content = msg.split("|", 2)
                    if receiver == "ALL":
                        broadcast(f"MSG|{nickname}|ALL|{content}")
                        database.save_message(nickname, "ALL", content, "TEXT")
                    else:
                        if receiver in clients:
                            send_to_client(clients[receiver], f"MSG|{nickname}|{receiver}|{content}")
                        database.save_message(nickname, receiver, content, "TEXT")

                elif msg.startswith("FILE|"):
                    _, fname, data = msg.split("|", 2)
                    broadcast(f"FILE|{nickname}|{fname}|{data}")
                    database.save_message(nickname, "ALL", f"{fname}|{data}", "FILE")

        except:
            if nickname and nickname in clients:
                del clients[nickname]
                broadcast(f"MSG|System|ALL|{nickname} đã thoát.")
                broadcast_user_list()
            client.close()
            break

def receive():
    print(f"--- SERVER RUNNING AT {HOST}:{PORT} ---")
    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == "__main__":
    receive()