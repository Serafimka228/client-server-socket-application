import json

possible_client_access_rights = ("local", "private", "public")
data = []


def get_client_info() -> tuple:
    print(f"Client access rights: {possible_client_access_rights}")
    client_address: str = input("Enter client address: ")
    client_access_rights: str = input("Enter client acces rights: ")
    return (client_address, client_access_rights)


def main() -> None:
    with open("clients\\access rights.json", "a") as file:
        client_address, client_access_rights = get_client_info()
        client_info = {
            "ip_address": client_address,
            "access_rights": client_access_rights,
        }
        data.append(client_info)
        json.dump(data, file)
        print("Added")


if __name__ == "__main__":
    main()
