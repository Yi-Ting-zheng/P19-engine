import pytest

from p19_engine.ledger import GENESIS, LedgerError, TruthLedger
from p19_engine.state_machine import RunState, StateError


def test_full_legal_path():
    st = RunState("r1")
    for target in ("DISPATCHED", "COLLECTED", "CONFLICT_CHECK", "ARBITRATION", "LEDGER_WRITE", "DONE"):
        st.transition(target, f"to {target}")
    assert st.current == "DONE"
    assert st.terminal
    assert [h["state"] for h in st.history][0] == "QUEUED"
    assert st.as_dict()["state"] == "DONE"


def test_illegal_transition_raises():
    st = RunState("r2")
    with pytest.raises(StateError, match="illegal transition QUEUED -> DONE"):
        st.transition("DONE")


def test_skip_state_rejected():
    st = RunState("r3")
    st.transition("DISPATCHED")
    with pytest.raises(StateError):
        st.transition("ARBITRATION")


def test_freeze_reason_and_terminal():
    st = RunState("r4")
    st.transition("DISPATCHED")
    st.transition("FREEZED", "missing reports")
    assert st.freeze_reason == "missing reports"
    assert st.terminal
    with pytest.raises(StateError, match="FREEZED"):
        st.transition("COLLECTED")


def test_ledger_append_and_verify(tmp_path):
    path = tmp_path / "ledger.jsonl"
    led = TruthLedger(path)
    ok, _ = led.verify()
    assert ok
    e1 = led.append(_payload("Specimen-001", "REJECT"))
    assert e1["seq"] == 1 and e1["prev_hash"] == GENESIS
    e2 = led.append(_payload("Specimen-002", "THEOREM-COND"))
    assert e2["seq"] == 2 and e2["prev_hash"] == e1["entry_hash"]
    ok, detail = led.verify()
    assert ok, detail


def test_ledger_tamper_detected(tmp_path):
    path = tmp_path / "ledger.jsonl"
    led = TruthLedger(path)
    led.append(_payload("Specimen-001", "REJECT"))
    led.append(_payload("Specimen-002", "THEOREM-COND"))
    lines = path.read_text(encoding="utf-8").splitlines()
    import json

    obj = json.loads(lines[0])
    obj["payload"]["truth_status"] = "THEOREM"
    lines[0] = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, detail = led.verify()
    assert not ok
    assert "mismatch" in detail or "chain broken" in detail


def test_ledger_missing_key_rejected(tmp_path):
    led = TruthLedger(tmp_path / "l.jsonl")
    with pytest.raises(LedgerError, match="missing keys"):
        led.append({"specimen_id": "x"})


def _payload(sid, status):
    return {
        "specimen_id": sid,
        "truth_status": status,
        "vote_breakdown": {"F": status, "N": status, "S": status, "A": status},
        "claims": {"gap_class": "none", "basis": "test"},
        "rule_hits": [],
        "hard_wall": None,
        "gaps": [],
        "evidence_hashes": [],
        "contract": "test@v0",
    }
