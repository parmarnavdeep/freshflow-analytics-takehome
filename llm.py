from __future__ import annotations
import json
import os
import re
from openai import OpenAI
from business_rules import BUSINESS_CONTEXT

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

SCHEMA = r'''
SQLite tables/views available:
items(item_id, description, dept, category, unit_of_measure, case_size, unit_cost)
shipments(date, store_id, banner, region, item_id, cases_received)
sales_daily(date, store_id, banner, region, item_id, units_sold, net_sales)
shipment_units(date, store_id, banner, region, item_id, description, dept, category, unit_of_measure, case_size, unit_cost, cases_received, shipped_units)
sales_enriched(date, store_id, banner, region, item_id, description, dept, category, unit_of_measure, unit_cost, units_sold, net_sales)
monthly_item_store(month, store_id, banner, region, item_id, description, dept, category, unit_of_measure, unit_cost, shipped_units, units_sold, net_sales, unit_shrink, shrink_cost)
'''

SYSTEM = f'''You are FreshFlow's Meridian analytics query planner.
{BUSINESS_CONTEXT}
{SCHEMA}

Return ONLY valid JSON with this shape:
{{
  "status": "query" | "clarify" | "unsupported",
  "message": "brief message; empty when status=query",
  "sql": "one read-only SQLite SELECT/WITH query; empty otherwise",
  "assumptions": ["..."],
  "metric_definition": "...",
  "sources": ["table/view names"]
}}

SQL rules:
- Only SELECT or WITH queries.
- Never use INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/PRAGMA/ATTACH.
- Prefer monthly_item_store for monthly shrink questions.
- Default shrink scope to fresh departments: Produce,Dairy,Meat,Bakery,Deli, and state that assumption.
- If the user asks "is shrink up/down" or similar without units vs cost, status=clarify and ask whether they mean unit shrink or shrink cost.
- Do not sum units across LB and EA without grouping by unit_of_measure.
- Use ROUND for human-readable numeric outputs.
- Limit detail queries to at most 50 rows unless the user explicitly asks otherwise.
'''


def _client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def plan(question: str) -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY before asking natural-language questions.")
    resp = _client().responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
        ],
    )
    text = resp.output_text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I|re.S)
    return json.loads(text)


def explain(question: str, plan: dict, columns: list[str], rows: list[tuple]) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return ""
    payload = {
        "question": question,
        "metric_definition": plan.get("metric_definition"),
        "assumptions": plan.get("assumptions", []),
        "columns": columns,
        "rows": rows[:50],
    }
    prompt = f'''Explain this SQLite result to a Meridian merchandising/ops user in 2-4 concise sentences.
Do not add numbers that are not present in the result. Mention important assumptions or unit scope.
If the result is empty, say no matching rows were found.
JSON evidence:\n{json.dumps(payload, default=str)}'''
    resp = _client().responses.create(model=MODEL, input=prompt)
    return resp.output_text.strip()
