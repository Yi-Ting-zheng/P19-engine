import hashlib
import re
from pathlib import Path

from .audit import RuleEngine

AXIOM_DECL_RE = re.compile(r"^\s*(?:axiom|constant|opaque)\s+(\w+)", re.M)
IMPORT_RE = re.compile(r"^\s*import\s+(\S+)", re.M)
DECL_RE = re.compile(r"^\s*(?:theorem|lemma|def)\s+(\w+)", re.M)
SORRY_RE = re.compile(r"\bsorry\b")


def scan_lean(path):
    result = {
        "path": str(path) if path is not None else None,
        "exists": False,
        "sha256": None,
        "axioms": [],
        "sorry_count": 0,
        "imports": [],
        "declarations": [],
        "lines": 0,
    }
    if path is None:
        return result
    p = Path(path)
    if not p.is_file():
        return result
    raw = p.read_bytes()
    result["exists"] = True
    result["sha256"] = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8", errors="replace")
    result["lines"] = text.count("\n") + 1
    result["axioms"] = sorted(set(AXIOM_DECL_RE.findall(text)))
    result["sorry_count"] = len(SORRY_RE.findall(text))
    result["imports"] = IMPORT_RE.findall(text)
    result["declarations"] = DECL_RE.findall(text)
    return result


def axiom_verdict(engine: RuleEngine, scan, declared):
    scanned = set(scan.get("axioms") or [])
    declared_set = set(declared or [])
    drift = sorted(scanned - declared_set)
    outside, forbidden = engine.outside_whitelist(scanned | declared_set)
    whitelist = engine.axiom_whitelist or {}
    known_domain = set(whitelist.get("known_domain", []))
    hard_wall_axioms = sorted((scanned | declared_set) & known_domain)
    if forbidden or outside or drift:
        verdict = "BLOCK"
    elif hard_wall_axioms:
        verdict = "CONDITIONAL"
    else:
        verdict = "CLEAN"
    return {
        "verdict": verdict,
        "scanned_axioms": sorted(scanned),
        "declared_axioms": sorted(declared_set),
        "undeclared_scan_drift": drift,
        "outside_whitelist": outside,
        "forbidden_axioms": forbidden,
        "hard_wall_axioms": hard_wall_axioms,
    }


def discovery_report(engine: RuleEngine, lean_path, declared_axioms=None):
    scan = scan_lean(lean_path)
    ax = axiom_verdict(engine, scan, declared_axioms)
    return {
        "scan": scan,
        "axiom_audit": ax,
        "artifact_unavailable": not scan["exists"],
    }
