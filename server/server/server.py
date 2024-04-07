import sys
import socket
from .commands import execute_command, send_message, send_current_dir
from .logger import logger
from clients.client import (
    Client,
    list_of_connected_clients,
    connect_client,
    disconnect_client,
)
from .dirwalk import update_list_of_accessable_paths


def init_server(address: str, port: int) -> socket:
    logger.debug("server init")
    try:
        update_list_of_accessable_paths()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((address, port))
        server_socket.listen()
        return server_socket
    except (Exception, KeyboardInterrupt) as e:
        logger.error(f"server init error || Exception: {e}")
        return None


def start_server(server_socket: socket) -> None:
    while True:
        try:
            while True:
                client = accept_connection(server_socket)
                while True:
                    if not client:
                        break
                    request = client.get_socket().recv(4096)
                    if not request:
                        disconnect_client(client)
                        logger.debug(f"Connection lost with {client.get_address()}")
                        break

                    request = request.decode(encoding="UTF-8")
                    if request == "\n":
                        request = "None"
                    execute_command(request, client)
                    send_current_dir(request, client)

        except (Exception, ConnectionResetError, KeyboardInterrupt) as e:
            if not isinstance(e, KeyboardInterrupt):
                logger.error(
                    f"Connection lost with {client.get_address()} || Exception:{e}"
                )


def accept_connection(server_socket: socket) -> Client:
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client = connect_client(client_socket, client_address)
            if not client:
                return None
            logger.debug(f"Connection established from {client_address}")
            response = "Connection established\n".encode(encoding="UTF-8")
            send_message(client_socket, response)
            send_current_dir(response, client)
            list_of_connected_clients.append(client)
            return client
    except (Exception, KeyboardInterrupt) as e:
        if not isinstance(e, KeyboardInterrupt):
            logger.error(f"Connection acception error || Exception:{e}")
            return None
