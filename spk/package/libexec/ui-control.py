"""Admin-only connection controls. No service launching or arbitrary CLI flags."""

import fcntl
import contextlib
import importlib.util
import ipaddress
import http.client
import json
import os
from pathlib import Path
import pwd
import re
import select
import stat
import subprocess
import sys
import socket
import struct
import time
from types import SimpleNamespace
from urllib.parse import urlsplit


AUTHENTICATE = "/usr/syno/synoman/webman/modules/authenticate.cgi"
IDENTITY = "/usr/bin/id"
PKGVAR = Path("/var/packages/netbird/var")
JSON_SOCKET = "run/netbird-http.sock"
MAX_BODY = 4096
LOGIN_STATES = {"NeedsLogin", "LoginFailed", "SessionExpired"}
STATES = LOGIN_STATES | {"Connected", "Connecting", "Idle"}


class ControlError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


def authenticate(env):
    try:
        result = subprocess.run(
            [AUTHENTICATE], input=b"", stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, env=env, timeout=5, check=True,
        )
        username = result.stdout.decode("utf-8").strip()
        if not username or len(username) > 256 or any(ord(c) < 32 for c in username):
            raise ValueError("invalid identity")
    except (OSError, ValueError, subprocess.SubprocessError):
        raise ControlError(401, "Sign in to DSM again with an administrator account.")
    try:
        result = subprocess.run(
            [IDENTITY, "-nG", "--", username], stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=5, check=True,
        )
        allowed = "administrators" in result.stdout.decode("utf-8").split()
    except (OSError, ValueError, subprocess.SubprocessError):
        allowed = False
    if not allowed:
        raise ControlError(403, "DSM administrator access is required.")


def https_origin(value):
    """Return an HTTPS origin; disallow credentials, paths and ambiguous hosts."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError("invalid URL")
    if any(ord(c) <= 32 or ord(c) >= 127 for c in value) or "\\" in value:
        raise ValueError("invalid URL")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment
            or parsed.path not in ("", "/")):
        raise ValueError("invalid URL")
    host = parsed.hostname
    if ":" in host:
        ipaddress.IPv6Address(host)
    elif not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", host):
        raise ValueError("invalid host")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError("invalid port")
    return "https://" + parsed.netloc


def check_request(env):
    if env.get("REQUEST_METHOD") != "POST":
        raise ControlError(405, "Use POST for connection controls.")
    if env.get("HTTPS", "").lower() not in ("on", "1"):
        raise ControlError(403, "Open DSM over HTTPS to use connection controls.")
    # Origin + a non-simple custom header protect writes even when DSM's global
    # CSRF option is disabled. No CORS access is granted by this endpoint.
    try:
        expected = https_origin("https://" + env.get("HTTP_HOST", ""))
    except ValueError:
        expected = None
    if (expected is None or env.get("HTTP_ORIGIN") != expected
            or env.get("HTTP_X_NETBIRD_ACTION") != "1"
            or env.get("HTTP_SEC_FETCH_SITE", "same-origin") != "same-origin"
            or not env.get("HTTP_X_SYNO_TOKEN") or env.get("QUERY_STRING", "")):
        raise ControlError(403, "Request verification failed. Reopen NetBird from DSM.")
    if env.get("CONTENT_TYPE", "").lower() != "application/json":
        raise ControlError(415, "Connection controls require a JSON request.")
    length = env.get("CONTENT_LENGTH", "")
    if not re.fullmatch(r"[0-9]{1,5}", length) or not 0 < int(length) <= MAX_BODY:
        raise ControlError(413, "The connection request is too large or has no valid length.")
    return int(length)


def read_body(stream, length):
    deadline = time.monotonic() + 5
    chunks = []
    remaining = length
    while remaining:
        ready, _, _ = select.select([stream], [], [], max(0, deadline - time.monotonic()))
        if not ready:
            raise ControlError(408, "The connection request was incomplete. Please retry.")
        chunk = os.read(stream.fileno(), remaining)
        if not chunk:
            raise ControlError(400, "The connection request was incomplete.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def unique_fields(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate field")
        result[name] = value
    return result


def parse_request(body):
    try:
        data = json.loads(body.decode("utf-8"), object_pairs_hook=unique_fields)
    except (ValueError, RecursionError):
        raise ControlError(400, "The connection request is invalid.")
    if not isinstance(data, dict) or not all(isinstance(v, str) for v in data.values()):
        raise ControlError(400, "The connection request is invalid.")
    action = data.get("action")
    if action in ("connect", "disconnect") and set(data) == {"action"}:
        return data
    if action in ("debug-start", "debug-stop") and set(data) == {"action"}:
        return data
    if (action == "bundle-create" and set(data) == {"action", "destination"}
            and data["destination"] in {"local", "support"}):
        return data
    if (action == "bundle-download" and set(data) == {"action", "id"}
            and re.fullmatch(r"[a-f0-9]{32}", data["id"])):
        return data
    if action != "enroll" or set(data) != {"action", "setupKey", "managementUrl"}:
        raise ControlError(400, "That connection action is not supported.")
    # NetBird 0.80.0 registers with UUID setup keys. Reject pasted API tokens
    # and other credentials before contacting the daemon or management server.
    if not re.fullmatch(r"[A-Fa-f0-9]{8}(?:-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12}", data["setupKey"]):
        raise ControlError(400, "Enter a NetBird setup key in UUID format, not a management API token.")
    try:
        data["managementUrl"] = https_origin(data["managementUrl"])
    except ValueError:
        raise ControlError(400, "Enter an HTTPS management URL without a path, credentials or query.")
    return data


def become_package_user():
    try:
        account = pwd.getpwnam("netbird")
        if account.pw_uid == 0:
            raise OSError("invalid package account")
        if os.geteuid() == 0:
            os.setgroups([])
            os.setgid(account.pw_gid)
            os.setuid(account.pw_uid)
        if (os.getuid() != account.pw_uid or os.geteuid() != account.pw_uid
                or os.getgid() != account.pw_gid or os.getegid() != account.pw_gid):
            raise OSError("wrong execution identity")
        os.umask(0o077)
    except (KeyError, OSError):
        raise ControlError(503, "DSM could not run this action as the NetBird package user. Use the CLI.")


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path, timeout):
        super().__init__("localhost", timeout=timeout)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(self.path))
        # Check the actual server, not just the socket file's owner.
        _, uid, _ = struct.unpack("3i", self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        if uid != os.geteuid():
            raise ControlError(503, "The daemon is not running as the package user. Follow the ownership recovery steps first.")


def daemon_request(method, payload=None, timeout=25):
    if method not in {"Status", "Login", "Up", "Down", "GetLogLevel", "SetLogLevel", "DebugBundle"}:
        raise ControlError(400, "That daemon action is not supported.")
    path = PKGVAR / JSON_SOCKET
    try:
        directory = path.parent.lstat()
        endpoint = path.lstat()
        if (not stat.S_ISDIR(directory.st_mode) or directory.st_mode & 0o077
                or directory.st_uid != os.geteuid() or not stat.S_ISSOCK(endpoint.st_mode)
                or endpoint.st_uid != os.geteuid()):
            raise OSError("unsafe socket")
    except OSError:
        raise ControlError(503, "The private control socket is unavailable. Restart NetBird in Package Center. If it was started as root, follow the ownership recovery steps first.")
    connection = UnixHTTPConnection(path, timeout)
    try:
        connection.request("POST", "/daemon.DaemonService/" + method,
                           body=json.dumps(payload or {}).encode("utf-8"),
                           headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        limit = 4 * 1024 * 1024 if method == "Status" and (payload or {}).get("getFullPeerStatus") is True else 65536
        body = response.read(limit + 1)
        if len(body) > limit:
            raise ControlError(502, "The daemon returned an invalid response.")
        if response.status != 200:
            message = ("Enrollment failed. Check the setup key, management URL and server availability."
                       if method == "Login" else
                       "The daemon could not complete the action. Check its status before retrying.")
            raise ControlError(400, message)
        result = json.loads(body)
        if not isinstance(result, dict):
            raise ValueError("invalid response")
        return result
    except (socket.timeout, TimeoutError):
        raise ControlError(504, "The request timed out. Check the connection status before retrying.")
    except (OSError, http.client.HTTPException, ValueError):
        raise ControlError(503, "Unable to reach the daemon. Check NetBird in Package Center.")
    finally:
        connection.close()


def daemon_state():
    state = daemon_request("Status", timeout=5).get("status")
    if not isinstance(state, str) or state not in STATES:
        raise ControlError(503, "Unable to read the daemon status. Check NetBird in Package Center.")
    return state


@contextlib.contextmanager
def action_lock():
    try:
        fd = os.open(str(PKGVAR / ".ui-action.lock"), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    except OSError:
        raise ControlError(503, "Cannot access package state. Check package-user permissions.")
    with os.fdopen(fd, "rb") as lock:
        info = os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_nlink != 1:
            raise ControlError(503, "Cannot safely lock package state. Check package-user permissions.")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ControlError(409, "Another connection action is running. Wait for it to finish.")
        yield


def diagnostics():
    spec = importlib.util.spec_from_file_location("netbird_ui_diagnostics", Path(__file__).with_name("ui-diagnostics.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def diagnostics_api():
    return SimpleNamespace(var=PKGVAR, Error=ControlError, rpc=daemon_request, lock=action_lock,
                           script=Path(__file__), python=sys.executable)


def perform(data):
    # All socket requests and lock-file writes happen as the package user.
    become_package_user()
    with action_lock():
        action = data["action"]
        if action in {"debug-start", "debug-stop", "bundle-create", "bundle-download"}:
            return diagnostics().action(data, diagnostics_api())
        state = daemon_state()
        if action == "enroll" and state not in LOGIN_STATES:
            raise ControlError(409, "This device is already enrolled. Its saved enrollment has been kept.")
        if action == "connect" and state in LOGIN_STATES:
            raise ControlError(409, "Enroll this device with a setup key first.")
        if action == "connect" and state in {"Connected", "Connecting"}:
            return {"ok": True, "message": "NetBird is already connected or connecting."}
        if action == "disconnect" and state in LOGIN_STATES | {"Idle"}:
            return {"ok": True, "message": "NetBird is already disconnected."}

        if action == "enroll":
            # Send only the supported enrollment fields. Do not proxy arbitrary
            # RPCs or settings, write config files, or persist the setup key.
            login = daemon_request("Login", {"setupKey": data["setupKey"],
                                             "managementUrl": data["managementUrl"]})
            if login.get("needsSSOLogin"):
                raise ControlError(400, "Enrollment requires a valid setup key. Create one in your NetBird dashboard.")
        daemon_request("Down" if action == "disconnect" else "Up",
                       {} if action == "disconnect" else {"async": True})
        state = daemon_state()
        if action == "disconnect":
            if state != "Idle":
                raise ControlError(409, "NetBird has not disconnected yet. Check its status before retrying.")
            message = "Disconnected. Your enrollment is saved."
        elif state == "Connected":
            message = "Connected to NetBird."
        elif state in {"Connecting", "Idle"}:
            message = "Connection requested. Watch the status above for the result."
        else:
            raise ControlError(409, "NetBird did not connect. Check its status before retrying.")
        return {"ok": True, "message": message}


def main():
    status = 200
    try:
        env = dict(os.environ)
        authenticate(env)
        if sys.argv[1:] == ["--details"]:
            if env.get("REQUEST_METHOD") != "GET":
                raise ControlError(405, "Use GET to read diagnostics.")
            become_package_user()
            result = diagnostics().details(diagnostics_api())
        else:
            length = check_request(env)
            data = parse_request(read_body(sys.stdin.buffer, length))
            result = perform(data)
    except ControlError as error:
        status = error.status
        result = {"ok": False, "message": error.message}
    except Exception:
        # Never send raw exception text or subprocess output to the browser/log.
        status = 500
        result = {"ok": False, "message": "The connection action could not finish. Check the current status before retrying."}
    phrases = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden",
               405: "Method Not Allowed", 408: "Request Timeout", 409: "Conflict",
               413: "Content Too Large", 415: "Unsupported Media Type",
               500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable", 504: "Gateway Timeout"}
    if "_download" in result:
        with result["_download"] as source:
            headers = ("Status: 200 OK\r\nContent-Type: application/zip\r\n"
                       "Content-Disposition: attachment; filename=netbird-debug.zip\r\n"
                       "Content-Length: {}\r\nCache-Control: no-store\r\n"
                       "Referrer-Policy: no-referrer\r\nX-Content-Type-Options: nosniff\r\n\r\n").format(result["size"])
            sys.stdout.buffer.write(headers.encode())
            remaining = result["size"]
            while remaining:
                chunk = source.read(min(65536, remaining))
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                remaining -= len(chunk)
        return
    print("Status: {} {}\r".format(status, phrases[status]))
    print("Content-Type: application/json\r")
    print("Cache-Control: no-store\r")
    print("Referrer-Policy: no-referrer\r")
    print("X-Content-Type-Options: nosniff\r")
    if status == 405:
        print("Allow: {}\r".format("GET" if sys.argv[1:] == ["--details"] else "POST"))
    print("\r")
    print(json.dumps(result))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        become_package_user()
        diagnostics().worker(sys.argv[2], sys.argv[3], diagnostics_api())
    else:
        main()
