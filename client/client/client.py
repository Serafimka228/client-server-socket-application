import os
import socket
from client.consts import HOST, PORT


def connect_to_server(client_socket: socket) -> bool:
    try:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((HOST, PORT))
        data = receive_data(client_socket)
        print(data)
        return True
    except (socket.timeout, socket.error):
        return False


def receive_data(client_socket: socket) -> str:
    try:
        data = client_socket.recv(4096).decode(encoding="UTF-8")
        return data
    except (socket.timeout, socket.error, ConnectionResetError):
        pass
