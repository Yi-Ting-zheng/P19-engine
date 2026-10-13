from pathlib import Path

import pytest

from p19_engine.audit import AuditError, RuleEngine, eval_string_when, eval_when
from p19_engine.discovery import axiom_verdict, discovery_report, scan_lean

REPO = Path(__file__).resolve().parent.parent
CONTRACT = REPO / "config" / "math_attack_rules.yaml"
P002 = REPO / "specimens" / "positive" / "Specimen-002"
P001 = REPO / "specimens" / "negative" / "Specimen-001"


@pytest.fixture(scope="module")
def engine():
    return RuleEngine.from_path(CONTRACT)


def test_contract_loads_13_rules(engine):
    assert len(engine.rules) == 13
    assert engine.meta["version"] == "v0.6"


def test_specimen_002_hits(engine):
    facts = {
        "build_exit_code": 0,
        "proof_summary_missing": True,
        "summary_incomplete": True,
        "formal_syntax_passed": True,
        "truth_grade_requested": "THEOREM",
        "truth_grade_basis": "formal_syntax_only",
        "external_artifact_scanned": False,
        "new_axioms_not_in_whitelist": False,
        "failure_disclosure_ratio": 1.0,
        "axiom_set_changed": False,
    }
    r = engine.evaluate(facts)
    assert r.rule_ids() == ["MA-006", "MA-006b", "EV-TRUTH-GRADE"]
    assert r.actions() == ["LAUNCH_CASCADE", "FLAG_REWORK", "DOWNGRADE"]
    assert not r.blocked
    assert r.downgrades[0]["downgrade_to"] == "THEOREM-COND"


def test_ev_axiom_blocks(engine):
    r = engine.evaluate({"external_artifact_scanned": True, "new_axioms_not_in_whitelist": True})
    assert r.blocked
    assert r.rule_ids() == ["EV-AXIOM"]


def test_ev_survivor_string_when(engine):
    assert engine.evaluate({"failure_disclosure_ratio": 0.06}).rule_ids() == ["EV-SURVIVOR"]
    assert engine.evaluate({"failure_disclosure_ratio": 0.5}).rule_ids() == []
    assert engine.evaluate({"failure_disclosure_ratio": 1.0}).rule_ids() == []


def test_strict_bool_vs_int_typing(engine):
    assert engine.evaluate({"build_exit_code": False}).rule_ids() == []
    assert engine.evaluate({"build_exit_code": 1}).rule_ids() == []


def test_cascade_requires_parent(engine):
    child_only = {"summary_incomplete": True}
    assert "MA-006b" not in engine.evaluate(child_only).rule_ids()
    with_parent = {"summary_incomplete": True, "cascade_parent_triggered": True}
    r = engine.evaluate(with_parent)
    assert "MA-006b" in r.rule_ids()
    assert "MA-002b" in r.rule_ids()


def test_missing_fact_never_fires(engine):
    assert engine.evaluate({}).rule_ids() == []


def test_string_when_evaluator():
    facts = {"residual_xN": 3e-4, "flag": True}
    assert eval_string_when("residual_xN > 1e-4", facts)
    assert not eval_string_when("residual_xN < 1e-4", facts)
    assert eval_string_when("residual_xN > 1e-4 and flag", facts)
    assert eval_string_when("not (residual_xN < 1e-4)", facts)
    assert not eval_string_when("missing_key > 1", facts)
    with pytest.raises(AuditError):
        eval_string_when("residual_xN >< 1e-4", facts)


def test_when_rejects_unknown_type():
    with pytest.raises(AuditError):
        eval_when(42, {})


def test_forbidden_pattern_matcher(engine):
    hits = engine.find_forbidden_patterns("IF 分片多次独立一致 THEN 升格为 THEOREM")
    assert [h["id"] for h in hits] == ["FP-MATH-03"]
    assert engine.find_forbidden_patterns("totally innocent statement") == []
    assert engine.find_forbidden_patterns("") == []


def test_whitelist_helpers(engine):
    outside, forbidden = engine.outside_whitelist(["propext", "SchanuelAt", "sneaky", "sorryAx"])
    assert "sneaky" in outside and "sorryAx" in outside
    assert "propext" not in outside and "SchanuelAt" not in outside
    assert forbidden == ["sorryAx"]


def test_unknown_action_rejected():
    doc = {
        "rules": [
            {"id": "X-1", "when": {"a": True}, "then": {"action": "NOT_A_VERB"}},
        ]
    }
    with pytest.raises(AuditError, match="not in vocabulary"):
        RuleEngine(doc)


def test_duplicate_id_rejected():
    doc = {
        "rules": [
            {"id": "X-1", "when": {"a": True}, "then": {"action": "DOWNGRADE"}},
            {"id": "X-1", "when": {"b": True}, "then": {"action": "DOWNGRADE"}},
        ]
    }
    with pytest.raises(AuditError, match="duplicate"):
        RuleEngine(doc)


def test_scan_lean_specimen_002():
    scan = scan_lean(P002 / "proof.lean")
    assert scan["exists"]
    assert scan["axioms"] == ["SchanuelAt"]
    assert scan["sorry_count"] == 0
    assert scan["sha256"]


def test_scan_lean_specimen_001_sorry():
    scan = scan_lean(P001 / "proof.lean")
    assert scan["exists"]
    assert scan["sorry_count"] >= 1
    assert scan["axioms"] == []


def test_scan_lean_missing_file(tmp_path):
    scan = scan_lean(tmp_path / "nope.lean")
    assert not scan["exists"]
    assert scan["axioms"] == []


def test_axiom_verdict_conditional(engine):
    scan = scan_lean(P002 / "proof.lean")
    declared = ["propext", "Classical.choice", "Quot.sound", "SchanuelAt"]
    verdict = axiom_verdict(engine, scan, declared)
    assert verdict["verdict"] == "CONDITIONAL"
    assert verdict["hard_wall_axioms"] == ["SchanuelAt"]
    assert verdict["forbidden_axioms"] == []
    assert verdict["undeclared_scan_drift"] == []


def test_axiom_verdict_block_forbidden(engine):
    scan = {"axioms": ["sneaky_axiom", "sorryAx"], "exists": True}
    verdict = axiom_verdict(engine, scan, [])
    assert verdict["verdict"] == "BLOCK"
    assert verdict["forbidden_axioms"] == ["sorryAx"]
    assert "sneaky_axiom" in verdict["outside_whitelist"]


def test_discovery_report_artifact_unavailable(engine):
    rep = discovery_report(engine, None, [])
    assert rep["artifact_unavailable"]
