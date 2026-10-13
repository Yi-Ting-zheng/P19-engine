from collections import OrderedDict

STATES = (
    "QUEUED",
    "DISPATCHED",
    "COLLECTED",
    "CONFLICT_CHECK",
    "ARBITRATION",
    "FREEZED",
    "LEDGER_WRITE",
    "DONE",
)

TRANSITIONS = {
    "QUEUED": frozenset({"DISPATCHED"}),
    "DISPATCHED": frozenset({"COLLECTED", "FREEZED"}),
    "COLLECTED": frozenset({"CONFLICT_CHECK", "FREEZED"}),
    "CONFLICT_CHECK": frozenset({"ARBITRATION", "FREEZED"}),
    "ARBITRATION": frozenset({"LEDGER_WRITE", "FREEZED"}),
    "LEDGER_WRITE": frozenset({"DONE", "FREEZED"}),
    "FREEZED": frozenset(),
    "DONE": frozenset(),
}

TERMINAL_STATES = frozenset({"FREEZED", "DONE"})


class StateError(Exception):
    pass


class RunState:
    def __init__(self, run_id):
        self.run_id = run_id
        self.current = "QUEUED"
        self.history = [{"state": "QUEUED", "reason": "init"}]
        self.freeze_reason = None

    @property
    def terminal(self):
        return self.current in TERMINAL_STATES

    def can(self, target):
        return target in TRANSITIONS[self.current]

    def transition(self, target, reason=""):
        if target not in TRANSITIONS[self.current]:
            raise StateError(
                f"illegal transition {self.current} -> {target} "
                f"(allowed: {sorted(TRANSITIONS[self.current]) or 'none'})"
            )
        if target == "FREEZED":
            self.freeze_reason = reason or "unspecified"
        self.current = target
        self.history.append({"state": target, "reason": reason})
        return self.current

    def as_dict(self):
        return OrderedDict(
            run_id=self.run_id,
            state=self.current,
            freeze_reason=self.freeze_reason,
            history=list(self.history),
        )
