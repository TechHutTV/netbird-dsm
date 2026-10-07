"""Bounded status data and diagnostics jobs, always run as the package user."""

import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
import uuid


SUPPORT_URL = "https://upload.debug.netbird.io/upload-url"
DEBUG_SECONDS = 600
MAX_BUNDLE = 50 * 1024 * 1024
LEVELS = {"PANIC", "FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"}


def directory(api):
    run = api.var / "run"
    path = run / "ui-diagnostics"
    for candidate in (run, path):
        if candidate == path:
            candidate.mkdir(mode=0o700, exist_ok=True)
        info = candidate.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise api.Error(503, "Cannot access the private diagnostics directory. Restart NetBird in Package Center.")
    return path


def private_file(path, flags=os.O_RDONLY, *, require_private=True):
    fd = os.open(str(path), flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_nlink != 1 or (require_private and info.st_mode & 0o077)):
            raise OSError("unsafe diagnostics file")
        return os.fdopen(fd, "rb"), info
    except Exception:
        os.close(fd)
        raise


def read_state(api, name):
    try:
        file, _ = private_file(directory(api) / (name + ".json"))
        with file:
            value = json.loads(file.read(16385))
        if not isinstance(value, dict):
            raise ValueError("invalid diagnostics state")
        return value
    except FileNotFoundError:
        return {}


def save_state(api, name, value):
    path = directory(api)
    with tempfile.NamedTemporaryFile(dir=str(path), delete=False) as out:
        out.write(json.dumps(value).encode())
        stage = out.name
    os.replace(stage, str(path / (name + ".json")))


def spawn(api, kind, job):
    # No request environment, cookies, setup keys or shell command is inherited.
    subprocess.Popen([api.python, "-I", "-B", str(api.script), "--worker", kind, job],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True,
                     env={"PATH": "/usr/bin:/bin"})


def daemon_identity(api):
    info = (api.var / "run/netbird-http.sock").lstat()
    return [info.st_dev, info.st_ino, info.st_ctime_ns]


def log_level(api):
    value = api.rpc("GetLogLevel", timeout=5).get("level")
    if value not in LEVELS:
        raise api.Error(502, "The daemon returned an unknown log level.")
    return value


def finish_debug(api, current):
    # A restarted daemon has its startup log level. Never change that instance,
    # or overwrite a log level that someone has since changed through the CLI.
    if daemon_identity(api) == current.get("daemon") and log_level(api) == "DEBUG":
        api.rpc("SetLogLevel", {"level": current["previous"]})
    current["state"] = "restored"
    save_state(api, "debug", current)


def action(data, api):
    action_name = data["action"]
    if action_name == "debug-start":
        current = read_state(api, "debug")
        if current.get("state") == "active":
            raise api.Error(409, "Temporary debug logging is already active.")
        current = {"id": uuid.uuid4().hex, "state": "active", "previous": log_level(api),
                   "daemon": daemon_identity(api), "expires": time.time() + DEBUG_SECONDS}
        save_state(api, "debug", current)
        try:
            api.rpc("SetLogLevel", {"level": "DEBUG"})
            spawn(api, "debug", current["id"])
        except Exception:
            finish_debug(api, current)
            raise
        return {"ok": True, "message": "Debug logging enabled for ten minutes. The previous log level will be restored automatically."}
    if action_name == "debug-stop":
        current = read_state(api, "debug")
        if current.get("state") == "active":
            finish_debug(api, current)
        return {"ok": True, "message": "Temporary debug logging stopped."}
    if action_name == "bundle-create":
        current = read_state(api, "bundle")
        if current.get("state") == "running" and time.time() - current.get("started", 0) < 300:
            raise api.Error(409, "A debug bundle is already being created.")
        current = {"id": uuid.uuid4().hex, "state": "running", "started": time.time(),
                   "upload": data["destination"] == "support"}
        save_state(api, "bundle", current)
        try:
            spawn(api, "bundle", current["id"])
        except Exception:
            current.update(state="error", message="The debug bundle job could not start.")
            save_state(api, "bundle", current)
            raise
        return {"ok": True, "message": "Creating the debug bundle. You can keep this page open to follow its progress."}
    if action_name == "bundle-download":
        current = read_state(api, "bundle")
        if current.get("id") != data["id"] or not current.get("download"):
            raise api.Error(409, "This bundle is no longer available. Create a new bundle.")
        file, info = private_file(directory(api) / "bundle.zip")
        if not 0 < info.st_size <= MAX_BUNDLE:
            file.close()
            raise api.Error(413, "The debug bundle exceeds the download size limit.")
        return {"_download": file, "size": info.st_size}
    raise api.Error(400, "That diagnostics action is not supported.")


def keep_bundle(api, raw_path):
    # Only accept NetBird's completed ZIP from its standard temporary directory.
    # The browser never supplies a path and cannot download arbitrary files.
    if not isinstance(raw_path, str) or not re.fullmatch(r"/tmp/netbird\.debug\.[0-9]+\.zip", raw_path):
        raise ValueError("unexpected bundle path")
    file, info = private_file(Path(raw_path))
    with file:
        if not 0 < info.st_size <= MAX_BUNDLE or file.read(4) != b"PK\x03\x04":
            raise ValueError("invalid bundle")
        file.seek(0)
        with tempfile.NamedTemporaryFile(dir=str(directory(api)), delete=False) as out:
            stage = Path(out.name)
            try:
                remaining = info.st_size
                while remaining:
                    chunk = file.read(min(65536, remaining))
                    if not chunk:
                        raise ValueError("incomplete bundle")
                    out.write(chunk)
                    remaining -= len(chunk)
            except Exception:
                stage.unlink()
                raise
        os.replace(str(stage), str(directory(api) / "bundle.zip"))
    current = os.lstat(raw_path)
    if (current.st_dev, current.st_ino) == (info.st_dev, info.st_ino):
        os.unlink(raw_path)


def worker(kind, job, api):
    if kind not in {"debug", "bundle"} or not re.fullmatch(r"[a-f0-9]{32}", job):
        return
    file, _ = private_file(directory(api) / (kind + ".lock"), os.O_RDWR | os.O_CREAT)
    with file:
        # A recently stopped debug worker may need one polling interval to
        # release its lock. Wait briefly so an immediate restart gets a timer.
        for attempt in range(6):
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if kind != "debug" or attempt == 5:
                    return
                time.sleep(1)
        if kind == "debug":
            while True:
                current = read_state(api, "debug")
                if current.get("id") != job or current.get("state") != "active":
                    return
                try:
                    expired = time.time() >= current["expires"]
                    changed = daemon_identity(api) != current.get("daemon")
                    if expired or changed:
                        with api.lock():
                            current = read_state(api, "debug")
                            if current.get("id") == job and current.get("state") == "active":
                                finish_debug(api, current)
                        return
                except (OSError, api.Error):
                    # Package restart / a short competing action: retry without
                    # extending the deadline or touching a replacement daemon.
                    pass
                time.sleep(2)
        current = read_state(api, "bundle")
        if current.get("id") != job or current.get("state") != "running":
            return
        try:
            request = {"anonymize": True, "anonymizeLevel": "strict", "systemInfo": True,
                       "logFileCount": 1}
            if current["upload"]:
                request["uploadURL"] = SUPPORT_URL
            result = api.rpc("DebugBundle", request, timeout=240)
            keep_bundle(api, result.get("path"))
            current.update(state="complete", download=True)
            key = result.get("uploadedKey", "")
            if current["upload"] and not result.get("uploadFailureReason") and isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}/[A-Za-z0-9_-]{1,128}", key):
                current["supportCode"] = key
                current["message"] = "Bundle uploaded. Send this support code with your report."
            elif current["upload"]:
                current["message"] = "The upload could not be confirmed. Download the bundle and attach it to your support request."
            else:
                current["message"] = "Bundle ready to download. Nothing was uploaded."
        except Exception:
            current.update(state="error", message="The debug bundle could not be created. Check the daemon and try again.")
        # Do not replace the state for a later job.
        if read_state(api, "bundle").get("id") == job:
            save_state(api, "bundle", current)


def text(value, limit=256):
    return value[:limit] if isinstance(value, str) else ""


def records(value):
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def counters(value):
    return str(value) if re.fullmatch(r"[0-9]{1,20}", str(value)) else ""


def recent_logs(api):
    try:
        # Existing daemon logs may be group/world readable. Keep the owner,
        # regular-file and link checks without requiring diagnostics-file modes.
        file, info = private_file(api.var / "netbird.log", require_private=False)
        with file:
            file.seek(max(0, info.st_size - 131072))
            value = file.read(131072).decode("utf-8", errors="replace")
        lines = value.splitlines()
        if info.st_size > 131072:
            lines = lines[1:]
        return [line[:2048] for line in lines[-200:]]
    except OSError:
        return []


def details(api):
    debug = read_state(api, "debug")
    bundle = read_state(api, "bundle")
    if bundle.get("state") == "running" and time.time() - bundle.get("started", 0) < 300:
        # NetBird holds its status mutex while collecting host diagnostics.
        # Poll our job record until collection finishes instead of queuing RPCs.
        return {"ok": True, "collecting": True, "bundle": {"id": bundle["id"], "state": "running"}}
    if bundle.get("state") == "running":
        bundle = {"state": "error", "message": "The bundle job timed out. You can try again."}
    public_bundle = {key: bundle[key] for key in ("id", "state", "message", "supportCode", "download") if key in bundle}
    try:
        result = api.rpc("Status", {"getFullPeerStatus": True}, timeout=5)
    except api.Error:
        # Saved downloads and job failures remain visible when the daemon is
        # unavailable; never strand the UI in an old 'creating' state.
        return {"ok": True, "unavailable": True, "bundle": public_bundle}
    full = result.get("fullStatus")
    full = full if isinstance(full, dict) else {}
    peers = records(full.get("peers"))
    health = {}
    for name in ("management", "signal"):
        source = full.get(name + "State")
        source = source if isinstance(source, dict) else {}
        health[name] = {"reported": bool(source), "connected": source.get("connected") is True}
    health["relays"] = [{"available": item.get("available") is True,
                          "transport": text(item.get("transport"), 32)} for item in records(full.get("relays"))[:100]]
    try:
        level = log_level(api)
    except api.Error:
        level = "Unknown"
    return {"ok": True, "state": text(result.get("status")), "health": health,
            "peers": [{"name": text(item.get("fqdn")), "ip": text(item.get("IP"), 64),
                       "state": text(item.get("connStatus"), 32),
                       "connection": ("Relayed" if item.get("relayed") is True else "Direct") if item.get("connStatus") == "Connected" else "",
                       "latency": text(item.get("latency"), 32),
                       "handshake": text(item.get("lastWireguardHandshake"), 64),
                       "received": counters(item.get("bytesRx")), "sent": counters(item.get("bytesTx"))}
                      for item in peers[:500]], "peerTotal": len(peers),
            "logs": recent_logs(api), "logLevel": level,
            "debug": {"active": debug.get("state") == "active", "expires": debug.get("expires", 0)},
            "bundle": public_bundle}
