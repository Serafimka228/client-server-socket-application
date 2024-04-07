import sys
import socket
from client.client import connect_to_server, receive_data


def main() -> None:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if not connect_to_server(client_socket):
        sys.exit(1)
    print(receive_data(client_socket))


if __name__ == "__main__":
    main()
