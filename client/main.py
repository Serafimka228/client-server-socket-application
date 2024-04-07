import sys
import socket
from client.client import connect_to_server, receive_data, init_socket, start_client


def main() -> None:
    client_socket: socket = init_socket()
    if not connect_to_server(client_socket):
        sys.exit(1)
        print(4)
    start_client(client_socket)


if __name__ == "__main__":
    main()
