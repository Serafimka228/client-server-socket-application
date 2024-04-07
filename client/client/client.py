import os
import socket
import selectors
from client.consts import HOST, PORT

selector = selectors.DefaultSelector()


def disconnect_from_server(client_socket: socket) -> None:
    selector.unregister(client_socket)
    client_socket.close()


def receive_data(client_socket: socket) -> bytes:
    try:
        data: bytes = client_socket.recv(4096)
        if data:
            return data
        else:
            disconnect_from_server(client_socket)
    except (socket.timeout, socket.error, ConnectionResetError) as e:
        print(e)


def send_data(client_socket: socket, data: str) -> None:
    try:
        client_socket.send(data.encode(encoding="UTF-8"))
    except (socket.timeout, socket.error) as e:
        print(e)


def init_socket() -> socket:
    client_socket: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return client_socket


def connect_to_server(client_socket: socket) -> bool:
    try:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((HOST, PORT))
        client_socket.setblocking(False)
        selector.register(client_socket, selectors.EVENT_READ, None)
        return True
    except (socket.timeout, socket.error) as e:
        print(e)
        selector.unregister(client_socket)
        client_socket.close()
        return False


def start_client(client_socket: socket) -> None:
    while True:
        events = selector.select(timeout=0.1)
        if events:
            for key, mask in events:
                if mask & selectors.EVENT_READ:
                    message: str = receive_data(key.fileobj).decode(encoding="UTF-8")
                    print(message, end="")
        else:
            user_input = input()
            if user_input:
                if user_input.upper() == "QUIT":
                    disconnect_from_server(client_socket)
                    return
                else:
                    send_data(client_socket, user_input)
