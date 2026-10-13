import re
from pathlib import Path

import yaml

BASE_ACTIONS = frozenset(
    {"BLOCK_START", "DOWNGRADE", "FLAG_AMBIGUOUS", "FLAG_REWORK", "REJECT_EVIDENCE"}
)
EXTENDED_ACTIONS = frozenset(
    {"ESCALATE_SCAN", "FREEZE_CONSTANT", "LAUNCH_CASCADE", "REFINE_SAMPLE"}
)
ALL_ACTIONS = BASE_ACTIONS | EXTENDED_ACTIONS


class AuditError(Exception):
    pass


class _Unresolvable(Exception):
    pass


def _strict_eq(a, b):
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return a == b


_TOKEN_RE = re.compile(
    r"""\s*(?:
        (?P<STRING>"[^"]*"|'[^']*')
      | (?P<NUMBER>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
      | (?P<ID>[A-Za-z_][A-Za-z0-9_.]*)
      | (?P<OP>==|!=|<=|>=|=|<|>)
      | (?P<LPAREN>\()
      | (?P<RPAREN>\))
      | (?P<AND>and|\u2227)
      | (?P<OR>or|\u2228)
      | (?P<NOT>not|\u00ac)
    )""",
    re.VERBOSE,
)

_KEYWORDS = {"and", "or", "not"}


def _tokenize(text):
    tokens = []
    pos = 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        m = _TOKEN_RE.match(text, pos)
        if not m or m.start() != pos:
            raise AuditError(f"cannot tokenize when-expression at: {text[pos:pos+20]!r}")
        pos = m.end()
        kind = m.lastgroup
        val = m.group(kind)
        if kind == "ID" and val.lower() in _KEYWORDS:
            kind = val.upper()
        tokens.append((kind, val))
    tokens.append(("EOF", ""))
    return tokens


class _Parser:
    def __init__(self, tokens, facts):
        self.toks = tokens
        self.i = 0
        self.facts = facts

    def peek(self):
        return self.toks[self.i]

    def next(self):
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def expect(self, kind):
        tok = self.next()
        if tok[0] != kind:
            raise AuditError(f"expected {kind}, got {tok}")
        return tok

    def parse(self):
        v = self.parse_or()
        if self.peek()[0] != "EOF":
            raise AuditError(f"trailing tokens: {self.peek()}")
        return v

    def parse_or(self):
        v = self.parse_and()
        while self.peek()[0] == "OR":
            self.next()
            rhs = self.parse_and()
            v = v or rhs
        return v

    def parse_and(self):
        v = self.parse_not()
        while self.peek()[0] == "AND":
            self.next()
            rhs = self.parse_not()
            v = v and rhs
        return v

    def parse_not(self):
        if self.peek()[0] == "NOT":
            self.next()
            return not self.parse_not()
        if self.peek()[0] == "LPAREN":
            self.next()
            v = self.parse_or()
            self.expect("RPAREN")
            return v
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_operand()
        kind, op = self.peek()
        if kind != "OP":
            if left is _MISSING:
                raise _Unresolvable()
            return bool(left)
        self.next()
        right = self.parse_operand()
        if left is _MISSING or right is _MISSING:
            raise _Unresolvable()
        if op in ("==", "="):
            return _strict_eq(left, right)
        if op == "!=":
            return not _strict_eq(left, right)
        try:
            lnum, rnum = float(left), float(right)
        except (TypeError, ValueError):
            raise _Unresolvable()
        if op == "<":
            return lnum < rnum
        if op == "<=":
            return lnum <= rnum
        if op == ">":
            return lnum > rnum
        if op == ">=":
            return lnum >= rnum
        raise AuditError(f"unknown operator {op!r}")

    def parse_operand(self):
        kind, val = self.next()
        if kind == "STRING":
            return val[1:-1]
        if kind == "NUMBER":
            return float(val)
        if kind == "ID":
            if val not in self.facts:
                return _MISSING
            return self.facts[val]
        raise AuditError(f"expected operand, got {(kind, val)}")


class _Missing:
    def __repr__(self):
        return "<missing>"


_MISSING = _Missing()


def eval_string_when(expr, facts):
    parser = _Parser(_tokenize(expr), facts)
    try:
        return bool(parser.parse())
    except _Unresolvable:
        return False


def eval_when(when, facts):
    if isinstance(when, dict):
        for k, v in when.items():
            if k not in facts or not _strict_eq(facts[k], v):
                return False
        return True
    if isinstance(when, str):
        return eval_string_when(when, facts)
    raise AuditError(f"unsupported when type: {type(when).__name__}")


def _norm(text):
    return re.sub(r"\s+", " ", text).strip().lower()


class AuditResult:
    def __init__(self, hits, facts_after):
        self.hits = hits
        self.facts_after = facts_after

    @property
    def blocked(self):
        return any(h["action"] == "BLOCK_START" for h in self.hits)

    @property
    def downgrades(self):
        return [h for h in self.hits if h["action"] == "DOWNGRADE"]

    def actions(self):
        return [h["action"] for h in self.hits]

    def rule_ids(self):
        return [h["rule_id"] for h in self.hits]

    def as_dict(self):
        return {
            "hits": [
                {
                    "rule_id": h["rule_id"],
                    "action": h["action"],
                    "emit": h["emit"],
                    "downgrade_to": h.get("downgrade_to"),
                }
                for h in self.hits
            ],
            "blocked": self.blocked,
        }


class RuleEngine:
    def __init__(self, doc):
        if not isinstance(doc, dict) or "rules" not in doc:
            raise AuditError("contract must be a mapping with a 'rules' list")
        self.doc = doc
        self.meta = doc.get("meta", {})
        vocab = self.meta.get("action_vocabulary_extension", {})
        allowed = set(vocab.get("base_vocabulary", BASE_ACTIONS)) | set(
            vocab.get("extended_vocabulary", EXTENDED_ACTIONS)
        )
        self.allowed_actions = frozenset(allowed)
        self.rules = doc["rules"]
        self.forbidden_patterns = doc.get("forbidden_patterns", [])
        self.axiom_whitelist = doc.get("axiom_whitelist", {})
        self._validate()

    def _validate(self):
        if not isinstance(self.rules, list) or not self.rules:
            raise AuditError("rules must be a non-empty list")
        seen = set()
        for r in self.rules:
            rid = r.get("id")
            if not rid:
                raise AuditError("rule missing id")
            if rid in seen:
                raise AuditError(f"duplicate rule id {rid}")
            seen.add(rid)
            if "when" not in r:
                raise AuditError(f"{rid}: missing when")
            then = r.get("then")
            if not isinstance(then, dict) or "action" not in then:
                raise AuditError(f"{rid}: then.action missing")
            action = then["action"]
            if action not in self.allowed_actions:
                raise AuditError(f"{rid}: action {action!r} not in vocabulary")
            forbidden = then.get("forbidden", [])
            if action in forbidden:
                raise AuditError(f"{rid}: then.action {action!r} listed in its own forbidden")

    @classmethod
    def from_path(cls, path):
        p = Path(path)
        if not p.is_file():
            raise AuditError(f"contract file not found: {p}")
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise AuditError(f"invalid YAML in {p}: {e}") from e
        return cls(doc)

    def evaluate(self, facts):
        if not isinstance(facts, dict):
            raise AuditError("facts must be a dict")
        working = dict(facts)
        hits = []
        for rule in self.rules:
            if not eval_when(rule["when"], working):
                continue
            then = rule["then"]
            hit = {
                "rule_id": rule["id"],
                "name": rule.get("name", ""),
                "action": then["action"],
                "emit": then.get("emit", ""),
                "escalation": then.get("escalation"),
            }
            if "downgrade_to" in then:
                hit["downgrade_to"] = then["downgrade_to"]
            hits.append(hit)
            if then.get("cascade_parent_triggered") is True:
                working["cascade_parent_triggered"] = True
        return AuditResult(hits, working)

    def find_forbidden_patterns(self, text):
        if not isinstance(text, str) or not text.strip():
            return []
        norm = _norm(text)
        found = []
        for fp in self.forbidden_patterns:
            bad = _norm(str(fp.get("bad", "")))
            if bad and bad in norm:
                found.append({"id": fp.get("id"), "why": _norm(str(fp.get("why", "")))})
        return found

    def outside_whitelist(self, axiom_names):
        allowed = set(self.axiom_whitelist.get("core_lean", [])) | set(
            self.axiom_whitelist.get("known_domain", [])
        )
        forbidden = set(self.axiom_whitelist.get("forbidden", []))
        names = set(axiom_names)
        return sorted(names - allowed), sorted(names & forbidden)
