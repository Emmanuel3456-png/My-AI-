import json

def login():
    with open("Users.json", "r") as file:
        users = json.load(file)

    print("===== QUANTUM MIND AI =====")
    print("General assistant for everyone")
    print()

    username = input("Username (or guest): ")
    password = input("Password: ")

    if username.strip().lower() in ("guest", ""):
        print("\nContinuing as guest.\n")
        return "guest", "user"

    if username in users:
        if users[username]["password"] == password:
            print("\nAccess Granted!\n")
            return username, users[username]["role"]

    print("\nAccess Denied. Try again, create an account in the app, or type guest.")
    return None, None
