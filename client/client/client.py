import os
import re
import sys
import tqdm
import socket
import selectors
from client.consts import HOST, PORT

import time

selector = selectors.DefaultSelector()
current_mode: str = "NORMAL"


def disconnect_from_server(client_socket: socket) -> None:
    try:
        selector.unregister(client_socket)
        client_socket.close()
    except (socket.timeout, socket.error):
        print(e)
        sys.exit(1)


def receive_data(client_socket: socket) -> bytes:
    try:
        data: bytes = client_socket.recv(1024)
        if data:
            return data
        else:
            disconnect_from_server(client_socket)
    except (socket.timeout, socket.error, ConnectionResetError) as e:
        print(e)
        return None


def send_data(client_socket: socket, data: str) -> None:
    try:
        client_socket.send(data.encode(encoding="UTF-8"))
    except (socket.timeout, socket.error) as e:
        print(e)


def init_socket() -> socket:
    try:
        client_socket: socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return client_socket
    except (socket.timeout, socket.error):
        print(e)
        sys.exit(1)


def connect_to_server(client_socket: socket) -> None:
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
        sys.exit(1)


def upload_file(client_socket: socket, request: str) -> None:
    global current_mode
    client_socket.setblocking(True)
    file_name: str = re.sub(r"upload ", "", request, 1, flags=re.IGNORECASE)
    file_size: int = os.path.getsize(file_name)
    send_data(client_socket, f"{file_name},{file_size}")
    with open(file_name, "rb") as f:
        progress_bar = tqdm.tqdm(
            unit="B", unit_scale=True, unit_divisor=1000, total=int(file_size)
        )
        while True:
            data: bytes = f.read(1024)
            if not data:
                break
            client_socket.sendall(data)
            progress_bar.update(1024)
        current_mode = "NORMAL"
    client_socket.setblocking(False)


def download_file(client_socket: socket) -> None:
    global current_mode
    client_socket.setblocking(True)
    header: str = receive_data(client_socket).decode(encoding="UTF-8")
    match = re.match(r"([^,]+),([^,]+)", header)
    file_size = int(match.group(2))
    file_name = re.search(r"\\([^\\]+)$", match.group(1)).group(1)
    with open(file_name, "wb") as f:
        progress_bar = tqdm.tqdm(
            unit="B", unit_scale=True, unit_divisor=1000, total=int(file_size)
        )
        received_bytes = 0
        while received_bytes < file_size:
            data: bytes = client_socket.recv(1024)
            if not data:
                current_mode = "NORMAL"
            else:
                f.write(data)
            progress_bar.update(1024)
            received_bytes += 1024
    current_mode = "NORMAL"
    client_socket.setblocking(False)


def check_events(client_socket: socket, events: list[tuple]) -> None:
    global current_mode
    if events:
        for key, mask in events:
            if current_mode == "DOWNLOAD":
                download_file(key.fileobj)
            else:
                message: str = receive_data(key.fileobj).decode(encoding="UTF-8")
                print(message, end="")
    else:
        user_input = input()
        if user_input:
            if user_input.upper() == "QUIT":
                disconnect_from_server(client_socket)
                return
            else:
                if re.match(r"^upload ", user_input, re.IGNORECASE):
                    current_mode = "UPLOAD"
                    send_data(client_socket, user_input)
                    upload_file(client_socket, user_input)
                    return
                if re.match(r"^download ", user_input, re.IGNORECASE):
                    current_mode = "DOWNLOAD"
                send_data(client_socket, user_input)


def start_client(client_socket: socket) -> None:
    try:
        while True:
            events = selector.select(timeout=0.1)
            check_events(client_socket, events)
    except (socket.timeout, socket.error, AttributeError) as e:
        print(f"Server closed connection: {e}")
        sys.exit(1)
