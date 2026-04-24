import requests
import json
import uuid
import hashlib
import os
import sys
import re
import time
import subprocess
from datetime import datetime, timezone
import ctypes
import webbrowser


class AuthlyXLogger:
    Enabled = True
    AppName = "AuthlyX"

    @staticmethod
    def _mask_sensitive(text):
        if not text:
            return text
        patterns = [
            r'("session_id"\s*:\s*")([^"]+)(")',
            r'("owner_id"\s*:\s*")([^"]+)(")',
            r'("secret"\s*:\s*")([^"]+)(")',
            r'("password"\s*:\s*")([^"]+)(")',
            r'("key"\s*:\s*")([^"]+)(")',
            r'("license_key"\s*:\s*")([^"]+)(")',
            r'("hash"\s*:\s*")([^"]+)(")',
            r'("request_id"\s*:\s*")([^"]+)(")',
            r'("nonce"\s*:\s*")([^"]+)(")',
            r'("hwid"\s*:\s*")([^"]+)(")',
            r'("sid"\s*:\s*")([^"]+)(")',
            r'(\bx-auth-signature\s*:\s*)([A-Za-z0-9+/=]+)',
            r'(\bx-v2-signature\s*:\s*)([A-Za-z0-9+/=]+)',
        ]
        out = str(text)
        for p in patterns:
            out = re.sub(
                p,
                lambda m: (m.group(1) + "***" + (m.group(3) if m.lastindex and m.lastindex >= 3 else "")),
                out,
                flags=re.IGNORECASE,
            )
        return out

    @staticmethod
    def Log(content):
        if not AuthlyXLogger.Enabled:
            return
        if content is None:
            return
        s = str(content)
        if not s.strip():
            return
        try:
            app = (AuthlyXLogger.AppName or "default").strip() or "default"
            program_data = os.environ.get("PROGRAMDATA") or ""
            root = os.path.join(program_data, "AuthlyX", app)
            os.makedirs(root, exist_ok=True)
            log_path = os.path.join(root, f"{datetime.now(timezone.utc):%Y_%m_%d}.log")
            line = f"[{datetime.now(timezone.utc):%H:%M:%S}] {AuthlyXLogger._mask_sensitive(s)}\n"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            return


class Auth:
    DefaultBaseUrl = "https://authly.cc/api/v2"
    IpLookupUrl = "https://api.ipify.org"

    def __init__(self, ownerId, appName, version, secret, debug=True, api=None):
        self.ownerId = ownerId or ""
        self.appName = appName or ""
        self.version = version or ""
        self.secret = secret or ""
        self.baseUrl = self._normalize_base_url(api or Auth.DefaultBaseUrl)
        self.loggingEnabled = True if debug is None else bool(debug)

        AuthlyXLogger.AppName = self.appName or "AuthlyX"
        AuthlyXLogger.Enabled = self.loggingEnabled

        self.sessionId = ""
        self.applicationHash = ""
        self.initialized = False
        self.cachedPublicIp = ""
        self.cachedPublicIpExpiresAt = 0.0

        self.response = {
            "success": False,
            "message": "",
            "raw": "",
            "code": "",
            "status_code": 0,
            "request_id": "",
            "nonce": "",
            "signature_kid": "",
        }

        self.userData = {
            "Username": "",
            "Email": "",
            "LicenseKey": "",
            "Subscription": "",
            "SubscriptionLevel": "",
            "ExpiryDate": "",
            "DaysLeft": 0,
            "LastLogin": "",
            "Hwid": "",
            "IpAddress": "",
            "RegisteredAt": "",
        }

        self.variableData = {"VarKey": "", "VarValue": "", "UpdatedAt": ""}

        self.updateData = {
            "Available": False,
            "LatestVersion": "",
            "DownloadUrl": "",
            "AutoUpdateEnabled": False,
            "ForceUpdate": False,
            "Changelog": "",
            "ShowReminder": False,
            "ReminderMessage": "",
            "AllowedUntil": "",
        }

        self.chatMessages = {
            "ChannelName": "",
            "Messages": [],
            "Count": 0,
            "NextCursor": "",
            "HasMore": False,
        }

        self._calculate_application_hash()
        AuthlyXLogger.Log(f"[SDK] AuthlyX initialized for app '{self.appName}' using '{self.baseUrl}'.")

    def _normalize_base_url(self, api):
        base = (api or "").strip()
        if not base:
            return Auth.DefaultBaseUrl
        return base.rstrip("/")

    def _reset_response(self):
        self.response["success"] = False
        self.response["message"] = ""
        self.response["raw"] = ""
        self.response["code"] = ""
        self.response["status_code"] = 0
        self.response["request_id"] = ""
        self.response["nonce"] = ""
        self.response["signature_kid"] = ""

    def _set_failure(self, code, message, raw="", status_code=0):
        self.response["success"] = False
        self.response["code"] = code or ""
        self.response["message"] = message or ""
        self.response["raw"] = raw or ""
        self.response["status_code"] = int(status_code or 0)
        return False

    def _has_required_credentials(self):
        return bool(self.ownerId and self.appName and self.version and self.secret)

    def _canonical_json(self, obj):
        return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

    def _create_security_context(self):
        request_id = str(uuid.uuid4())
        nonce = os.urandom(16).hex()
        ts = int(time.time() * 1000)
        return request_id, nonce, ts

    def _calculate_application_hash(self):
        try:
            path = sys.executable
            if not path or not os.path.exists(path):
                path = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
            if not path or not os.path.exists(path):
                self.applicationHash = "UNKNOWN_HASH"
                return
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while True:
                    b = f.read(1024 * 1024)
                    if not b:
                        break
                    h.update(b)
            self.applicationHash = h.hexdigest()
        except Exception:
            self.applicationHash = "UNKNOWN_HASH"

    def _get_windows_sid(self):
        try:
            out = subprocess.check_output(
                ["whoami", "/user", "/fo", "csv", "/nh"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            if not out:
                return ""
            cols = [c.strip().strip('"') for c in out.split(",")]
            for c in cols:
                if c.startswith("S-1-"):
                    return c
            if len(cols) >= 2 and cols[1].startswith("S-1-"):
                return cols[1]
            return ""
        except Exception:
            return ""

    def _get_system_identifier(self):
        if sys.platform == "win32":
            sid = self._get_windows_sid()
            if sid:
                return sid
        try:
            seed = (os.environ.get("USERNAME") or "") + "|" + (os.environ.get("COMPUTERNAME") or "") + "|" + (sys.platform or "")
            return hashlib.sha256(seed.encode("utf-8", errors="ignore")).hexdigest()
        except Exception:
            return "UNKNOWN_SID"

    def _get_public_ip(self):
        now = time.time()
        if self.cachedPublicIp and now < self.cachedPublicIpExpiresAt:
            return self.cachedPublicIp
        try:
            r = requests.get(Auth.IpLookupUrl, timeout=10)
            ip = (r.text or "").strip()
            if ip:
                self.cachedPublicIp = ip
                self.cachedPublicIpExpiresAt = now + 600.0
                return ip
        except Exception:
            return self.cachedPublicIp or ""
        return ""

    def _build_url(self, endpoint):
        ep = (endpoint or "").lstrip("/")
        return f"{self.baseUrl}/{ep}"

    def _validate_response_metadata(self, headers, request_id, nonce):
        resp_request_id = headers.get("x-v2-request-id") or ""
        resp_nonce = headers.get("x-v2-nonce") or ""
        sig_kid = headers.get("x-v2-signature-kid") or ""
        if resp_request_id and resp_request_id != request_id:
            return False, "AUTH_REQUEST_MISMATCH", "Response request_id does not match the original request.", sig_kid
        if resp_nonce and resp_nonce != nonce:
            return False, "AUTH_REQUEST_MISMATCH", "Response nonce does not match the original request.", sig_kid
        return True, "", "", sig_kid

    def _compute_days_left(self, expiry):
        try:
            if not expiry:
                return 0
            s = str(expiry).strip()
            if not s:
                return 0
            if s.endswith("Z"):
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            delta = dt - now
            days = int(delta.total_seconds() // 86400)
            return days if days > 0 else 0
        except Exception:
            return 0

    def _load_user_data(self, obj):
        if not isinstance(obj, dict):
            return

        user = obj.get("user") or {}
        lic = obj.get("license") or {}
        dev = obj.get("device") or {}

        if isinstance(user, dict) and user:
            self.userData["Username"] = str(user.get("username") or "")
            self.userData["Email"] = str(user.get("email") or self.userData["Email"] or "")
            self.userData["Subscription"] = str(user.get("subscription") or self.userData["Subscription"] or "")
            lvl = user.get("subscription_level")
            self.userData["SubscriptionLevel"] = "" if lvl is None else str(lvl)
            self.userData["ExpiryDate"] = str(user.get("expiry_date") or self.userData["ExpiryDate"] or "")
            self.userData["LastLogin"] = str(user.get("last_login") or self.userData["LastLogin"] or "")
            self.userData["RegisteredAt"] = str(user.get("created_at") or user.get("registered_at") or self.userData["RegisteredAt"] or "")

        if isinstance(lic, dict) and lic:
            self.userData["LicenseKey"] = str(lic.get("license_key") or self.userData["LicenseKey"] or "")
            if not self.userData["Subscription"]:
                self.userData["Subscription"] = str(lic.get("subscription") or "")
            lvl = lic.get("subscription_level")
            if self.userData["SubscriptionLevel"] == "" and lvl is not None:
                self.userData["SubscriptionLevel"] = str(lvl)
            if not self.userData["ExpiryDate"]:
                self.userData["ExpiryDate"] = str(lic.get("expiry_date") or "")

        if isinstance(dev, dict) and dev:
            if not self.userData["Subscription"]:
                self.userData["Subscription"] = str(dev.get("subscription") or "")
            lvl = dev.get("subscription_level")
            if self.userData["SubscriptionLevel"] == "" and lvl is not None:
                self.userData["SubscriptionLevel"] = str(lvl)
            if not self.userData["ExpiryDate"]:
                self.userData["ExpiryDate"] = str(dev.get("expiry_date") or "")
            if not self.userData["LastLogin"]:
                self.userData["LastLogin"] = str(dev.get("last_login") or "")
            if not self.userData["RegisteredAt"]:
                self.userData["RegisteredAt"] = str(dev.get("registered_at") or "")
            if not self.userData["IpAddress"]:
                self.userData["IpAddress"] = str(dev.get("ip_address") or "")
            if not self.userData["Hwid"]:
                self.userData["Hwid"] = str(dev.get("hwid") or "")

        if not self.userData["Hwid"]:
            self.userData["Hwid"] = self._get_system_identifier()
        if not self.userData["IpAddress"]:
            self.userData["IpAddress"] = self._get_public_ip()

        self.userData["DaysLeft"] = self._compute_days_left(self.userData["ExpiryDate"])

    def _load_variable_data(self, obj):
        if not isinstance(obj, dict):
            return
        var = obj.get("variable") or {}
        if not isinstance(var, dict):
            return
        self.variableData["VarKey"] = str(var.get("var_key") or "")
        self.variableData["VarValue"] = str(var.get("var_value") or "")
        self.variableData["UpdatedAt"] = str(var.get("updated_at") or "")

    def _load_update_data(self, obj):
        if not isinstance(obj, dict):
            return
        upd = obj.get("update")
        if not isinstance(upd, dict):
            if ("auto_update_enabled" in obj) or ("auto_update_download_url" in obj):
                self.updateData["Available"] = True
                self.updateData["LatestVersion"] = str(obj.get("server_version") or obj.get("version") or "")
                self.updateData["AutoUpdateEnabled"] = bool(obj.get("auto_update_enabled"))
                self.updateData["DownloadUrl"] = str(obj.get("auto_update_download_url") or "")
                self.updateData["ForceUpdate"] = bool(obj.get("force_update") or False)
            return
        self.updateData["Available"] = bool(upd.get("available") or False)
        self.updateData["LatestVersion"] = str(upd.get("latest_version") or "")
        self.updateData["AutoUpdateEnabled"] = bool(upd.get("auto_update_enabled"))
        self.updateData["DownloadUrl"] = str(upd.get("download_url") or "")
        self.updateData["ForceUpdate"] = bool(upd.get("force_update") or False)
        self.updateData["Changelog"] = str(upd.get("changelog") or "")
        self.updateData["ShowReminder"] = bool(upd.get("show_reminder") or False)
        self.updateData["ReminderMessage"] = str(upd.get("reminder_message") or "")
        self.updateData["AllowedUntil"] = "" if upd.get("allowed_until") is None else str(upd.get("allowed_until"))

    def _compare_semver(self, a, b):
        def parts(v):
            if not v:
                return [0, 0, 0]
            s = str(v).strip()
            if "-" in s:
                s = s.split("-", 1)[0]
            out = []
            for p in s.split(".")[:3]:
                try:
                    out.append(int(p))
                except Exception:
                    out.append(0)
            while len(out) < 3:
                out.append(0)
            return out

        ap = parts(a)
        bp = parts(b)
        return (ap > bp) - (ap < bp)

    def _should_show_update_prompt(self, force_show=False):
        if not self.updateData.get("Available"):
            return False
        if force_show:
            return True
        if not self._is_client_outdated():
            return False
        if not self._has_whitelisted_update_message():
            return False
        return True

    def _is_client_outdated(self):
        latest = (self.updateData.get("LatestVersion") or "").strip()
        if not latest:
            return False
        return self._compare_semver(self.version, latest) < 0

    def _has_whitelisted_update_message(self):
        return bool(self.updateData.get("ShowReminder")) or bool((self.updateData.get("AllowedUntil") or "").strip())

    def _is_auto_update_enabled(self):
        return bool(self.updateData.get("AutoUpdateEnabled"))

    def _format_display_date(self, raw_date):
        value = (raw_date or "").strip()
        if not value:
            return value
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.strftime("%B %d, %Y").replace(" 0", " ")
        except Exception:
            return value

    def _build_whitelisted_update_message(self):
        allowed_until = (self.updateData.get("AllowedUntil") or "").strip()
        if allowed_until:
            base = f"A new version is ready, and you can keep using this build until {self._format_display_date(allowed_until)}."
        else:
            base = "A new version is ready, and you can still use this build for now."

        if not self._is_auto_update_enabled():
            return base

        return base + "\n\nWould you like to download the latest version now?"

    def _show_required_update_console(self):
        message = (self.response.get("message") or "").strip() or "Please update your app to the latest version."
        print(message)

        latest = (self.updateData.get("LatestVersion") or "").strip()
        if latest:
            print(f"Latest version: {latest}")

        download_url = (self.updateData.get("DownloadUrl") or "").strip()
        if self._is_auto_update_enabled() and download_url:
            print("1. Download Latest")
            print("2. Exit")
            if sys.stdin and sys.stdin.isatty():
                choice = input("Select an option (1 or 2): ").strip()
                if choice == "1":
                    webbrowser.open(download_url)

    def _prompt_update_if_needed(self, force_show=False):
        if not self._should_show_update_prompt(force_show=force_show):
            return

        if force_show:
            self._show_required_update_console()
            return

        download_url = (self.updateData.get("DownloadUrl") or "").strip()
        msg = self._build_whitelisted_update_message()

        # Windows MessageBox (Yes/No or OK), fallback to console prompt
        try:
            if os.name == "nt":
                MB_OK = 0x00000000
                MB_YESNO = 0x00000004
                MB_ICONINFORMATION = 0x00000040
                MB_TOPMOST = 0x00040000
                IDYES = 6

                flags = (MB_YESNO if self._is_auto_update_enabled() and download_url else MB_OK) | MB_ICONINFORMATION | MB_TOPMOST
                r = ctypes.windll.user32.MessageBoxW(0, msg, "AuthlyX Update", flags)
                if self._is_auto_update_enabled() and download_url and r == IDYES:
                    webbrowser.open(download_url)
                return
        except Exception:
            pass

        print(msg)
        if self._is_auto_update_enabled() and download_url and sys.stdin and sys.stdin.isatty():
            choice = input("Download the latest version now? (Y/N): ").strip().lower()
            if choice == "y":
                webbrowser.open(download_url)

    def _load_chat_data(self, obj):
        if not isinstance(obj, dict):
            return
        data = obj.get("data") or {}
        if not isinstance(data, dict):
            return
        self.chatMessages["ChannelName"] = str(data.get("channel_name") or "")
        msgs = data.get("messages") or []
        if not isinstance(msgs, list):
            msgs = []
        mapped = []
        for m in msgs:
            if not isinstance(m, dict):
                continue
            mapped.append(
                {
                    "Id": m.get("id"),
                    "Username": str(m.get("username") or ""),
                    "Message": str(m.get("message") or ""),
                    "CreatedAt": str(m.get("created_at") or ""),
                }
            )
        self.chatMessages["Messages"] = mapped
        self.chatMessages["Count"] = len(mapped)
        self.chatMessages["NextCursor"] = str(data.get("next_cursor") or "")
        self.chatMessages["HasMore"] = bool(data.get("has_more") or False)

    def _post_json(self, endpoint, payload):
        self._reset_response()
        if payload is None or not isinstance(payload, dict):
            return self._set_failure("INVALID_PAYLOAD", "Payload cannot be null.")

        request_id, nonce, ts = self._create_security_context()
        payload["request_id"] = request_id
        payload["nonce"] = nonce
        payload["timestamp"] = ts

        body = self._canonical_json(payload)
        url = self._build_url(endpoint)

        AuthlyXLogger.Log(f"[SDK][REQUEST] POST {url} {body}")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"AuthlyX-Python-Client/{self.version or '0'}",
            "x-request-id": request_id,
            "x-auth-nonce": nonce,
            "x-auth-timestamp": str(ts),
        }

        try:
            r = requests.post(url, data=body.encode("utf-8"), headers=headers, timeout=30)
            raw = r.text or ""
            AuthlyXLogger.Log(f"[SDK][RESPONSE] {r.status_code} {raw}")

            self.response["raw"] = raw
            self.response["status_code"] = int(r.status_code)
            self.response["request_id"] = request_id
            self.response["nonce"] = nonce

            try:
                obj = r.json() if raw else {}
            except Exception:
                self._set_failure("INVALID_JSON", "Invalid JSON response from server.", raw, r.status_code)
                return False

            if not isinstance(obj, dict):
                obj = {}

            lowered = {k.lower(): v for k, v in r.headers.items()}
            ok, code, msg, kid = self._validate_response_metadata(lowered, request_id, nonce)
            self.response["signature_kid"] = kid or ""
            if not ok:
                self._set_failure(code, msg, raw, r.status_code)
                return False

            self.response["success"] = bool(obj.get("success") if "success" in obj else (200 <= r.status_code < 300))
            self.response["code"] = str(obj.get("code") or "")
            self.response["message"] = str(obj.get("message") or r.reason or "")

            if not self.response["success"] and not self.response["code"]:
                self.response["code"] = str(r.status_code)

            if "session_id" in obj and obj.get("session_id"):
                self.sessionId = str(obj.get("session_id"))

            self._load_user_data(obj)
            self._load_variable_data(obj)
            self._load_update_data(obj)
            self._load_chat_data(obj)

            return bool(self.response["success"])
        except requests.exceptions.Timeout as ex:
            return self._set_failure("TIMEOUT", f"Request timed out: {str(ex)}")
        except requests.exceptions.RequestException as ex:
            return self._set_failure("NETWORK_ERROR", f"Network error: {str(ex)}")
        except Exception as ex:
            return self._set_failure("SDK_ERROR", f"Unexpected SDK error: {str(ex)}")

    def _ensure_initialized(self):
        if self.initialized and self.sessionId:
            return True
        self._set_failure("NOT_INITIALIZED", "AuthlyX is not initialized. Call Init() first.")
        return False

    def Init(self):
        if not self._has_required_credentials():
            return self._set_failure("MISSING_CREDENTIALS", "Owner ID, app name, version, and secret are required.")
        payload = {
            "owner_id": self.ownerId,
            "app_name": self.appName,
            "version": self.version,
            "secret": self.secret,
            "hash": self.applicationHash or "",
        }
        ok = self._post_json("init", payload)
        self._prompt_update_if_needed(force_show=(self.response.get("code") == "UPDATE_REQUIRED"))
        if ok and self.sessionId:
            self.initialized = True
        return bool(self.initialized)

    def Login(self, identifier, password=None, deviceType=None):
        if deviceType is not None:
            return self.DeviceLogin(deviceType, identifier)
        if password is None:
            return self.LicenseLogin(identifier)
        return self._user_login(identifier, password)

    def _user_login(self, username, password):
        if not self._ensure_initialized():
            return False
        payload = {
            "session_id": self.sessionId,
            "username": username or "",
            "password": password or "",
            "sid": self._get_system_identifier(),
            "ip": self._get_public_ip(),
        }
        return self._post_json("login", payload)

    def LicenseLogin(self, licenseKey):
        if not self._ensure_initialized():
            return False
        payload = {
            "session_id": self.sessionId,
            "license_key": licenseKey or "",
            "sid": self._get_system_identifier(),
            "ip": self._get_public_ip(),
        }
        return self._post_json("licenses", payload)

    def DeviceLogin(self, deviceType, deviceId):
        if not self._ensure_initialized():
            return False
        payload = {
            "session_id": self.sessionId,
            "device_type": (deviceType or "").strip().lower(),
            "device_id": deviceId or "",
            "ip": self._get_public_ip(),
        }
        return self._post_json("device-auth", payload)

    def Register(self, username, password, licenseKey, email=""):
        if not self._ensure_initialized():
            return False
        payload = {
            "session_id": self.sessionId,
            "username": username or "",
            "password": password or "",
            "key": licenseKey or "",
            "email": email or "",
            "hwid": self._get_system_identifier(),
        }
        return self._post_json("register", payload)

    def ChangePassword(self, oldPassword, newPassword):
        if not self._ensure_initialized():
            return False
        payload = {
            "session_id": self.sessionId,
            "old_password": oldPassword or "",
            "new_password": newPassword or "",
        }
        return self._post_json("change-password", payload)

    def ExtendTime(self, username, licenseKey):
        if not self._ensure_initialized():
            return False
        sid = self._get_system_identifier()
        ip = self._get_public_ip()
        payload = {
            "session_id": self.sessionId,
            "username": username or "",
            "license_key": licenseKey or "",
            "sid": sid,
            "ip": ip,
        }
        return self._post_json("extend", payload)

    def GetVariable(self, key):
        if not self._ensure_initialized():
            return ""
        payload = {"session_id": self.sessionId, "var_key": key or ""}
        ok = self._post_json("variables", payload)
        if ok:
            return self.variableData.get("VarValue") or ""
        return ""

    def SetVariable(self, key, value):
        if not self._ensure_initialized():
            return False
        payload = {"session_id": self.sessionId, "var_key": key or "", "var_value": value or ""}
        return self._post_json("variables/set", payload)

    def Log(self, message):
        if not self._ensure_initialized():
            return False
        payload = {"session_id": self.sessionId, "message": message or ""}
        return self._post_json("logs", payload)

    def GetChats(self, channelName, limit=100, cursor=None):
        if not self._ensure_initialized():
            return False
        payload = {"session_id": self.sessionId, "channel_name": channelName or "", "limit": int(limit or 100)}
        if cursor:
            payload["cursor"] = cursor
        return self._post_json("chats/get", payload)

    def SendChat(self, message, channelName=None):
        if not self._ensure_initialized():
            return False
        payload = {"session_id": self.sessionId, "message": message or ""}
        if channelName:
            payload["channel_name"] = channelName
        return self._post_json("chats/send", payload)

    def ValidateSession(self):
        if not self.initialized or not self.sessionId:
            return self._set_failure("INVALID_SESSION", "No active session. Please login first.")
        payload = {"session_id": self.sessionId}
        return self._post_json("validate-session", payload)

    def IsInitialized(self):
        return bool(self.initialized)

    def GetSessionId(self):
        return self.sessionId or ""

    def GetCurrentApplicationHash(self):
        return self.applicationHash or ""

    init = Init
    login = Login
    register = Register
    extend_time = ExtendTime
    extendTime = ExtendTime
    get_variable = GetVariable
    getVariable = GetVariable
    set_variable = SetVariable
    setVariable = SetVariable
    get_chats = GetChats
    getChats = GetChats
    send_chat = SendChat
    sendChat = SendChat
    validate_session = ValidateSession
    validateSession = ValidateSession
    change_password = ChangePassword
    changePassword = ChangePassword
    isInitialized = IsInitialized
    getSessionId = GetSessionId
    log = Log
    getCurrentApplicationHash = GetCurrentApplicationHash


AuthlyX = Auth
