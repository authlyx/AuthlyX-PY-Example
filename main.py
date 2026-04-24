import os
import sys
from AuthlyX import AuthlyX


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    try:
        input("Press Enter to continue...")
    except Exception:
        return


def show_result(title, auth):
    r = auth.response
    ok = "SUCCESS" if r.get("success") else "FAILED"
    print()
    print(f"{title}: {ok}")
    print(f"Message: {r.get('message')}")
    if r.get("code"):
        print(f"Code: {r.get('code')}")
    if r.get("status_code"):
        print(f"Status: {r.get('status_code')}")


def show_user(auth):
    u = auth.userData
    print()
    print("USER PROFILE")
    print("==============================================")
    print(f"Username: {u.get('Username') or 'N/A'}")
    print(f"Email: {u.get('Email') or 'N/A'}")
    print(f"License Key: {u.get('LicenseKey') or 'N/A'}")
    print(f"Subscription: {u.get('Subscription') or 'N/A'}")
    print(f"Subscription Level: {u.get('SubscriptionLevel') or 'N/A'}")
    print(f"Expiry Date: {u.get('ExpiryDate') or 'N/A'}")
    print(f"Days Left: {u.get('DaysLeft') or 0}")
    print(f"Last Login: {u.get('LastLogin') or 'N/A'}")
    print(f"Registered At: {u.get('RegisteredAt') or 'N/A'}")
    print(f"HWID/SID: {u.get('Hwid') or 'N/A'}")
    print(f"IP Address: {u.get('IpAddress') or 'N/A'}")
    print("==============================================")


def do_init(auth):
    ok = auth.Init()
    show_result("Init", auth)
    return ok


def do_login_user(auth):
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    auth.Login(username, password=password)
    show_result("Login", auth)


def do_login_license(auth):
    license_key = input("License Key: ").strip()
    auth.Login(license_key)
    show_result("License Login", auth)


def do_login_device(auth):
    device_type = input("Device Type (motherboard/processor): ").strip().lower()
    device_id = input("Device ID: ").strip()
    auth.Login(device_id, deviceType=device_type)
    show_result("Device Login", auth)


def do_register(auth):
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    license_key = input("License Key: ").strip()
    email = input("Email (optional): ").strip()
    auth.Register(username, password, license_key, email=email)
    show_result("Register", auth)


def do_extend(auth):
    username = input("Username: ").strip()
    license_key = input("License Key: ").strip()
    auth.ExtendTime(username, license_key)
    show_result("Extend", auth)


def do_get_var(auth):
    k = input("Variable Key: ").strip()
    v = auth.GetVariable(k)
    show_result("Get Variable", auth)
    if auth.response.get("success"):
        print(f"Value: {v}")


def do_set_var(auth):
    k = input("Variable Key: ").strip()
    v = input("Variable Value: ").strip()
    auth.SetVariable(k, v)
    show_result("Set Variable", auth)


def do_get_chats(auth):
    ch = input("Channel Name (empty for app): ").strip() or auth.appName
    auth.GetChats(ch)
    show_result("Get Chats", auth)
    if not auth.response.get("success"):
        return
    msgs = auth.chatMessages.get("Messages") or []
    if not msgs:
        print("No messages.")
        return
    for m in msgs:
        ts = m.get("CreatedAt") or ""
        user = m.get("Username") or ""
        msg = m.get("Message") or ""
        print(f"[{ts}] {user}: {msg}")


def do_send_chat(auth):
    ch = input("Channel Name (empty for app): ").strip() or auth.appName
    msg = input("Message: ").strip()
    auth.SendChat(msg, channelName=ch)
    show_result("Send Chat", auth)


def do_validate(auth):
    auth.ValidateSession()
    show_result("Validate Session", auth)


def test_all(auth):
    username = os.environ.get("AUTHLYX_USERNAME", "").strip()
    password = os.environ.get("AUTHLYX_PASSWORD", "").strip()
    license_key = os.environ.get("AUTHLYX_LICENSE_KEY", "").strip()
    motherboard = os.environ.get("AUTHLYX_MOTHERBOARD_ID", "").strip()
    processor = os.environ.get("AUTHLYX_PROCESSOR_ID", "").strip()
    var_key = os.environ.get("AUTHLYX_VARIABLE_KEY", "theme").strip() or "theme"
    var_value = os.environ.get("AUTHLYX_VARIABLE_VALUE", "dark").strip() or "dark"

    if not username or not password:
        print("Set AUTHLYX_USERNAME and AUTHLYX_PASSWORD to run the authenticated test flow.")
        return

    auth.Login(username, password=password)
    show_result("Login", auth)
    if not auth.response.get("success"):
        return
    show_user(auth)

    auth.SetVariable(var_key, var_value)
    show_result("Set Variable", auth)

    auth.GetVariable(var_key)
    show_result("Get Variable", auth)

    auth.SendChat("python sdk test", channelName=auth.appName)
    show_result("Send Chat", auth)

    auth.GetChats(auth.appName)
    show_result("Get Chats", auth)

    if license_key:
        auth.ExtendTime(username, license_key)
        show_result("Extend", auth)

        auth.Login(license_key)
        show_result("License Login", auth)
        if auth.response.get("success"):
            show_user(auth)

    if motherboard:
        auth.Login(motherboard, deviceType="motherboard")
        show_result("Device Login (motherboard)", auth)
        if auth.response.get("success"):
            show_user(auth)

    if processor:
        auth.Login(processor, deviceType="processor")
        show_result("Device Login (processor)", auth)
        if auth.response.get("success"):
            show_user(auth)

    auth.ValidateSession()
    show_result("Validate Session", auth)


def main():
    api = os.environ.get("AUTHLYX_API") or "https://authly.cc/api/v2"
    auth = AuthlyX(
        ownerId=os.environ.get("AUTHLYX_OWNER_ID") or "b49d11af8c42",
        appName=os.environ.get("AUTHLYX_APP_NAME") or "TEST",
        version=os.environ.get("AUTHLYX_VERSION") or "1.3",
        secret=os.environ.get("AUTHLYX_SECRET") or "1L0edLKqHlFv0AL3NIQ7uPpikN2ECr7aZSHrNWMo",
        api=api,
    )

    if len(sys.argv) > 1 and sys.argv[1].lower() == "--test-all":
        if not do_init(auth):
            show_user(auth)
            return
        test_all(auth)
        show_user(auth)
        return

    clear()
    print("AuthlyX Python Example")
    print(f"API: {api}")
    print(f"App: {auth.appName}")
    print()

    if not do_init(auth):
        pause()
        return

    while True:
        print()
        print("1. Login (username/password)")
        print("2. Login (license key)")
        print("3. Login (device)")
        print("4. Register")
        print("5. Extend")
        print("6. Get Variable")
        print("7. Set Variable")
        print("8. Get Chats")
        print("9. Send Chat")
        print("10. Validate Session")
        print("11. Show User Info")
        print("12. Test All")
        print("0. Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            do_login_user(auth)
        elif choice == "2":
            do_login_license(auth)
        elif choice == "3":
            do_login_device(auth)
        elif choice == "4":
            do_register(auth)
        elif choice == "5":
            do_extend(auth)
        elif choice == "6":
            do_get_var(auth)
        elif choice == "7":
            do_set_var(auth)
        elif choice == "8":
            do_get_chats(auth)
        elif choice == "9":
            do_send_chat(auth)
        elif choice == "10":
            do_validate(auth)
        elif choice == "11":
            show_user(auth)
        elif choice == "12":
            test_all(auth)
        elif choice == "0":
            return
        else:
            print("Invalid choice.")

        pause()
        clear()


if __name__ == "__main__":
    main()
