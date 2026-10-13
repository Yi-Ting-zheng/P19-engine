import argparse
import sys
import time
from pathlib import Path

import yaml

from .ledger import TruthLedger
from .orchestrator import run_specimen

REPO_ROOT = Path(__file__).resolve().parent.parent

SPECIMEN_MAP = {
    "001": "specimens/negative/Specimen-001",
    "002": "specimens/positive/Specimen-002",
    "003": "specimens/cancelled/Specimen-003",
    "Specimen-001": "specimens/negative/Specimen-001",
    "Specimen-002": "specimens/positive/Specimen-002",
    "Specimen-003": "specimens/cancelled/Specimen-003",
}
ORDER = ["001", "002", "003"]


def check_expect(spec, result):
    exp = spec.get("expect") or {}
    fails = []
    if "verdict" in exp and exp["verdict"] != result["verdict"]:
        fails.append(f"verdict: expected {exp['verdict']!r}, got {result['verdict']!r}")
    if "state" in exp and exp["state"] != result["state"]["state"]:
        fails.append(f"state: expected {exp['state']!r}, got {result['state']['state']!r}")
    if "votes" in exp and exp["votes"] != result["votes"]:
        fails.append(f"votes: expected {exp['votes']!r}, got {result['votes']!r}")
    got_hits = (result["audit"] or {}).get("hits", [])
    got_ids = [h["rule_id"] for h in got_hits]
    if "rule_hits" in exp and exp["rule_hits"] != got_ids:
        fails.append(f"rule_hits: expected {exp['rule_hits']!r}, got {got_ids!r}")
    if result["verdict"] is not None:
        if "hard_wall" in exp and exp["hard_wall"] != (result["ledger_payload"] or {}).get("hard_wall"):
            fails.append(
                f"hard_wall: expected {exp['hard_wall']!r}, got {(result['ledger_payload'] or {}).get('hard_wall')!r}"
            )
        if "ledger_truth_status" in exp:
            got = (result["ledger_payload"] or {}).get("truth_status")
            if exp["ledger_truth_status"] != got:
                fails.append(
                    f"ledger_truth_status: expected {exp['ledger_truth_status']!r}, got {got!r}"
                )
    if result["missing"]:
        fails.append(f"missing reports: {result['missing']}")
    return fails


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="run_p0", description="P19 P0 one-shot closed loop")
    ap.add_argument("--specimen", default="all", help="001|002|003|all")
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--contract", default=str(REPO_ROOT / "config" / "math_attack_rules.yaml"))
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--timeout", type=float, default=20.0)
    args = ap.parse_args(argv)

    ids = ORDER if args.specimen == "all" else [args.specimen]
    for sid in ids:
        if sid not in SPECIMEN_MAP:
            print(f"unknown specimen {sid!r}; choose 001|002|003|all", file=sys.stderr)
            return 2

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    workdir = Path(args.workdir) if args.workdir else REPO_ROOT / "runs" / f"p0_{stamp}"
    workdir.mkdir(parents=True, exist_ok=True)
    ledger_path = Path(args.ledger) if args.ledger else REPO_ROOT / "runs" / "truth_ledger.jsonl"

    all_ok = True
    for sid in ids:
        specimen_dir = REPO_ROOT / SPECIMEN_MAP[sid]
        spec = yaml.safe_load((specimen_dir / "specimen.yaml").read_text(encoding="utf-8"))["specimen"]
        run_dir = workdir / spec["id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        result = run_specimen(
            specimen_dir=specimen_dir,
            workdir=run_dir,
            contract_path=args.contract,
            ledger_path=ledger_path,
            timeout=args.timeout,
        )
        fails = check_expect(spec, result)
        ok = not fails
        all_ok = all_ok and ok
        hits = (result["audit"] or {}).get("hits", [])
        hit_str = ",".join(h["rule_id"] for h in hits) or "-"
        votes_str = " ".join(f"{r}={result['votes'].get(r, '?')}" for r in ("F", "N", "S", "A"))
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {spec['id']} verdict={result['verdict']} state={result['state']['state']} votes: {votes_str} hits: {hit_str}")
        for f in fails:
            print(f"       - {f}")

    ledger = TruthLedger(ledger_path)
    intact, detail = ledger.verify()
    print(f"ledger: {ledger_path} — verify: {'OK' if intact else 'BROKEN'} ({detail})")
    print(f"runs: {workdir}")
    if not all_ok or not intact:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
