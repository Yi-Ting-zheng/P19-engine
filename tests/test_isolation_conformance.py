import os
from pathlib import Path

import pytest

from p19_engine import isolation, protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECIMEN = REPO_ROOT / "specimens" / "negative" / "Specimen-001" / "specimen.yaml"
CONTRACT = REPO_ROOT / "config" / "math_attack_rules.yaml"

win_only = pytest.mark.skipif(
    not isolation.is_windows(), reason="ACL deny-list hardening is Windows-only"
)


def _runtime(tmp_path):
    from p19_engine.rooms import RoomRuntime

    return RoomRuntime(tmp_path / "run", "iso-test-run", SPECIMEN, CONTRACT)


@win_only
def test_apply_blocks_sibling_listing_and_release_restores(tmp_path):
    rt = _runtime(tmp_path)
    try:
        rt.prepare()
        assert rt.isolation["mode"] == "acl_deny_list"
        assert rt.isolation["list_block"] == "BLOCKED"
        with pytest.raises(PermissionError):
            os.listdir(rt.rooms_root)
        for room in protocol.ROOMS:
            assert rt.inboxes[room].is_file()
    finally:
        rt.release()
    assert len(os.listdir(rt.rooms_root)) == 4


def test_room_ids_random_and_unique(tmp_path):
    rt = _runtime(tmp_path)
    try:
        rt.prepare()
        ids = [rt.room_ids[r] for r in protocol.ROOMS]
        assert len(set(ids)) == 4
        for rid in ids:
            assert len(rid) == 32
            int(rid, 16)
        for room in protocol.ROOMS:
            leaf = rt.room_dir(room).name
            assert leaf == rt.room_ids[room]
            assert not leaf.startswith("room")
            assert rt.room_dir(room).parent == rt.rooms_root
    finally:
        rt.release()


def test_worker_argv_has_no_sibling_paths(tmp_path):
    rt = _runtime(tmp_path)
    try:
        rt.prepare()
        cmd = rt._worker_cmd("F")
        joined = " ".join(cmd)
        for other in ("N", "S", "A"):
            assert str(rt.room_dir(other)) not in joined
            assert rt.tokens[other] not in joined
        assert str(rt.room_dir("F")) in joined
        assert rt.tokens["F"] in cmd
        assert cmd[cmd.index("--room") + 1] == "F"
        assert str(CONTRACT) in joined
    finally:
        rt.release()


@win_only
def test_selfcheck_reports_sibling_blocked(tmp_path):
    rt = _runtime(tmp_path)
    try:
        rt.prepare()
        sc = isolation.selfcheck(rt.inboxes["F"])
        assert sc["sibling_enumeration"] == "BLOCKED"
        assert sc["egress"] in ("OPEN", "BLOCKED")
        assert sc["enforcement"] == "acl_deny_list"
    finally:
        rt.release()


def test_fallback_non_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(isolation, "is_windows", lambda: False)
    root = tmp_path / "rooms"
    status = isolation.apply(root)
    assert status["mode"] == "fallback"
    assert status["list_block"] == "UNSUPPORTED"
    assert os.listdir(root) == []
    assert isolation.selfcheck(root / "x" / "inbox.yaml")["enforcement"] == "process_level_only"


def test_release_idempotent(tmp_path):
    rt = _runtime(tmp_path)
    rt.prepare()
    first = rt.release()
    assert first["released"] is True
    second = isolation.release(rt.rooms_root)
    assert second["released"] is True


def test_forged_outbox_recorded_invalid(tmp_path):
    from p19_engine import protocol as P

    rt = _runtime(tmp_path)
    try:
        rt.prepare()
        forged = P.make_report(
            "preseeded",
            "Specimen-001",
            "F",
            P.new_token(),
            "REJECT",
            {"truth_status": "REJECT"},
        )
        P.write_message(rt.outboxes["F"], forged)
        reports, missing = rt.collect(timeout=0.3)
        assert reports == {}
        assert missing["F"].startswith("invalid report")
        for room in ("N", "S", "A"):
            assert missing[room].startswith("timeout")
    finally:
        rt.release()


def test_egress_probe_returns_marker():
    assert isolation.egress_probe() in ("OPEN", "BLOCKED")
