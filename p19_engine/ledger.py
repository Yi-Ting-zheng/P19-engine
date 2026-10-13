import json
from pathlib import Path

from .protocol import canonical_json, sha256_hex

GENESIS = sha256_hex("p19.truth_ledger/v1")

LEDGER_ENTRY_KEYS = (
    "specimen_id",
    "truth_status",
    "vote_breakdown",
    "claims",
    "rule_hits",
    "hard_wall",
    "gaps",
    "evidence_hashes",
    "contract",
)


class LedgerError(Exception):
    pass


def _entry_hash(seq, payload, prev_hash):
    return sha256_hex(canonical_json({"seq": seq, "payload": payload, "prev_hash": prev_hash}))


class TruthLedger:
    def __init__(self, path):
        self.path = Path(path)

    def _load_lines(self):
        if not self.path.is_file():
            return []
        lines = []
        for i, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise LedgerError(f"line {i}: invalid JSON ({e})") from e
            if not isinstance(obj, dict):
                raise LedgerError(f"line {i}: entry must be an object")
            lines.append(obj)
        return lines

    def entries(self):
        return self._load_lines()

    def tip(self):
        lines = self._load_lines()
        if not lines:
            return GENESIS, 0
        last = lines[-1]
        return last.get("entry_hash", ""), last.get("seq", len(lines))

    def append(self, payload):
        if not isinstance(payload, dict):
            raise LedgerError("payload must be a dict")
        missing = [k for k in LEDGER_ENTRY_KEYS if k not in payload]
        if missing:
            raise LedgerError(f"payload missing keys {missing}")
        prev_hash, seq = self.tip()
        seq += 1
        entry = {"seq": seq, "payload": payload, "prev_hash": prev_hash}
        entry["entry_hash"] = _entry_hash(seq, payload, prev_hash)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        return entry

    def verify(self):
        try:
            lines = self._load_lines()
        except LedgerError as e:
            return False, str(e)
        prev = GENESIS
        for i, entry in enumerate(lines, 1):
            for key in ("seq", "payload", "prev_hash", "entry_hash"):
                if key not in entry:
                    return False, f"entry {i}: missing {key}"
            if entry["seq"] != i:
                return False, f"entry {i}: seq {entry['seq']} != {i}"
            if entry["prev_hash"] != prev:
                return False, f"entry {i}: prev_hash chain broken"
            expect = _entry_hash(entry["seq"], entry["payload"], entry["prev_hash"])
            if entry["entry_hash"] != expect:
                return False, f"entry {i}: entry_hash mismatch (tampered)"
            prev = entry["entry_hash"]
        return True, f"chain intact ({len(lines)} entries)"
