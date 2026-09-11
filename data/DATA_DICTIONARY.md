# Meridian Markets — 90-day extract

A 10-store pilot slice of Meridian Markets, 2026-04-01 through 2026-06-30.
Three files. Everything joins on `item_id` and `store_id`.

| File | Rows | Grain |
|---|---:|---|
| `items.csv` | 200 | one row per item |
| `shipments.csv` | 42,550 | one row per store-item-shipment |
| `sales_daily.csv` | 181,124 | one row per store-item-day with movement |

## items.csv

| Column | Type | Notes |
|---|---|---|
| `item_id` | int | Primary key. Joins to both fact files. |
| `description` | text | Item name as merchandising refers to it. |
| `dept` | text | Produce, Dairy, Meat, Bakery, Deli, Grocery. |
| `category` | text | Sub-grouping within a department. |
| `unit_of_measure` | text | `LB` or `EA`. The unit that `units_sold` is counted in. |
| `case_size` | int | Units per case. Units received = cases_received × case_size. |
| `unit_cost` | decimal | Meridian's cost per unit, in dollars. Stable over the window. |

## shipments.csv

| Column | Type | Notes |
|---|---|---|
| `date` | date | Date the shipment arrived at the store. |
| `store_id` | int | 101–110. |
| `banner` | text | Meridian Foods or GreenLeaf. |
| `region` | text | Northeast, Midwest, or West. |
| `item_id` | int | Joins to items.csv. |
| `cases_received` | int | Cases, not units. |

## sales_daily.csv

| Column | Type | Notes |
|---|---|---|
| `date` | date | Date of sale. |
| `store_id` | int | 101–110. |
| `banner` | text | Denormalized from the store. |
| `region` | text | Denormalized from the store. |
| `item_id` | int | Joins to items.csv. |
| `units_sold` | int | Units, in the item's unit_of_measure. |
| `net_sales` | decimal | Retail dollars for that store-item-day. |

Store-item-days with no movement are absent rather than zero-filled.

## Meridian shrink definition

There is no shrink table.

- **shipped_units** = `cases_received × case_size`
- **unit_shrink** = `shipped_units − units_sold`
- **shrink_cost** = `unit_shrink × unit_cost`

Two ambiguities matter:

1. **Units vs cost** — "Is shrink up?" can produce different answers depending on whether the user means unit shrink or shrink cost.
2. **Scope** — ops defaults shrink to the five fresh departments (Produce, Dairy, Meat, Bakery, Deli). Grocery is excluded unless explicitly requested because shipped-minus-sold there is typically inventory build rather than waste.

The prototype surfaces these assumptions rather than silently choosing a misleading interpretation.
