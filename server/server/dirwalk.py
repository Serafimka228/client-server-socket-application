import os
from .consts import possible_client_access_rights


def list_directories(path: str) -> list[str]:
    directories: list = []
    for entry in os.scandir(path):
        if entry.is_dir():
            new_path = os.path.join(path, entry.name)
            directories.append(new_path)
            subdirectories = list_directories(new_path)
            directories.extend(subdirectories)
    return directories


list_of_accessable_paths: dict = {}  # {str: list}


# get list of
def update_list_of_accessable_paths() -> None:
    global list_of_accessable_paths
    local_paths = list_directories(possible_client_access_rights.get("local", ""))
    private_paths = list_directories(possible_client_access_rights.get("private", ""))
    public_paths = list_directories(possible_client_access_rights.get("public", ""))
    list_of_accessable_paths = {
        "local": local_paths,
        "private": private_paths,
        "public": public_paths,
    }
    print(list_of_accessable_paths)


def main():
    dirls = list_directories("root\\")
    print(dirls)


if __name__ == "__main__":
    main()
