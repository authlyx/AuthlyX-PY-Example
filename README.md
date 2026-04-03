# AuthlyX Python SDK

This is a Python authentication SDK for desktop and Python applications that want simple integration with the AuthlyX API.

This folder is primarily for SDK users. The script here is only a reference example to help you integrate faster.

## Requirements

- Python 3
- `requests`

Install dependencies:

```powershell
pip install requests
```

## Install

Copy `AuthlyX.py` into your project and import it:

```py
from AuthlyX import AuthlyX
```

## Quick Start

```py
from AuthlyX import AuthlyX

AuthlyXApp = AuthlyX(
    ownerId="12345678",
    appName="MYAPP",
    version="1.0.0",
    secret="your-secret"
)

AuthlyXApp.Init()

if not AuthlyXApp.response["success"]:
    print(AuthlyXApp.response["message"])
    raise SystemExit
```

## Optional Parameters

```py
from AuthlyX import AuthlyX

AuthlyXApp = AuthlyX(
    ownerId="12345678",
    appName="MYAPP",
    version="1.0.0",
    secret="your-secret",
    debug=False,
    api="https://example.com/api/v2"
)
```

### Available options

- `debug`
  - Default: `true`
  - Set `false` to disable SDK logs

- `api`
  - Default: `https://authly.cc/api/v2`
  - Use this for your custom domain

## Available Methods

- `Init()`
- `Login(identifier, password=None, deviceType=None)`
- `Register(username, password, licenseKey, email="")`
- `ChangePassword(oldPassword, newPassword)`
- `ExtendTime(username, licenseKey)`
- `GetVariable(key)`
- `SetVariable(key, value)`
- `Log(message)`
- `GetChats(channelName, limit=100, cursor=None)`
- `SendChat(message, channelName=None)`
- `ValidateSession()`

## Init

```py
AuthlyXApp.Init()

if AuthlyXApp.response["success"]:
    print("Init success")
else:
    print(AuthlyXApp.response["message"])
```

## Login (Unified)

`Login(...)` is a single entry point that supports:

- username/password login
- license login
- device login

```py
AuthlyXApp.Login("username", password="password")

if AuthlyXApp.response["success"]:
    print("Login success")
    print(AuthlyXApp.userData["Username"])
    print(AuthlyXApp.userData["SubscriptionLevel"])
else:
    print(AuthlyXApp.response["message"])
```

### License Login

```py
AuthlyXApp.Login("XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")

if AuthlyXApp.response["success"]:
    print("License login success")
else:
    print(AuthlyXApp.response["message"])
```

### Device Login (Motherboard)

```py
AuthlyXApp.Login("YOUR_MOTHERBOARD_ID", deviceType="motherboard")

if AuthlyXApp.response["success"]:
    print("Device login success")
    print(AuthlyXApp.userData["SubscriptionLevel"])
else:
    print(AuthlyXApp.response["message"])
```

### Device Login (Processor)

```py
AuthlyXApp.Login("YOUR_PROCESSOR_ID", deviceType="processor")

if AuthlyXApp.response["success"]:
    print("Device login success")
else:
    print(AuthlyXApp.response["message"])
```

## Register

```py
AuthlyXApp.Register("new_user", "password", "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX", email="user@example.com")

if AuthlyXApp.response["success"]:
    print("Registered successfully")
else:
    print(AuthlyXApp.response["message"])
```

## Extend Time

```py
AuthlyXApp.ExtendTime("username", "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")

if AuthlyXApp.response["success"]:
    print("Extended successfully")
    print("New expiry:", AuthlyXApp.userData["ExpiryDate"])
else:
    print(AuthlyXApp.response["message"])
```

## Change Password

```py
AuthlyXApp.ChangePassword("old_password", "new_password")

if AuthlyXApp.response["success"]:
    print("Password changed successfully")
else:
    print(AuthlyXApp.response["message"])
```

## Variables

```py
AuthlyXApp.SetVariable("theme", "dark")
print(AuthlyXApp.response["message"])

value = AuthlyXApp.GetVariable("theme")
if AuthlyXApp.response["success"]:
    print("theme =", value)
else:
    print(AuthlyXApp.response["message"])
```

## Chats

```py
AuthlyXApp.SendChat("Hello world", channelName="MAIN")
print(AuthlyXApp.response["message"])

AuthlyXApp.GetChats("MAIN")
if AuthlyXApp.response["success"]:
    for msg in AuthlyXApp.chatMessages["Messages"]:
        print(f"[{msg['CreatedAt']}] {msg['Username']}: {msg['Message']}")
else:
    print(AuthlyXApp.response["message"])
```

## Validate Session

```py
AuthlyXApp.ValidateSession()

if AuthlyXApp.response["success"]:
    print("Session is valid")
else:
    print(AuthlyXApp.response["message"])
```

## User Data

After a successful login, the SDK populates `AuthlyXApp.userData`:

- `Username`
- `Email`
- `LicenseKey`
- `Subscription`
- `SubscriptionLevel`
- `ExpiryDate`
- `DaysLeft`
- `LastLogin`
- `Hwid` (this is the Windows SID where available)
- `IpAddress`
- `RegisteredAt`

