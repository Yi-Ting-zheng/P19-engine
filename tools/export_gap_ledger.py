import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_ledger(registry_path: Path) -> dict:
    raw = registry_path.read_text(encoding="utf-8")
    doc = yaml.safe_load(raw)
    reg = doc["registry"]
    registry_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    entries = []
    prev = sha256_hex("p19.gap_ledger/v1")
    for gap in reg["gaps"]:
        body = {
            "seq": len(entries) + 1,
            "gap": gap,
            "registry_version": reg["version"],
            "prev_hash": prev,
        }
        entry_hash = sha256_hex(json.dumps(body, sort_keys=True, ensure_ascii=False))
        entries.append({**body, "entry_hash": entry_hash})
        prev = entry_hash
    return {
        "gap_ledger": {
            "registry_version": reg["version"],
            "registry_sha256": registry_sha,
            "source_docs": reg.get("source_docs", []),
            "statistics": reg.get("statistics", {}),
            "entries": entries,
            "tail_hash": prev,
            "hard_wall_meta": doc.get("hard_wall_meta"),
            "append_only": True,
        }
    }


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="export_gap_ledger")
    ap.add_argument("--registry", default=str(REPO_ROOT / "config" / "gap_registry.yaml"))
    ap.add_argument(
        "--out",
        default=str(REPO_ROOT / "specimens" / "positive" / "Specimen-002" / "evidence" / "gap_ledger.yaml"),
    )
    args = ap.parse_args(argv)

    registry_path = Path(args.registry)
    if not registry_path.is_file():
        print(f"registry not found: {registry_path}", file=sys.stderr)
        return 2
    ledger = build_ledger(registry_path)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        yaml.safe_dump(ledger, allow_unicode=True, sort_keys=True, default_flow_style=False),
        encoding="utf-8",
    )
    gl = ledger["gap_ledger"]
    print(f"gap_ledger exported: {out}")
    print(f"  entries: {len(gl['entries'])}  tail: {gl['tail_hash'][:16]}...")
    print(f"  registry_sha256: {gl['registry_sha256'][:16]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
