FRESH_DEPTS = ("Produce", "Dairy", "Meat", "Bakery", "Deli")

BUSINESS_CONTEXT = r'''
Meridian Markets pilot data covers 10 stores (101-110) from 2026-04-01 through 2026-06-30.

Authoritative business definitions:
- shipped_units = shipments.cases_received * items.case_size
- unit_shrink = shipped_units - units_sold
- shrink_cost = unit_shrink * items.unit_cost
- Ops team's default shrink scope = fresh departments only: Produce, Dairy, Meat, Bakery, Deli.
- Grocery is excluded by default because shipped-minus-sold there is usually inventory build, not waste.
- unit_of_measure is LB or EA. Never aggregate LB and EA unit quantities into one comparable unit total unless results are grouped by unit_of_measure.
- Store-item-days with no sales movement are absent from sales_daily rather than explicitly zero-filled.

Ambiguities that must be surfaced:
1) "Is shrink up?" may mean unit shrink or shrink cost. Ask for clarification if the question does not specify and the distinction affects the answer.
2) "Shrink" defaults to fresh departments only, but a user may explicitly request all departments.

Trust rules:
- Numbers must come from SQLite query results; never invent or mentally calculate them.
- Use net_sales for retail sales dollars.
- Do not call shipment-minus-sales "inventory" or "on-hand"; the extract contains no inventory snapshots, transfers, or adjustments.
- Prefer explicit date ranges and filters in answers.
'''
