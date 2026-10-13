import shutil

import yaml

from p19_engine import isolation
from p19_engine.ledger import TruthLedger
from p19_engine.orchestrator import apply_audit_verdict, arbitrate, run_specimen
from p19_engine.run_p0 import ORDER, REPO_ROOT, SPECIMEN_MAP, check_expect

CONTRACT = REPO_ROOT / "config" / "math_attack_rules.yaml"


def _load_spec(rel):
    path = REPO_ROOT / rel / "specimen.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["specimen"]


def _run(specimen_dir, run_dir, ledger_path):
    return run_specimen(
        specimen_dir=specimen_dir,
        workdir=run_dir,
        contract_path=CONTRACT,
        ledger_path=ledger_path,
        timeout=30.0,
    )


def test_closed_loop_three_specimens(tmp_path):
    ledger_path = tmp_path / "truth_ledger.jsonl"
    results = {}
    for sid in ORDER:
        rel = SPECIMEN_MAP[sid]
        spec = _load_spec(rel)
        run_dir = tmp_path / spec["id"]
        run_dir.mkdir()
        results[sid] = (spec, _run(REPO_ROOT / rel, run_dir, ledger_path))

    s1, r1 = results["001"]
    assert r1["verdict"] == "REJECT"
    assert r1["state"]["state"] == "DONE"
    assert set(r1["votes"].values()) == {"REJECT"}
    assert check_expect(s1, r1) == []

    s2, r2 = results["002"]
    assert r2["verdict"] == "THEOREM-COND"
    assert r2["state"]["state"] == "DONE"
    assert set(r2["votes"].values()) == {"THEOREM-COND"}
    hits = [h["rule_id"] for h in r2["audit"]["hits"]]
    assert hits == ["MA-006", "MA-006b", "EV-TRUTH-GRADE"]
    assert r2["ledger_payload"]["hard_wall"] == "GAP-001"
    assert r2["ledger_payload"]["gaps"] == ["GAP-001"]
    assert check_expect(s2, r2) == []

    s3, r3 = results["003"]
    assert r3["verdict"] == "CANCELLED"
    assert r3["state"]["state"] == "DONE"
    assert set(r3["votes"].values()) == {"CANCELLED"}
    assert check_expect(s3, r3) == []

    for res in (r1, r2, r3):
        for room in ("F", "N", "S", "A"):
            assert res["reports"][room]["msg_hash"]
            assert res["reports"][room]["evidence_count"] >= 1
        run_root = tmp_path / res["specimen_id"]
        room_dirs = [d for d in (run_root / "rooms").iterdir() if d.is_dir()]
        assert len(room_dirs) == 4
        for d in room_dirs:
            assert (d / "inbox.yaml").is_file()
            assert (d / "outbox.yaml").is_file()
            assert (d / "worker.log").is_file()
        assert (run_root / "isolation.json").is_file()
        iso = res["isolation"]
        assert iso["runtime"]["mode"] in ("acl_deny_list", "fallback")
        for room in ("F", "N", "S", "A"):
            assert iso["workers"][room]["egress"] in ("OPEN", "BLOCKED")
        if isolation.is_windows():
            assert iso["runtime"]["mode"] == "acl_deny_list"
            for room in ("F", "N", "S", "A"):
                assert iso["workers"][room]["sibling_enumeration"] == "BLOCKED"

    led = TruthLedger(ledger_path)
    ok, detail = led.verify()
    assert ok, detail
    entries = led.entries()
    assert [e["seq"] for e in entries] == [1, 2, 3]
    assert [e["payload"]["truth_status"] for e in entries] == ["REJECT", "THEOREM-COND", "CANCELLED"]


def test_audit_block_freezes_without_ledger(tmp_path):
    src = REPO_ROOT / SPECIMEN_MAP["002"]
    mutant_dir = tmp_path / "mutant"
    mutant_dir.mkdir()
    shutil.copy(src / "specimen.yaml", mutant_dir / "specimen.yaml")
    shutil.copy(src / "proof.lean", mutant_dir / "proof.lean")
    doc = yaml.safe_load((mutant_dir / "specimen.yaml").read_text(encoding="utf-8"))
    doc["specimen"]["audit_facts"]["external_artifact_scanned"] = True
    doc["specimen"]["audit_facts"]["new_axioms_not_in_whitelist"] = True
    (mutant_dir / "specimen.yaml").write_text(
        yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    ledger_path = tmp_path / "ledger.jsonl"
    res = _run(mutant_dir, tmp_path / "run", ledger_path)
    assert res["state"]["state"] == "FREEZED"
    assert "EV-AXIOM" in res["state"]["freeze_reason"]
    assert res["verdict"] is None
    assert res["ledger_seq"] is None
    assert not ledger_path.exists()


def test_missing_worker_report_freezes(tmp_path):
    from p19_engine import protocol as P

    ledger_path = tmp_path / "ledger.jsonl"
    src_dir = REPO_ROOT / SPECIMEN_MAP["001"]
    spec = _load_spec(SPECIMEN_MAP["001"])
    run_dir = tmp_path / "run"

    def forge(rt):
        forged = P.make_report(
            "preseeded", spec["id"], "F", P.new_token(), "REJECT", {"truth_status": "REJECT"}
        )
        P.write_message(rt.outboxes["F"], forged)

    res = run_specimen(
        src_dir,
        run_dir,
        CONTRACT,
        ledger_path,
        timeout=30.0,
        pre_spawn_hook=forge,
    )
    assert res["state"]["state"] == "FREEZED"
    assert "F" in res["state"]["freeze_reason"]
    assert res["verdict"] is None
    assert not ledger_path.exists()


def test_arbitrate_unanimous():
    votes = {"F": "X", "N": "X", "S": "X", "A": "X"}
    assert arbitrate(votes) == "X"


def test_arbitrate_three_to_one():
    votes = {"F": "REJECT", "N": "THEOREM-COND", "S": "THEOREM-COND", "A": "THEOREM-COND"}
    assert arbitrate(votes) == "THEOREM-COND"


def test_arbitrate_no_quorum():
    votes = {"F": "A1", "N": "A1", "S": "A2", "A": "A2"}
    assert arbitrate(votes) is None


def test_arbitrate_empty():
    assert arbitrate({}) is None


def test_apply_audit_verdict_downgrades_theorem(tmp_path):
    from p19_engine.audit import RuleEngine

    engine = RuleEngine.from_path(CONTRACT)
    facts = {
        "build_exit_code": 0,
        "proof_summary_missing": True,
        "summary_incomplete": True,
        "formal_syntax_passed": True,
        "truth_grade_requested": "THEOREM",
        "truth_grade_basis": "formal_syntax_only",
    }
    audit = engine.evaluate(facts)
    assert apply_audit_verdict("THEOREM", audit) == "THEOREM-COND"
    assert apply_audit_verdict("EMPIRICAL", audit) == "EMPIRICAL"
    assert apply_audit_verdict("THEOREM", None) == "THEOREM"
