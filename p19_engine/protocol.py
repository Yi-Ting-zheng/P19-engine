import hashlib
import json
import os
import secrets
from pathlib import Path

import yaml

PROTOCOL_VERSION = "1.0"
ROOMS = ("F", "N", "S", "A")
TRUTH_VOTES = (
    "THEOREM",
    "THEOREM-COND",
    "EMPIRICAL",
    "HYPOTHESIS",
    "REJECT",
    "CANCELLED",
    "ABSTAIN",
)
GAP_CLASSES = ("none", "mathematical_barrier", "formalization_pending", "methodological")

_DISPATCH_KEYS = (
    "kind",
    "protocol_version",
    "run_id",
    "specimen_id",
    "room",
    "token",
    "artifact_ref",
    "context_refs",
    "issued_at",
    "msg_hash",
)
_REPORT_KEYS = (
    "kind",
    "protocol_version",
    "run_id",
    "specimen_id",
    "room",
    "token",
    "vote",
    "claims",
    "evidence",
    "msg_hash",
)


class ProtocolError(Exception):
    pass


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_obj(obj) -> str:
    return sha256_hex(canonical_json(obj))


def new_token() -> str:
    return secrets.token_hex(16)


def _stamp(msg: dict) -> dict:
    body = {k: v for k, v in msg.items() if k != "msg_hash"}
    out = dict(msg)
    out["msg_hash"] = hash_obj(body)
    return out


def _verify_hash(msg: dict) -> None:
    body = {k: v for k, v in msg.items() if k != "msg_hash"}
    if hash_obj(body) != msg.get("msg_hash"):
        raise ProtocolError("msg_hash mismatch (message tampered or corrupted)")


def _check_room(room) -> None:
    if room not in ROOMS:
        raise ProtocolError(f"unknown room {room!r}, expected one of {ROOMS}")


def make_dispatch(run_id, specimen_id, room, token, artifact_ref, context_refs=None, issued_at=None):
    _check_room(room)
    return _stamp(
        {
            "kind": "dispatch",
            "protocol_version": PROTOCOL_VERSION,
            "run_id": run_id,
            "specimen_id": specimen_id,
            "room": room,
            "token": token,
            "artifact_ref": artifact_ref,
            "context_refs": list(context_refs or []),
            "issued_at": issued_at or "",
        }
    )


def make_report(run_id, specimen_id, room, token, vote, claims, evidence=None, issued_at=None):
    _check_room(room)
    if vote not in TRUTH_VOTES:
        raise ProtocolError(f"invalid vote {vote!r}, expected one of {TRUTH_VOTES}")
    if not isinstance(claims, dict) or not claims:
        raise ProtocolError("claims must be a non-empty dict")
    return _stamp(
        {
            "kind": "report",
            "protocol_version": PROTOCOL_VERSION,
            "run_id": run_id,
            "specimen_id": specimen_id,
            "room": room,
            "token": token,
            "vote": vote,
            "claims": claims,
            "evidence": list(evidence or []),
            "issued_at": issued_at or "",
        }
    )


def _require(msg, keys, kind):
    if not isinstance(msg, dict):
        raise ProtocolError(f"{kind}: message must be a mapping")
    missing = [k for k in keys if k not in msg]
    if missing:
        raise ProtocolError(f"{kind}: missing keys {missing}")
    if msg.get("kind") != kind:
        raise ProtocolError(f"{kind}: kind field is {msg.get('kind')!r}")
    if msg.get("protocol_version") != PROTOCOL_VERSION:
        raise ProtocolError(f"{kind}: unsupported protocol_version {msg.get('protocol_version')!r}")
    _verify_hash(msg)


def validate_dispatch(msg, expect_room=None, expect_run=None, expect_specimen=None, expect_token=None):
    _require(msg, _DISPATCH_KEYS, "dispatch")
    _check_room(msg["room"])
    if expect_room is not None and msg["room"] != expect_room:
        raise ProtocolError(f"dispatch room {msg['room']!r} != expected {expect_room!r}")
    if expect_token is not None and msg["token"] != expect_token:
        raise ProtocolError("dispatch token mismatch (foreign channel rejected)")
    if expect_run is not None and msg["run_id"] != expect_run:
        raise ProtocolError("dispatch run_id mismatch")
    if expect_specimen is not None and msg["specimen_id"] != expect_specimen:
        raise ProtocolError("dispatch specimen_id mismatch")
    if not isinstance(msg["token"], str) or len(msg["token"]) < 16:
        raise ProtocolError("dispatch token missing or too short")
    if not isinstance(msg["artifact_ref"], str) or not msg["artifact_ref"]:
        raise ProtocolError("dispatch artifact_ref must be a non-empty string")
    if not isinstance(msg["context_refs"], list):
        raise ProtocolError("dispatch context_refs must be a list")
    return msg


def validate_report(msg, expect_room=None, expect_run=None, expect_specimen=None, expect_token=None):
    _require(msg, _REPORT_KEYS, "report")
    _check_room(msg["room"])
    if msg["vote"] not in TRUTH_VOTES:
        raise ProtocolError(f"report vote {msg['vote']!r} not in vocabulary")
    if expect_room is not None and msg["room"] != expect_room:
        raise ProtocolError(f"report room {msg['room']!r} != expected {expect_room!r}")
    if expect_run is not None and msg["run_id"] != expect_run:
        raise ProtocolError("report run_id mismatch")
    if expect_specimen is not None and msg["specimen_id"] != expect_specimen:
        raise ProtocolError("report specimen_id mismatch")
    if expect_token is not None and msg["token"] != expect_token:
        raise ProtocolError("report token mismatch (cross-room or forged report rejected)")
    if not isinstance(msg["claims"], dict) or not msg["claims"]:
        raise ProtocolError("report claims must be a non-empty dict")
    if not isinstance(msg["evidence"], list):
        raise ProtocolError("report evidence must be a list")
    return msg


def write_message(path, msg) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    text = yaml.safe_dump(msg, allow_unicode=True, sort_keys=True, default_flow_style=False)
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)


def read_message(path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise ProtocolError(f"message file not found: {p}")
    try:
        msg = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise ProtocolError(f"invalid YAML in {p}: {e}") from e
    if not isinstance(msg, dict):
        raise ProtocolError(f"message file {p} does not contain a mapping")
    return msg


def channel_paths(room_dir):
    d = Path(room_dir)
    return d / "inbox.yaml", d / "outbox.yaml"
