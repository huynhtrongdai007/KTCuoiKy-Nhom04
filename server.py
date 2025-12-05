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