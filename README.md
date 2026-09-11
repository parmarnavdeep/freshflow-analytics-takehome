# FreshFlow Analytics — Meridian prototype

A trust-first natural-language analytics prototype for the Meridian Markets 90-day extract.

## Architecture

`Question → OpenAI query planner → SQL guardrails → SQLite → deterministic result → OpenAI explanation`

The LLM interprets and explains. SQLite calculates every numeric answer.

## Run

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export OPENAI_API_KEY="..."            # Windows PowerShell: $env:OPENAI_API_KEY="..."
streamlit run app.py
```

Optional model override:

```bash
export OPENAI_MODEL="gpt-5.6-luna"
```

Place the assignment's `items.csv`, `shipments.csv`, and `sales_daily.csv` files under `data/`.
`freshflow.db` is created automatically on first run.

> The assignment CSV extracts are intentionally not committed. The repository contains the application code and data dictionary; use the provided assignment extracts locally.

## Trust decisions

- Meridian shrink definition: `shipped units - sold units`.
- Shipment cases are converted with authoritative `case_size`.
- Shrink defaults to fresh departments only (Produce, Dairy, Meat, Bakery, Deli).
- Unit and cost shrink remain distinct metrics.
- LB and EA quantities are not silently aggregated into one comparable unit number.
- SQL is read-only and validated before execution.
- UI exposes metric definition, assumptions, sources, result rows, and generated SQL.
- Ambiguous "is shrink up/down?" questions trigger clarification: units or cost?

## Deliberate cuts for the 2-hour scope

- No authentication/authorization.
- No conversation memory or follow-up context.
- No vector DB/RAG; all source data is structured and local.
- No production deployment/observability.
- SQL validation is prototype-grade, not a full parser/sandbox.
- No formal semantic-metric service; business rules live in code/prompt.

## Best demo flow

1. `What was our total shrink cost in June?`
2. `What were the top 10 fresh items by shrink cost in June?`
3. `How did strawberry sales trend over the three months?`
4. `Is shrink up or down versus May?` → should ask units vs cost.
5. Inspect SQL + assumptions after a successful answer.

## Next production step

Move Meridian metric definitions into a governed semantic layer with versioned metrics, row-level access control, query audit/provenance, and regression tests for canonical business questions.
