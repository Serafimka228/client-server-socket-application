import sys
import socket
import selectors
from .commands import execute_command, send_message, send_current_dir
from .logger import logger
from clients.client import (
    Client,
    list_of_connected_clients,
    connect_client,
    disconnect_client,
)
from .dirwalk import update_list_of_accessable_paths


selector = selectors.DefaultSelector()


def accept_connection(server_socket: socket) -> None:
    try:
        client_socket, client_address = server_socket.accept()
        client_socket.setblocking(False)
        client = connect_client(client_socket, client_address)
        if not client:
            return None
        logger.debug(f"Connection established from {client_address}")
        response = "Connection established\n".encode(encoding="UTF-8")
        selector.register(client_socket, selectors.EVENT_READ, client)
        send_message(client_socket, response)
        send_current_dir(response, client)
        list_of_connected_clients.append(client)
    except (Exception, KeyboardInterrupt) as e:
        if not isinstance(e, KeyboardInterrupt):
            logger.error(f"Connection acception error || Exception:{e}")


def init_server(address: str, port: int) -> socket:
    logger.debug("server init")
    try:
        update_list_of_accessable_paths()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((address, port))
        server_socket.listen()
        server_socket.setblocking(False)
        selector.register(server_socket, selectors.EVENT_READ, accept_connection)
        return server_socket
    except (Exception, KeyboardInterrupt) as e:
        logger.error(f"server init error || Exception: {e}")
        return None


def handle_request(client: Client) -> None:
    try:
        if not client:
            return

        request = client.get_socket().recv(4096)
        if not request:
            disconnect_client(client)
            logger.debug(f"Connection lost with {client.get_address()}")
            return
        request = request.decode(encoding="UTF-8")
        if request == "\n":
            request = "None"
        execute_command(request, client)
        send_current_dir(request, client)
    except (Exception, ConnectionResetError) as e:
        logger.error(f"Connection lost with {client.get_address()} || Exception:{e}")


def start_server(server_socket: socket) -> None:
    while True:
        events = selector.select()
        for key, mask in events:
            callback = key.data
            if callback == accept_connection:
                callback(server_socket)
            else:
                handle_request(callback)
