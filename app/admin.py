from database import load_users, save_users, hash_pass

def admin_panel(current_user):
    while True:
        print("\n=== ADMIN PANEL ===")
        print("1. Add Admin/User")
        print("2. Remove User")
        print("3. List Users")
        print("4. Exit Panel")
        choice = input("Admin> ").strip()

        if choice == "1":
            u = input("New username: ").strip().lower()
            p = input("New password: ").strip()
            r = input("Role [admin/user]: ").strip().lower()
            if r not in ["admin", "user"]: r = "user"
            users = load_users()
            if u in users:
                print("User exists.")
            else:
                users[u] = {"password": hash_pass(p), "role": r}
                save_users(users)
                print(f"Added {u} as {r}")

        elif choice == "2":
            u = input("Username to remove: ").strip().lower()
            if u == current_user: print("You can't remove yourself."); continue
            users = load_users()
            if u in users: del users[u]; save_users(users); print(f"Removed {u}")
            else: print("User not found.")

        elif choice == "3":
            users = load_users()
            for u, data in users.items(): print(f"- {u} : {data['role']}")

        elif choice == "4":
            break
        else:
            print("Invalid choice.")
