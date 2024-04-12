import re
import os
import sys
import socket
import selectors
from datetime import datetime
from .logger import logger
from .myselector import selector
from clients.client import disconnect_client, Client
from .dirwalk import list_directories, list_of_accessable_paths


class commands:
    @staticmethod
    def ECHO(request: str, client: Client) -> bool:
        try:
            request: str = re.sub(r"echo ", "", request, 1, flags=re.IGNORECASE)
            send_message(client.get_socket(), f"{request}\n".encode(encoding="UTF-8"))
            return True
        except Exception as e:
            logger.error(f"ECHO Exception: {e}")
            return False

    @staticmethod
    def TIME(_, client: Client) -> bool:
        try:
            current_time: str = datetime.now().strftime("%H:%M:%S")
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
            path = request = re.sub(r"cd ", "", request, 1, flags=re.IGNORECASE)
            path = path.split()
            accessable_paths = list_of_accessable_paths.get(
                client.get_access_rights(), []
            )
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
        except socket.error as e:
            logger.error(f"LIST Exception: {e}")
            return False

    ##  проверяю существует ли файл
    ##  если существует то:
    ##      отправляю {позицию в файле}
    ##      получаю файл, записывая с определенной позиции
    ##  иначе:
    ##      отправляю OK
    ##      получаю файл

    @staticmethod
    def UPLOAD(request: str, client: Client) -> bool:
        try:
            client.get_socket().setblocking(True)
            selector.unregister(client.get_socket())
            request: str = re.sub(r"upload ", "", request, 1, flags=re.IGNORECASE)
            header: str = client.get_socket().recv(1024).decode(encoding="UTF-8")
            match = re.match(r"([^,]+),([^,]+)", header)
            file_size: int = int(match.group(2))
            file_name: str = match.group(1)
            file_path: str = client.get_current_catalog()
            file_name: str = os.path.join(file_path, file_name)
            #
            received_bytes: int = 0
            if os.path.exists(file_name):
                received_bytes = os.path.getsize(file_name)
                f = open(file_name, "ab")
                f.seek(received_bytes)
                send_message(
                    client.get_socket(), f"{received_bytes}".encode(encoding="UTF-8")
                )
            else:
                send_message(client.get_socket(), "OK".encode(encoding="UTF-8"))
                f = open(file_name, "wb")
            #
            while received_bytes < file_size:
                data: bytes = client.get_socket().recv(1024)
                if not data:
                    break
                else:
                    f.write(data)
                received_bytes += 1024

            f.close()
            selector.register(client.get_socket(), selectors.EVENT_READ, client)
            client.get_socket().setblocking(False)
            return True
        except (FileNotFoundError, AttributeError, PermissionError) as e:
            logger.error(f"UPLOAD exception: {e}")
            return False

    ##  получаю запрос
    ##  если запрос содержит в себе смещение:   (1)
    ##      отправляю файл со смещения
    ##  иначе:
    ##      отправляю файл

    @staticmethod
    def DOWNLOAD(request: str, client: Client) -> bool:
        try:
            client.get_socket().setblocking(True)
            request: str = re.sub(r"download ", "", request, 1, flags=re.IGNORECASE)
            if "," in request:  # (1)
                send_bytes = int(request.split(",", 1)[1])
                print(send_bytes)
            else:
                send_bytes = 0
            file_name: str = request.split(",")[0]
            file_name = f"{client.get_current_catalog()}{file_name}"
            file_size: int = os.path.getsize(file_name)
            header: bytes = f"{file_name},{str(file_size)}".encode(encoding="UTF-8")
            with open(file_name, "rb") as f:
                send_message(client.get_socket(), header)
                if send_bytes != file_size:
                    f.seek(send_bytes)
                    while True:
                        data: bytes = f.read(1024)
                        if not data:
                            break
                        send_message(client.get_socket(), data)
                else:
                    print("already downloaded")
            client.get_socket().setblocking(False)
            return True
        except (FileNotFoundError, AttributeError, PermissionError) as e:
            logger.error(f"DOWNLOAD Exception: {e}")
            return False


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
    try:
        client_socket.send(message)
    except (socket.error, socket.timeout) as e:
        logger.error(f"Send message error: {e}")


def send_current_dir(request: str, client: Client) -> None:
    request: str = request.split()[0].upper()
    if request != "QUIT":
        current_dir = client.get_current_catalog() + " $ "
        send_message(client.get_socket(), current_dir.encode(encoding="UTF-8"))


def execute_command(request: str, client: Client) -> None:
    # try:
    command_name: str = request.split()[0].upper()
    command = list_of_commands.get(command_name, None)
    if command != None:
        if not command(request, client):
            logger.debug(
                f"client: {client.get_ip_address()} - {command_name} was not executed"
            )
        else:
            logger.debug(f"client: {client.get_ip_address()} - {command_name}")


# except Exception as e:
#    logger.error(f"Command execution error: {e}")
