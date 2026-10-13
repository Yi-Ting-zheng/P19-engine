import argparse
import sys
from pathlib import Path

import yaml

from . import isolation, observers, protocol
from .audit import RuleEngine


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="p19_room_worker")
    ap.add_argument("--inbox", required=True)
    ap.add_argument("--outbox", required=True)
    ap.add_argument("--room", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--contract", required=True)
    args = ap.parse_args(argv)

    try:
        dispatch = protocol.read_message(args.inbox)
        protocol.validate_dispatch(
            dispatch,
            expect_room=args.room,
            expect_token=args.token,
        )
        spec_path = Path(dispatch["artifact_ref"])
        if not spec_path.is_file():
            raise protocol.ProtocolError(f"specimen file not found: {spec_path}")
        doc = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or "specimen" not in doc:
            raise protocol.ProtocolError(f"invalid specimen file: {spec_path}")
        spec = doc["specimen"]
        if spec.get("id") != dispatch["specimen_id"]:
            raise protocol.ProtocolError("specimen id mismatch vs dispatch")

        engine = RuleEngine.from_path(args.contract)
        vote, claims, evidence = observers.observe(
            args.room, spec, engine, spec_path.parent
        )
        claims["isolation_selfcheck"] = isolation.selfcheck(args.inbox)
        report = protocol.make_report(
            dispatch["run_id"],
            dispatch["specimen_id"],
            args.room,
            args.token,
            vote,
            claims,
            evidence,
        )
        protocol.validate_report(
            report,
            expect_room=args.room,
            expect_run=dispatch["run_id"],
            expect_specimen=dispatch["specimen_id"],
            expect_token=args.token,
        )
        protocol.write_message(args.outbox, report)
        return 0
    except Exception as e:
        print(f"[room_worker {args.room}] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
