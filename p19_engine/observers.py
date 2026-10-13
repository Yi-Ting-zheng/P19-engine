import math
from pathlib import Path

from .discovery import discovery_report

ROOMS = ("F", "N", "S", "A")


def _wall_claims(spec, vote):
    gap_class = "none"
    hard_wall = None
    if vote == "THEOREM-COND":
        gap_class = "mathematical_barrier"
        hard_wall = spec.get("claims", {}).get("hard_wall")
        if not hard_wall:
            hard_wall = "UNDECLARED-GAP"
    return {
        "truth_status": vote,
        "gap_class": gap_class,
        "hard_wall": hard_wall,
    }


def _wall_vote(spec, engine, discovery):
    ax = discovery.get("axiom_audit", {})
    if ax.get("hard_wall_axioms") or spec.get("claims", {}).get("hard_wall"):
        return "THEOREM-COND"
    return "EMPIRICAL"


def _cancelled_evidence(spec):
    c = spec.get("cancelled", {})
    return {
        "kind": "cancellation",
        "reason": str(c.get("reason", "")),
        "reversible": bool(c.get("reversible")),
        "reconsider_when": str(c.get("reconsider_when", "")),
        "metadata_complete": all(
            c.get(k) for k in ("reason", "evidence", "alternative", "reversible", "reconsider_when")
        ),
    }


def _numeric_probe(spec, tolerance_div=1):
    probe = spec.get("numeric_probe") or {}
    series = probe.get("series")
    claimed = probe.get("claimed")
    tolerance = probe.get("tolerance")
    if claimed is None or tolerance is None:
        return None
    if series == "basel":
        terms = int(probe.get("terms", 20000))
        computed = sum(1.0 / (n * n) for n in range(1, terms + 1))
    elif series == "pi_pow_pi":
        computed = math.pi ** math.pi
    else:
        return {
            "kind": "numeric_probe",
            "series": series,
            "verdict": "UNKNOWN_SERIES",
            "detail": f"unsupported series {series!r}",
        }
    tol = float(tolerance) / tolerance_div
    residual = abs(computed - float(claimed))
    return {
        "kind": "numeric_probe",
        "series": series,
        "computed": computed,
        "claimed": float(claimed),
        "residual": residual,
        "tolerance": tol,
        "verdict": "PASS" if residual <= tol else "FAIL",
    }


def _resolve_proof(spec, specimen_dir):
    proof_rel = (spec.get("artifact") or {}).get("proof")
    if not proof_rel:
        return None
    return Path(specimen_dir) / proof_rel


def observe(room, spec, engine, specimen_dir):
    if room not in ROOMS:
        raise ValueError(f"unknown room {room!r}")
    vote, claims_extra, evidence = {
        "F": _observe_f,
        "N": _observe_n,
        "S": _observe_s,
        "A": _observe_a,
    }[room](spec, engine, specimen_dir)
    claims = _wall_claims(spec, vote)
    claims.update(claims_extra or {})
    return vote, claims, evidence


def _observe_f(spec, engine, specimen_dir):
    evidence = []
    if spec.get("type") == "cancelled":
        evidence.append(_cancelled_evidence(spec))
        return "CANCELLED", {}, evidence
    machine = spec.get("machine", {})
    exit_code = machine.get("build_exit_code")
    proof = _resolve_proof(spec, specimen_dir)
    discovery = discovery_report(engine, proof, machine.get("axioms", []))
    scan = discovery["scan"]
    ax = discovery["axiom_audit"]
    evidence.append(
        {
            "kind": "static_scan",
            "exists": scan["exists"],
            "sha256": scan["sha256"],
            "sorry_count": scan["sorry_count"],
            "scanned_axioms": scan["axioms"],
            "declared_axioms": ax["declared_axioms"],
        }
    )
    evidence.append(
        {
            "kind": "whitelist_audit",
            "verdict": ax["verdict"],
            "outside_whitelist": ax["outside_whitelist"],
            "forbidden_axioms": ax["forbidden_axioms"],
            "undeclared_scan_drift": ax["undeclared_scan_drift"],
        }
    )
    if exit_code is None or exit_code != 0:
        evidence.insert(0, {"kind": "build_exit", "code": exit_code})
        return "REJECT", {"basis": "Room-F build/scan"}, evidence
    if not scan["exists"]:
        evidence.insert(0, {"kind": "build_exit", "code": exit_code, "detail": "proof file missing"})
        return "REJECT", {"basis": "Room-F build/scan"}, evidence
    if scan["sorry_count"] > 0 or machine.get("sorry_count", 0) > 0:
        evidence.insert(0, {"kind": "sorry_detected", "scan": scan["sorry_count"]})
        return "REJECT", {"basis": "Room-F build/scan"}, evidence
    if ax["verdict"] == "BLOCK":
        evidence.insert(0, {"kind": "axiom_block", "axiom_audit": ax})
        return "REJECT", {"basis": "Room-F build/scan"}, evidence
    vote = _wall_vote(spec, engine, discovery)
    if vote == "THEOREM-COND":
        evidence.append({"kind": "hard_wall", "axioms": ax["hard_wall_axioms"]})
    return vote, {"basis": "Room-F build/scan"}, evidence


def _observe_n(spec, engine, specimen_dir):
    evidence = []
    if spec.get("type") == "cancelled":
        evidence.append(_cancelled_evidence(spec))
        return "CANCELLED", {}, evidence
    probe = _numeric_probe(spec)
    if probe is None:
        evidence.append({"kind": "numeric_probe", "verdict": "ABSENT"})
        return "REJECT", {"basis": "Room-N numeric"}, evidence
    evidence.append(probe)
    if probe["verdict"] != "PASS":
        return "REJECT", {"basis": "Room-N numeric"}, evidence
    vote = "THEOREM-COND" if spec.get("claims", {}).get("hard_wall") else "EMPIRICAL"
    if vote == "THEOREM-COND":
        evidence.append({"kind": "hard_wall", "gap": spec["claims"]["hard_wall"]})
    return vote, {"basis": "Room-N numeric"}, evidence


def _observe_s(spec, engine, specimen_dir):
    evidence = []
    if spec.get("type") == "cancelled":
        ev = _cancelled_evidence(spec)
        evidence.append(ev)
        if not ev["metadata_complete"]:
            return "REJECT", {"basis": "Room-S semantic"}, evidence
        return "CANCELLED", {}, evidence
    claims = spec.get("claims", {})
    statement = str(claims.get("statement", ""))
    fp_hits = engine.find_forbidden_patterns(statement)
    if fp_hits:
        evidence.append({"kind": "forbidden_pattern", "ids": [h["id"] for h in fp_hits]})
    machine = spec.get("machine", {})
    if machine.get("build_exit_code") != 0:
        evidence.append(
            {"kind": "claim_consistency", "detail": "requested grade contradicts declared build failure"}
        )
        return "REJECT", {"basis": "Room-S semantic"}, evidence
    if fp_hits:
        return "REJECT", {"basis": "Room-S semantic"}, evidence
    if (
        claims.get("truth_grade_requested") == "THEOREM"
        and claims.get("truth_grade_basis") == "formal_syntax_only"
    ):
        evidence.append(
            {
                "kind": "claim_consistency",
                "detail": "THEOREM requested on formal_syntax_only basis -> capped at THEOREM-COND",
            }
        )
        vote = "THEOREM-COND"
    elif claims.get("hard_wall"):
        vote = "THEOREM-COND"
        evidence.append({"kind": "hard_wall", "gap": claims["hard_wall"]})
    else:
        vote = "EMPIRICAL"
    return vote, {"basis": "Room-S semantic"}, evidence


def _observe_a(spec, engine, specimen_dir):
    evidence = []
    if spec.get("type") == "cancelled":
        ev = _cancelled_evidence(spec)
        evidence.append(ev)
        if ev["reversible"] and ev["reconsider_when"]:
            return "CANCELLED", {}, evidence
        return "REJECT", {"basis": "Room-A adversarial"}, evidence
    machine = spec.get("machine", {})
    claims = spec.get("claims", {})
    fails = []
    if machine.get("build_exit_code") != 0:
        fails.append("declared_build_failure")
        evidence.append({"kind": "trust_nothing", "build_exit_code": machine.get("build_exit_code")})
    fp_hits = engine.find_forbidden_patterns(str(claims.get("statement", "")))
    if fp_hits:
        fails.append("forbidden_pattern")
        evidence.append({"kind": "forbidden_pattern", "ids": [h["id"] for h in fp_hits]})
    stress = _numeric_probe(spec, tolerance_div=10)
    if stress is not None:
        evidence.append({"kind": "stress_probe", **{k: stress[k] for k in ("residual", "tolerance", "verdict")}})
        if stress["verdict"] != "PASS":
            fails.append("stress_probe_fail")
    proof = _resolve_proof(spec, specimen_dir)
    discovery = discovery_report(engine, proof, machine.get("axioms", []))
    ax = discovery["axiom_audit"]
    evidence.append(
        {
            "kind": "whitelist_attack",
            "verdict": ax["verdict"],
            "outside_whitelist": ax["outside_whitelist"],
            "forbidden_axioms": ax["forbidden_axioms"],
        }
    )
    if ax["verdict"] == "BLOCK":
        fails.append("axiom_whitelist")
    if fails:
        return "REJECT", {"basis": "Room-A adversarial"}, evidence
    vote = "THEOREM-COND" if ax["hard_wall_axioms"] or claims.get("hard_wall") else "EMPIRICAL"
    if vote == "THEOREM-COND":
        evidence.append({"kind": "hard_wall", "axioms": ax["hard_wall_axioms"]})
    return vote, {"basis": "Room-A adversarial"}, evidence
