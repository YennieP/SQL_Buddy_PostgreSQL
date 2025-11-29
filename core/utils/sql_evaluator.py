# core/utils/sql_evaluator.py

import re
from typing import Tuple, Dict, Set


def _normalize_sql(sql: str) -> str:
    if not sql:
        return ""
    s = sql.strip()

    if s.endswith(";"):
        s = s[:-1]

    s = re.sub(r"--.*?$", "", s, flags=re.MULTILINE)

    s = re.sub(r"\s+", " ", s)

    return s.lower().strip()


def _split_select_from_where(sql: str) -> Dict[str, str]:
    s = _normalize_sql(sql)

    result = {"select": "", "from": "", "where": ""}

    m = re.match(r"select\s+(.*?)\s+from\s+(.*)", s)
    if not m:
        result["select"] = s
        return result

    result["select"] = m.group(1)
    rest = m.group(2)

    where_idx = rest.find(" where ")
    if where_idx == -1:
        result["from"] = rest
    else:
        result["from"] = rest[:where_idx]
        result["where"] = rest[where_idx + len(" where "):]

    return result


def _split_by_comma(s: str):
    return [item.strip() for item in s.split(",") if item.strip()]


def _split_where_conditions(where: str):
    if not where:
        return []
    parts = [p.strip() for p in where.split(" and ") if p.strip()]
    return parts


def _normalize_identifier(identifier: str) -> str:
    if not identifier:
        return ""
    s = identifier.strip()
    s = s.replace("`", "")

    s = re.sub(r"\s+as\s+\w+$", "", s, flags=re.IGNORECASE)

    if "." in s:
        s = s.split(".")[-1]

    return s.lower().strip()


def _extract_select_columns(select_clause: str) -> Set[str]:
    cols: Set[str] = set()
    for part in _split_by_comma(select_clause):
        p = part.strip()
        if not p:
            continue

        if "(" in p or ")" in p:
            cols.add(re.sub(r"\s+", " ", p.lower()))
        else:
            cols.add(_normalize_identifier(p))

    return cols


def _extract_tables(from_clause: str) -> Set[str]:
    tables: Set[str] = set()
    if not from_clause:
        return tables

    s = from_clause.lower()

    matches = re.findall(
        r"\bfrom\s+([a-z_][a-z0-9_]*)|\bjoin\s+([a-z_][a-z0-9_]*)",
        s,
    )

    for m in matches:
        name = m[0] or m[1]
        if name:
            tables.add(name.strip())

    if not tables:
        for part in _split_by_comma(s):
            token = part.split()[0]
            if token:
                tables.add(token.strip())

    return tables


def _normalize_condition(cond: str) -> str:
    if not cond:
        return ""
    s = cond.strip()
    while s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def _extract_where_conditions(where_clause: str) -> Set[str]:
    conds_raw = _split_where_conditions(where_clause)
    return { _normalize_condition(c) for c in conds_raw if _normalize_condition(c) }


def _f1_score(correct: Set[str], student: Set[str]) -> float:
    if not correct:
        return 1.0

    if not student:
        return 0.0

    inter = correct & student
    if not inter:
        return 0.0

    precision = len(inter) / len(student)
    recall = len(inter) / len(correct)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compare_query_structure(correct_sql: str, student_sql: str) -> Tuple[bool, Dict]:
    c_parts = _split_select_from_where(correct_sql)
    s_parts = _split_select_from_where(student_sql)

    c_tables = _extract_tables(c_parts["from"])
    s_tables = _extract_tables(s_parts["from"])

    c_cols = _extract_select_columns(c_parts["select"])
    s_cols = _extract_select_columns(s_parts["select"])

    c_conds = _extract_where_conditions(c_parts["where"])
    s_conds = _extract_where_conditions(s_parts["where"])

    from_ok = (c_tables == s_tables)
    select_ok = (c_cols == s_cols)
    where_ok = (c_conds == s_conds)

    details = {
        "correct": {
            "tables": sorted(c_tables),
            "columns": sorted(c_cols),
            "conditions": sorted(c_conds),
        },
        "student": {
            "tables": sorted(s_tables),
            "columns": sorted(s_cols),
            "conditions": sorted(s_conds),
        },
        "from_ok": from_ok,
        "select_ok": select_ok,
        "where_ok": where_ok,
    }

    is_equal = from_ok and select_ok and where_ok
    return is_equal, details


def evaluate_sql_answer(student_sql: str, correct_sql: str) -> Tuple[float, Dict]:
    is_equal, details = compare_query_structure(correct_sql, student_sql)

    c_tables = set(details["correct"]["tables"])
    s_tables = set(details["student"]["tables"])

    c_cols = set(details["correct"]["columns"])
    s_cols = set(details["student"]["columns"])

    c_conds = set(details["correct"]["conditions"])
    s_conds = set(details["student"]["conditions"])

    from_f1 = _f1_score(c_tables, s_tables)
    select_f1 = _f1_score(c_cols, s_cols)
    where_f1 = _f1_score(c_conds, s_conds)

    from_score = 40 * from_f1
    select_score = 30 * select_f1
    where_score = 30 * where_f1

    score = from_score + select_score + where_score

    if is_equal:
        score = 100.0

    details["is_equal"] = is_equal
    details["score_breakdown"] = {
        "from": round(from_score, 1),
        "select": round(select_score, 1),
        "where": round(where_score, 1),
        "from_f1": round(from_f1, 3),
        "select_f1": round(select_f1, 3),
        "where_f1": round(where_f1, 3),
    }

    details["debug"] = {
        "correct_raw": _split_select_from_where(correct_sql),
        "student_raw": _split_select_from_where(student_sql),
    }

    return float(round(score, 1)), details