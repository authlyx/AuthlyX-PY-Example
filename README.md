# AuthlyX Python SDK

This is a Python authentication SDK for desktop, CLI, and utility apps that want simple integration with the AuthlyX API.

This folder includes the SDK in `AuthlyX.py` and a runnable example in `main.py`.

## Requirements

- Python `3.8` or later
- `requests`

## Quick Start

```py
from AuthlyX import AuthlyX

AuthlyXApp = AuthlyX(
    ownerId="12345678",
    appName="MYAPP",
    version="1.0.0",
    secret="your-secret",
    debug=True,
    api="https://authly.cc/api/v2",
)

AuthlyXApp.Init()
```

## Optional Parameters

```py
AuthlyXApp = AuthlyX(
    ownerId="12345678",
    appName="MYAPP",
    version="1.0.0",
    secret="your-secret",
    debug=False,
    api="https://example.com/api/v2",
)
```

### Available options

- `debug`
  - Default: `True`
  - Set `False` to disable SDK logs

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

## Authentication Example

```py
# Username + password
AuthlyXApp.Login("username", password="password")

# License key only
AuthlyXApp.Login("XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")

# Device login
AuthlyXApp.Login("YOUR_DEVICE_ID", deviceType="motherboard")
```

## Username Login Example

```py
AuthlyXApp.Login("username", password="password")

if AuthlyXApp.response["success"]:
    print("Login success")
    print(AuthlyXApp.userData["Username"])
    print(AuthlyXApp.userData["SubscriptionLevel"])
else:
    print(AuthlyXApp.response["message"])
```

## Variable Example

```py
AuthlyXApp.SetVariable("theme", "dark")

value = AuthlyXApp.GetVariable("theme")
print(value)
```

## Logging

By default, SDK logging is enabled.

Logs are written to:

`C:\ProgramData\AuthlyX\{AppName}\YYYY_MM_DD.log`

Sensitive values such as passwords, secrets, session IDs, request IDs, nonces, license keys, and hashes are masked automatically.

## Example Project

The runnable example in `main.py` uses the public test app by default for `Init()`.

If you want to run the authenticated example too, set:

- `AUTHLYX_USERNAME`
- `AUTHLYX_PASSWORD`

Optional extra test values:

- `AUTHLYX_LICENSE_KEY`
- `AUTHLYX_MOTHERBOARD_ID`
- `AUTHLYX_PROCESSOR_ID`

Then run:

```powershell
pip install requests
python main.py
```
