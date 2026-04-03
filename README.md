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

## Quick Start

```py
from AuthlyX import AuthlyX

AuthlyXApp = AuthlyX(
    ownerId="12345678",
    appName="MYAPP",
    version="1.0.0",
    secret="qIBFoBJWQH4jaOZr6Sf8BJZyEVnT0LiN4QfGxJGn"
)

AuthlyXApp.Init()
```

## Optional Parameters

```py
from AuthlyX import AuthlyX

AuthlyXApp = AuthlyX(
    ownerId="12345678",
    appName="MYAPP",
    version="1.0.0",
    secret="qIBFoBJWQH4jaOZr6Sf8BJZyEVnT0LiN4QfGxJGn",
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

## Authentication Example

```py
# Username + password
AuthlyXApp.Login("username", password="password")

# License key only
AuthlyXApp.Login("XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")

# Device login
AuthlyXApp.Login("YOUR_MOTHERBOARD_ID", deviceType="motherboard")
```

The SDK routes `Login(...)` automatically:

- `password + identifier` for username login
- `identifier only` for license login
- `deviceType + identifier` for device login

## User Data

After a successful login, the SDK populates `AuthlyXApp.userData`, for example:

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

## Run The Example

Use your local API during development:

```powershell
$env:AUTHLYX_API="http://localhost:4000/api/v2"
python .\main.py
```

Or run the built-in smoke test:

```powershell
$env:AUTHLYX_API="http://localhost:4000/api/v2"
python .\main.py --test-all
```

