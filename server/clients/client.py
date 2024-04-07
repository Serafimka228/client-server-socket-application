import json
import os
import socket
from collections import deque
from server.logger import logger
from server.consts import possible_client_access_rights


list_of_connected_clients = deque()


class Client:

    def __init__(self, client_socket: socket, client_address: tuple):
        self.__socket = client_socket
        self.__address = client_address
        self.__init_access_rights()
        self.__set_starting_catalog()

    def __init_access_rights(self) -> None:
        with open("clients\\access rights.json", "r") as file:
            data = json.load(file)
        for client in data:
            address, port = self.__address
            if isinstance(client, dict) and client.get("ip_address") == address:
                self.__access_rights = client.get("access_rights")
                break
            else:
                self.__access_rights = "public"

    def __set_starting_catalog(self) -> None:
        self.__current_catalog = possible_client_access_rights.get(self.__access_rights)

    def get_current_catalog(self) -> str:
        return self.__current_catalog

    def change_current_catalog(self, path: str) -> None:
        self.__current_catalog = path

    def get_socket(self) -> socket:
        return self.__socket

    def get_address(self) -> tuple:
        return self.__address

    def get_ip_address(self) -> str:
        ip_address, port = self.__address
        return ip_address

    def get_access_rights(self) -> str:
        return self.__access_rights

    __socket: socket
    __current_catalog: str
    __address: tuple
    __port_number: str
    __access_rights: str  # "local", "private", "public"


def connect_client(client_socket: socket, client_address: tuple) -> Client:
    try:
        client = Client(client_socket, client_address)
        list_of_connected_clients.append(client)
        return client
    except Exception as e:
        logger.error(f"Connect client error || Exception: {e}")
        if client in list_of_connected_clients:
            list_of_connected_clients.remove(client)
        return None


def disconnect_client(client: Client) -> bool:
    try:
        if client in list_of_connected_clients:
            list_of_connected_clients.remove(client)
        from server.server import selector

        selector.unregister(client.get_socket())
        return True
    except Exception as e:
        logger.error(f"Disconnect client error || Exception: {e}")
        return False
