import socket
import re
from datetime import datetime
from .logger import logger
from clients.client import disconnect_client, Client
from .dirwalk import list_directories, list_of_accessable_paths


class commands:
    @staticmethod
    def ECHO(request: str, client: Client) -> bool:
        try:
            request = re.sub(r"echo ", "", request, 1, flags=re.IGNORECASE)
            send_message(client.get_socket(), request.encode(encoding="UTF-8"))
            return True
        except Exception as e:
            logger.error(f"ECHO Exception: {e}")
            return False

    @staticmethod
    def TIME(_, client: Client) -> bool:
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            send_message(
                client.get_socket(), (str(current_time) + "\n").encode(encoding="UTF-8")
            )
            return True
        except Exception as e:
            logger.error(f"TIME Exception: {e}")
            return False

    @staticmethod
    def QUIT(request: str, client: Client) -> bool:
        try:
            send_message(
                client.get_socket(), "Connection closed".encode(encoding="UTF-8")
            )
            disconnect_client(client)
            client.get_socket().close()
            return True
        except Exception as e:
            logger.error(f"QUIT Exception: {e}")
            return False

    @staticmethod
    def CD(request: str, client: Client) -> bool:
        try:
            print(f"req = {request}")
            path = request = re.sub(r"cd ", "", request, 1, flags=re.IGNORECASE)
            path = path.split()
            print(f"path = {path}")
            print(client.get_access_rights())
            print(f"list {list_of_accessable_paths}")
            accessable_paths = list_of_accessable_paths.get(
                client.get_access_rights(), []
            )
            print(accessable_paths)
            if path not in accessable_paths:
                return False
            if path == "..":
                pass
            if not path:
                return False
            client.change_current_catalog(path[0])
            return True
        except Exception as e:
            logger.error(f"CD Exception: {e}")
            return False

    @staticmethod
    def LIST(request: str, client: Client) -> bool:
        try:
            directories: list = list_directories(client.get_current_catalog())
            for directory in directories:
                send_message(
                    client.get_socket(), (directory + "\n").encode(encoding="UTF-8")
                )
            return True
        except Exception as e:
            logger.error(f"LIST Exception: {e}")
            return False

    @staticmethod
    def UPLOAD(request: str, client: Client) -> bool:
        pass

    @staticmethod
    def DOWNLOAD(request: str, client: Client) -> bool:
        pass


list_of_commands = {
    "ECHO": commands.ECHO,
    "TIME": commands.TIME,
    "UPLOAD": commands.UPLOAD,
    "DOWNLOAD": commands.DOWNLOAD,
    "CD": commands.CD,
    "LIST": commands.LIST,
    "LS": commands.LIST,
    "QUIT": commands.QUIT,
}


def send_message(client_socket: socket, message: bytes) -> None:
    client_socket.send(message)


def send_current_dir(request: str, client: Client) -> None:
    request: str = request.split()[0].upper()
    if request != "QUIT":
        current_dir = client.get_current_catalog() + " $ "
        send_message(client.get_socket(), current_dir.encode(encoding="UTF-8"))


def execute_command(request: str, client: Client) -> None:
    try:
        command_name: str = request.split()[0].upper()
        command = list_of_commands.get(command_name, None)
        if command != None:
            if not command(request, client):
                logger.debug(
                    f"client: {client.get_ip_address()} - {command_name} was not executed"
                )
            else:
                logger.debug(f"client: {client.get_ip_address()} - {command_name}")
    except Exception as e:
        logger.error(f"Command execution error: {e}")
