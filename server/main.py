import sys
from server.server import init_server, start_server
from server.consts import HOST, PORT


def main() -> None:
    server_socket = init_server(HOST, PORT)
    if not server_socket:
        sys.exit(1)
    start_server(server_socket)


if __name__ == "__main__":
    main()
