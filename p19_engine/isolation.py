import argparse
import json
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path

EGRESS_PROBE_TARGET = ("1.1.1.1", 443)
EGRESS_PROBE_TIMEOUT = 0.3


class IsolationError(Exception):
    pass


def is_windows() -> bool:
    return os.name == "nt"


def current_user() -> str:
    user = os.environ.get("USERNAME")
    if not user:
        import getpass

        user = getpass.getuser()
    domain = os.environ.get("USERDOMAIN")
    return f"{domain}\\{user}" if domain else user


def apply(rooms_root) -> dict:
    """Apply directory-level sibling-enumeration hardening on the rooms root.

    Windows: icacls deny-(R) (non-inheritable) on the rooms root blocks
    listdir() for everyone including the controller, while absolute-path
    read/write of known child files keeps working (SeChangeNotifyPrivilege
    traversal bypass). Self-verifies; raises IsolationError if listdir still
    succeeds. Other platforms: honest fallback record (Linux enforcement is
    Phase B containers).
    """
    root = Path(rooms_root)
    root.mkdir(parents=True, exist_ok=True)
    if not is_windows():
        return {
            "mode": "fallback",
            "platform": platform.system(),
            "list_block": "UNSUPPORTED",
            "user": current_user(),
            "detail": "ACL hardening is Windows-only; Linux enforcement is Phase B containers",
        }
    user = current_user()
    proc = subprocess.run(
        ["icacls", str(root), "/deny", f"{user}:(RD)"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        os.listdir(root)
    except PermissionError:
        verified = True
    except OSError:
        verified = True
    else:
        verified = False
    if not verified:
        raise IsolationError(
            f"ACL deny-list self-check failed for {root}: listdir still permitted "
            f"(icacls rc={proc.returncode})"
        )
    return {
        "mode": "acl_deny_list",
        "platform": platform.system(),
        "list_block": "BLOCKED",
        "user": user,
        "icacls_rc": proc.returncode,
    }


def release(rooms_root) -> dict:
    """Remove the deny-list ACE (idempotent). Must run before any rmtree of the tree."""
    root = Path(rooms_root)
    if not root.is_dir():
        return {"released": False, "reason": "missing"}
    if not is_windows():
        return {"released": False, "reason": "not_windows"}
    user = current_user()
    proc = subprocess.run(
        ["icacls", str(root), "/remove:d", user],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        os.listdir(root)
        listable = True
    except OSError:
        listable = False
    return {"released": listable, "icacls_rc": proc.returncode, "user": user}


def sibling_enumeration(inbox_path) -> str:
    """Probe whether the rooms root (parent of the room dir) can be listed."""
    rooms_root = Path(inbox_path).parent.parent
    try:
        os.listdir(rooms_root)
    except PermissionError:
        return "BLOCKED"
    except OSError:
        return "BLOCKED"
    return "OPEN"


def egress_probe(timeout=EGRESS_PROBE_TIMEOUT) -> str:
    """Detect any outbound TCP path. OPEN = egress available (Phase A marker,
    Phase B containers must turn this into BLOCKED via --network=none)."""
    try:
        conn = socket.create_connection(EGRESS_PROBE_TARGET, timeout=timeout)
    except OSError:
        return "BLOCKED"
    conn.close()
    return "OPEN"


def selfcheck(inbox_path) -> dict:
    return {
        "sibling_enumeration": sibling_enumeration(inbox_path),
        "egress": egress_probe(),
        "platform": platform.system(),
        "enforcement": "acl_deny_list" if is_windows() else "process_level_only",
    }


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="p19_isolation")
    ap.add_argument("--apply", metavar="ROOMS_ROOT")
    ap.add_argument("--release", metavar="ROOMS_ROOT")
    ap.add_argument("--selfcheck", metavar="INBOX_PATH")
    args = ap.parse_args(argv)
    if args.apply:
        print(json.dumps(apply(args.apply), ensure_ascii=False, indent=2))
    elif args.release:
        print(json.dumps(release(args.release), ensure_ascii=False, indent=2))
    elif args.selfcheck:
        print(json.dumps(selfcheck(args.selfcheck), ensure_ascii=False, indent=2))
    else:
        ap.error("one of --apply/--release/--selfcheck required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
