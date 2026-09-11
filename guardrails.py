from __future__ import annotations
import re

FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|PRAGMA|ATTACH|DETACH|VACUUM)\b", re.I)
ALLOWED_OBJECTS = {"items", "shipments", "sales_daily", "shipment_units", "sales_enriched", "monthly_item_store"}

def validate_sql(sql: str) -> None:
    s = sql.strip().rstrip(";")
    if not re.match(r"^(SELECT|WITH)\b", s, re.I):
        raise ValueError("Only read-only SELECT/WITH queries are allowed.")
    if FORBIDDEN.search(s):
        raise ValueError("Query contains a forbidden SQL operation.")
    if ";" in s:
        raise ValueError("Only one SQL statement is allowed.")
    objects = re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", s, re.I)
    bad = [o for o in objects if o.lower() not in ALLOWED_OBJECTS and not o.lower().startswith("cte")]
    ctes = {m.lower() for m in re.findall(r"(?:WITH|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s+AS\s*\(", s, re.I)}
    bad = [o for o in bad if o.lower() not in ctes]
    if bad:
        raise ValueError(f"Query references non-allowed object(s): {', '.join(sorted(set(bad)))}")
