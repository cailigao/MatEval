"""MatKG Call: per-record ACC (rule-based SPARQL equivalence)."""
from __future__ import annotations

import re

from src.common import compute_per_record

SLUG = "matkg_call"
TITLE = "MatKG Call"
METRIC_NAME = "ACC"
SCALE = 1.0

_FENCE_RE = re.compile(r"```(?:sparql)?\s*(.*?)\s*```", re.IGNORECASE | re.DOTALL)
_COMMENT_RE = re.compile(r"#[^\n]*")
_PREFIX_RE = re.compile(r"PREFIX\s+([A-Za-z_][\w.-]*)\s*:\s*<([^>]*)>", re.IGNORECASE)
_VAR_RE = re.compile(r"[?$]([A-Za-z_]\w*)")
_WS_RE = re.compile(r"\s+")


def _extract_sparql(text: str | None) -> str:
    if not text:
        return ""
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def _is_parseable(sparql: str) -> bool:
    try:
        from rdflib.plugins.sparql import prepareQuery
        prepareQuery(sparql)
        return True
    except Exception:
        return False


def _strip_filters(body: str) -> str:
    out = []
    i, n = 0, len(body)
    while i < n:
        m = re.match(r"FILTER\s*\(", body[i:], re.IGNORECASE)
        if m:
            paren_start = i + m.end() - 1
            depth = 0
            j = paren_start
            in_str = False
            quote = ""
            while j < n:
                c = body[j]
                if in_str:
                    if c == "\\" and j + 1 < n:
                        j += 2
                        continue
                    if c == quote:
                        in_str = False
                    j += 1
                    continue
                if c == '"' or c == "'":
                    in_str = True
                    quote = c
                elif c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                j += 1
            i = j
            out.append(" ")
        else:
            out.append(body[i])
            i += 1
    return "".join(out)


def _extract_filters(s: str) -> list:
    found = []
    i, n = 0, len(s)
    while i < n:
        m = re.match(r"FILTER\s*\(", s[i:], re.IGNORECASE)
        if m:
            start = i
            paren_start = i + m.end() - 1
            depth = 0
            j = paren_start
            in_str = False
            quote = ""
            while j < n:
                c = s[j]
                if in_str:
                    if c == "\\" and j + 1 < n:
                        j += 2
                        continue
                    if c == quote:
                        in_str = False
                    j += 1
                    continue
                if c == '"' or c == "'":
                    in_str = True
                    quote = c
                elif c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                j += 1
            found.append(s[start:j])
            i = j
        else:
            i += 1
    return found


def _split_top_level(body: str, sep: str) -> list:
    parts = []
    buf = []
    i, n = 0, len(body)
    in_iri = False
    in_str = False
    quote = ""
    while i < n:
        c = body[i]
        if in_iri:
            buf.append(c)
            if c == ">":
                in_iri = False
            i += 1
            continue
        if in_str:
            buf.append(c)
            if c == "\\" and i + 1 < n:
                buf.append(body[i + 1])
                i += 2
                continue
            if c == quote:
                in_str = False
            i += 1
            continue
        if c == "<":
            in_iri = True
            buf.append(c)
        elif c == '"' or c == "'":
            in_str = True
            quote = c
            buf.append(c)
        elif c == sep:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    if buf:
        parts.append("".join(buf))
    return parts


def _tokenize(s: str) -> list:
    tokens = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c == "<":
            j = s.find(">", i)
            if j == -1:
                tokens.append(s[i:])
                break
            tokens.append(s[i : j + 1])
            i = j + 1
        elif c == '"' or c == "'":
            quote = c
            j = i + 1
            while j < n and s[j] != quote:
                if s[j] == "\\":
                    j += 2
                else:
                    j += 1
            tokens.append(s[i : j + 1])
            i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in "<\"',":
                j += 1
            tok = s[i:j]
            if tok.endswith(","):
                tok = tok[:-1]
            if tok:
                tokens.append(tok)
            i = j
            while i < n and s[i] == ",":
                i += 1
    return [t for t in tokens if t and t != ","]


def _split_triples(body: str) -> list:
    triples = []
    statements = [s.strip() for s in _split_top_level(body, ".") if s.strip()]
    for stmt in statements:
        if ";" in stmt:
            parts = [p.strip() for p in _split_top_level(stmt, ";") if p.strip()]
        else:
            parts = [stmt.strip()]
        if not parts:
            continue
        subject = None
        predicate = None
        for pi, part in enumerate(parts):
            tokens = _tokenize(part)
            if not tokens:
                continue
            if pi == 0:
                if len(tokens) < 2:
                    continue
                subject = tokens[0]
                predicate = tokens[1]
                objs = tokens[2:]
            else:
                predicate = tokens[0]
                objs = tokens[1:]
            for o in objs:
                triples.append((subject, predicate, o))
    return triples


def _expand_prefixed(text: str, prefixes: dict) -> str:
    def repl(m):
        prefix, local = m.group(1), m.group(2)
        if prefix in prefixes:
            return f"<{prefixes[prefix]}{local}>"
        return m.group(0)
    return re.sub(r"\b([A-Za-z_][\w.-]*):([^\s<>(){}\[\].,;]+)", repl, text)


def _canonicalize_vars(text: str) -> str:
    mapping = {}
    counter = [0]
    def repl(m):
        name = m.group(1)
        if name not in mapping:
            counter[0] += 1
            mapping[name] = f"?v{counter[0]}"
        return mapping[name]
    return _VAR_RE.sub(repl, text)


def _extract_block(text: str, keyword: str):
    m = re.search(rf"\b{keyword}\s*\{{", text, re.IGNORECASE)
    if not m:
        return None
    start = m.end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[start : i - 1] if depth == 0 else text[start:]


def _normalize(sparql: str) -> dict:
    s = _COMMENT_RE.sub("", sparql)
    prefixes = {m.group(1): m.group(2) for m in _PREFIX_RE.finditer(s)}
    s = _PREFIX_RE.sub("", s)
    s = re.sub(r"\bBASE\s+<[^>]*>", "", s, flags=re.IGNORECASE)
    s = _expand_prefixed(s, prefixes)
    s = _canonicalize_vars(s)
    s = _WS_RE.sub(" ", s).strip()

    distinct = bool(re.search(r"\bSELECT\s+DISTINCT\b", s, re.IGNORECASE))

    proj_match = re.search(r"\bSELECT\b(.*?)(?:\bWHERE\b|\{)", s, re.IGNORECASE | re.DOTALL)
    projection = frozenset()
    if proj_match:
        proj = proj_match.group(1)
        proj = re.sub(r"\bDISTINCT\b", "", proj, flags=re.IGNORECASE)
        proj = re.sub(r"\bREDUCED\b", "", proj, flags=re.IGNORECASE)
        proj = re.sub(r"\([^)]*?AS\s+([?$]\w+)\s*\)", r"\1", proj, flags=re.IGNORECASE)
        proj_vars = _VAR_RE.findall(proj)
        projection = frozenset(f"?{v}" for v in proj_vars)

    body = _extract_block(s, "WHERE")
    if body is None:
        m = re.search(r"\{", s)
        if m:
            depth = 1
            i = m.end()
            while i < len(s) and depth > 0:
                if s[i] == "{":
                    depth += 1
                elif s[i] == "}":
                    depth -= 1
                i += 1
            body = s[m.end() : i - 1]
        else:
            body = ""
    body = body or ""
    body_no_filter = _strip_filters(body)
    triples = _split_triples(body_no_filter)
    triple_set = frozenset(f"{sub} {pred} {obj}" for sub, pred, obj in triples)

    filters = [_WS_RE.sub(" ", f).strip() for f in _extract_filters(s)]
    filter_set = frozenset(filters)

    gb_match = re.search(r"\bGROUP\s+BY\b(.*?)(?:\bORDER\b|\bLIMIT\b|\bOFFSET\b|$)",
                          s, re.IGNORECASE | re.DOTALL)
    group_by = tuple()
    if gb_match:
        group_by = tuple(sorted(f"?{v}" for v in _VAR_RE.findall(gb_match.group(1))))

    order_by = tuple()
    ob_match = re.search(r"\bORDER\s+BY\b(.*?)(?:\bLIMIT\b|\bOFFSET\b|$)",
                         s, re.IGNORECASE | re.DOTALL)
    if ob_match:
        items = _WS_RE.sub(" ", ob_match.group(1)).strip().split()
        seq = []
        i = 0
        while i < len(items):
            tok = items[i]
            direction = "ASC"
            if tok.upper() in ("ASC", "DESC"):
                direction = tok.upper()
                i += 1
                if i < len(items):
                    seq.append(f"{items[i]}:{direction}")
            else:
                seq.append(f"{tok}:ASC")
            i += 1
        order_by = tuple(seq)

    limit = None
    lim_match = re.search(r"\bLIMIT\s+(\d+)", s, re.IGNORECASE)
    if lim_match:
        limit = int(lim_match.group(1))

    structures = set()
    for kw in ("UNION", "OPTIONAL", "MINUS", "VALUES", "BIND", "GRAPH"):
        if re.search(rf"\b{kw}\b", s, re.IGNORECASE):
            structures.add(kw)
    select_count = len(re.findall(r"\bSELECT\b", s, re.IGNORECASE))
    if select_count > 1:
        structures.add("SUBSELECT")

    return {
        "distinct": distinct,
        "projection": projection,
        "triples": triple_set,
        "filters": filter_set,
        "group_by": group_by,
        "order_by": order_by,
        "limit": limit,
        "structures": frozenset(structures),
    }


def score_query(model_answer, target) -> float:
    m = _extract_sparql(model_answer if isinstance(model_answer, str) else str(model_answer or ""))
    t = _extract_sparql(target if isinstance(target, str) else str(target or ""))
    if not m or not t:
        return 0.0
    if not _is_parseable(m):
        return 0.0
    return 1.0 if _normalize(m) == _normalize(t) else 0.0


def score(r: dict) -> float:
    return score_query(r.get("answer", ""), r.get("target", ""))


def compute(records: list[dict]) -> tuple[float, str, list[dict]]:
    metric, out = compute_per_record(records, score, scale=SCALE)
    return metric, METRIC_NAME, out
