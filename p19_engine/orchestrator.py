import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml

from . import protocol, rooms
from .audit import RuleEngine
from .ledger import TruthLedger
from .state_machine import RunState


def arbitrate(votes):
    if not votes:
        return None
    counts = Counter(votes.values())
    top, top_n = counts.most_common(1)[0]
    if len(counts) == 1:
        return top
    if top_n >= 3:
        return top
    return None


def apply_audit_verdict(final, audit):
    if audit is None:
        return final
    for d in audit.downgrades:
        if final == "THEOREM" and d.get("downgrade_to"):
            final = d["downgrade_to"]
    return final


def run_specimen(
    specimen_dir,
    workdir,
    contract_path,
    ledger_path,
    timeout=20.0,
    run_id=None,
    pre_spawn_hook=None,
):
    specimen_dir = Path(specimen_dir)
    spec_path = specimen_dir / "specimen.yaml"
    contract_path = Path(contract_path)
    doc = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    spec = doc["specimen"]
    specimen_id = spec["id"]
    if run_id is None:
        run_id = f"{specimen_id}-{protocol.new_token()[:12]}"

    engine = RuleEngine.from_path(contract_path)
    contract_sha = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    state = RunState(run_id)
    rt = rooms.RoomRuntime(workdir, run_id, spec_path, contract_path)
    result = None
    try:
        rt.prepare()
        state.transition("DISPATCHED", "4 rooms dispatched")
        if pre_spawn_hook is not None:
            pre_spawn_hook(rt)
        rt.spawn()
        reports, missing = rt.collect(timeout=timeout)
        rt.wait_all(timeout=5.0)

        workers_iso = {
            room: (
                ((reports.get(room) or {}).get("claims") or {}).get("isolation_selfcheck")
            )
            for room in protocol.ROOMS
        }
        isolation_info = {"runtime": rt.isolation, "workers": workers_iso}
        result = {
            "run_id": run_id,
            "specimen_id": specimen_id,
            "state": state.as_dict(),
            "verdict": None,
            "votes": {},
            "audit": None,
            "missing": missing,
            "ledger_seq": None,
            "ledger_payload": None,
            "reports": {},
            "isolation": isolation_info,
        }
        (Path(workdir) / "isolation.json").write_text(
            json.dumps(isolation_info, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if missing:
            state.transition("FREEZED", f"report missing/invalid: {sorted(missing)}")
            result["state"] = state.as_dict()
            return result

        state.transition("COLLECTED", "4 valid reports")

        if rt.isolation.get("mode") == "acl_deny_list":
            bad = [
                room
                for room in protocol.ROOMS
                if (workers_iso[room] or {}).get("sibling_enumeration") != "BLOCKED"
            ]
            if bad:
                state.transition(
                    "FREEZED",
                    f"isolation violation: sibling enumeration not blocked in {sorted(bad)}",
                )
                result["state"] = state.as_dict()
                return result

        votes = {room: reports[room]["vote"] for room in protocol.ROOMS}
        result["votes"] = votes
        result["reports"] = {
            room: {
                "msg_hash": reports[room]["msg_hash"],
                "vote": reports[room]["vote"],
                "evidence_count": len(reports[room]["evidence"]),
            }
            for room in protocol.ROOMS
        }
        state.transition("CONFLICT_CHECK", f"distinct votes={len(set(votes.values()))}")
        state.transition("ARBITRATION", "audit evaluate + quorum")

        audit = engine.evaluate(spec.get("audit_facts") or {})
        result["audit"] = audit.as_dict()

        if audit.blocked:
            state.transition("FREEZED", f"audit BLOCK_START: {audit.rule_ids()}")
            result["state"] = state.as_dict()
            return result

        final = arbitrate(votes)
        if final is None:
            state.transition("FREEZED", f"no quorum: votes={votes}")
            result["state"] = state.as_dict()
            return result
        final = apply_audit_verdict(final, audit)
        result["verdict"] = final

        hard_wall = None
        gap_class = "none"
        for room in protocol.ROOMS:
            c = reports[room]["claims"]
            if c.get("hard_wall") and not hard_wall:
                hard_wall = c["hard_wall"]
            if c.get("gap_class") and c["gap_class"] != "none":
                gap_class = c["gap_class"]

        payload = {
            "specimen_id": specimen_id,
            "truth_status": final,
            "vote_breakdown": votes,
            "claims": {
                "gap_class": gap_class,
                "basis": "4-room quorum + math_attack_rules evaluation",
            },
            "rule_hits": [
                {
                    "rule_id": h["rule_id"],
                    "action": h["action"],
                    "downgrade_to": h.get("downgrade_to"),
                }
                for h in audit.hits
            ],
            "hard_wall": hard_wall,
            "gaps": [hard_wall] if hard_wall else [],
            "evidence_hashes": [
                {"room": room, "sha256": reports[room]["msg_hash"]}
                for room in protocol.ROOMS
            ],
            "contract": f"{contract_path.name}@{engine.meta.get('version', 'unknown')}#{contract_sha[:16]}",
        }

        state.transition("LEDGER_WRITE", f"truth_status={final}")
        ledger = TruthLedger(ledger_path)
        entry = ledger.append(payload)
        state.transition("DONE", f"ledger seq={entry['seq']}")
        result["ledger_seq"] = entry["seq"]
        result["ledger_payload"] = payload
        result["state"] = state.as_dict()
        return result
    finally:
        rt.release()
