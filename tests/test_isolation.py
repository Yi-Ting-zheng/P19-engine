import subprocess
import sys
from pathlib import Path

from p19_engine import protocol as P

REPO = Path(__file__).resolve().parent.parent


def _run_worker(inbox, outbox, room, token, timeout=30):
    cmd = [
        sys.executable,
        "-m",
        "p19_engine.room_worker",
        "--inbox",
        str(inbox),
        "--outbox",
        str(outbox),
        "--room",
        room,
        "--token",
        token,
        "--contract",
        str(REPO / "config" / "math_attack_rules.yaml"),
    ]
    return subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=timeout)


def test_worker_rejects_foreign_room_dispatch(tmp_path):
    token = P.new_token()
    inbox = tmp_path / "inbox.yaml"
    outbox = tmp_path / "outbox.yaml"
    dispatch = P.make_dispatch(
        "run-x", "Specimen-001", "N", token,
        str(REPO / "specimens" / "negative" / "Specimen-001" / "specimen.yaml"),
    )
    P.write_message(inbox, dispatch)
    proc = _run_worker(inbox, outbox, room="F", token=token)
    assert proc.returncode == 2
    assert not outbox.exists()
    assert "room" in (proc.stderr + proc.stdout).lower()


def test_worker_rejects_foreign_token(tmp_path):
    token = P.new_token()
    inbox = tmp_path / "inbox.yaml"
    outbox = tmp_path / "outbox.yaml"
    dispatch = P.make_dispatch(
        "run-x", "Specimen-001", "F", token,
        str(REPO / "specimens" / "negative" / "Specimen-001" / "specimen.yaml"),
    )
    P.write_message(inbox, dispatch)
    proc = _run_worker(inbox, outbox, room="F", token=P.new_token())
    assert proc.returncode == 2
    assert not outbox.exists()
    assert "token" in (proc.stderr + proc.stdout).lower()


def test_worker_happy_path_writes_own_outbox_only(tmp_path):
    token = P.new_token()
    inbox = tmp_path / "inbox.yaml"
    outbox = tmp_path / "outbox.yaml"
    dispatch = P.make_dispatch(
        "run-x", "Specimen-001", "F", token,
        str(REPO / "specimens" / "negative" / "Specimen-001" / "specimen.yaml"),
    )
    P.write_message(inbox, dispatch)
    proc = _run_worker(inbox, outbox, room="F", token=token)
    assert proc.returncode == 0, proc.stderr
    assert outbox.exists()
    report = P.read_message(outbox)
    P.validate_report(report, expect_room="F", expect_run="run-x", expect_token=token)
    assert report["vote"] == "REJECT"
    other = tmp_path / "outbox_G.yaml"
    assert not other.exists()


def test_channel_paths_are_room_local(tmp_path):
    paths = [P.channel_paths(tmp_path / f"room_{r}") for r in ("F", "N", "S", "A")]
    inboxes = {str(p[0]) for p in paths}
    outboxes = {str(p[1]) for p in paths}
    assert len(inboxes) == 4 and len(outboxes) == 4
    assert inboxes.isdisjoint(outboxes)
