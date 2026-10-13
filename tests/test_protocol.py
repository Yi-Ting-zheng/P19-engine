import tempfile
from pathlib import Path

import pytest

from p19_engine import protocol as P


def test_dispatch_roundtrip(tmp_path):
    tok = P.new_token()
    d = P.make_dispatch("run-1", "Specimen-001", "F", tok, "specimens/x/specimen.yaml")
    P.validate_dispatch(d, expect_room="F", expect_run="run-1", expect_token=tok)
    inbox, _ = P.channel_paths(tmp_path / "room_F")
    P.write_message(inbox, d)
    back = P.read_message(inbox)
    P.validate_dispatch(back, expect_room="F", expect_token=tok)
    assert back == d


def test_report_roundtrip(tmp_path):
    tok = P.new_token()
    r = P.make_report(
        "run-1", "Specimen-001", "N", tok, "REJECT",
        {"truth_status": "REJECT", "gap_class": "none"},
        evidence=[{"kind": "numeric_probe", "verdict": "FAIL"}],
    )
    P.validate_report(r, expect_room="N", expect_token=tok, expect_run="run-1")
    outbox, _ = P.channel_paths(tmp_path / "room_N")
    P.write_message(outbox, r)
    back = P.read_message(outbox)
    P.validate_report(back, expect_room="N", expect_token=tok)


def test_tampered_hash_rejected():
    tok = P.new_token()
    r = P.make_report("run-1", "S-1", "F", tok, "REJECT", {"truth_status": "REJECT"})
    bad = dict(r)
    bad["vote"] = "THEOREM"
    with pytest.raises(P.ProtocolError, match="msg_hash"):
        P.validate_report(bad, expect_room="F", expect_token=tok)


def test_cross_room_token_forgery_rejected():
    tok = P.new_token()
    r = P.make_report("run-1", "S-1", "F", tok, "REJECT", {"truth_status": "REJECT"})
    with pytest.raises(P.ProtocolError, match="token mismatch"):
        P.validate_report(r, expect_room="F", expect_token=P.new_token())


def test_unknown_room_rejected():
    with pytest.raises(P.ProtocolError, match="unknown room"):
        P.make_dispatch("run-1", "S-1", "Z", "t" * 16, "ref")


def test_invalid_vote_rejected():
    with pytest.raises(P.ProtocolError, match="invalid vote"):
        P.make_report("run-1", "S-1", "F", "t" * 16, "PROVEN", {"truth_status": "PROVEN"})


def test_missing_keys_rejected():
    tok = P.new_token()
    r = P.make_report("run-1", "S-1", "F", tok, "REJECT", {"truth_status": "REJECT"})
    del r["claims"]
    with pytest.raises(P.ProtocolError, match="missing keys"):
        P.validate_report(r, expect_room="F", expect_token=tok)


def test_dispatch_room_mismatch_rejected():
    tok = P.new_token()
    d = P.make_dispatch("run-1", "S-1", "F", tok, "ref")
    with pytest.raises(P.ProtocolError, match="room"):
        P.validate_dispatch(d, expect_room="N")


def test_read_missing_file(tmp_path):
    with pytest.raises(P.ProtocolError, match="not found"):
        P.read_message(tmp_path / "nope.yaml")


def test_token_uniqueness():
    tokens = {P.new_token() for _ in range(50)}
    assert len(tokens) == 50
