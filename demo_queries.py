from db import init_db, query, data_quality_summary

init_db()
print("DATA QUALITY", data_quality_summary())

queries = {
"June fresh shrink cost": """
SELECT ROUND(SUM(shrink_cost),2) AS shrink_cost
FROM monthly_item_store
WHERE month='2026-06' AND dept IN ('Produce','Dairy','Meat','Bakery','Deli')
""",
"Top 10 fresh items by June shrink cost": """
SELECT item_id, description, dept, unit_of_measure,
       ROUND(SUM(shrink_cost),2) AS shrink_cost
FROM monthly_item_store
WHERE month='2026-06' AND dept IN ('Produce','Dairy','Meat','Bakery','Deli')
GROUP BY item_id, description, dept, unit_of_measure
ORDER BY shrink_cost DESC
LIMIT 10
""",
"Worst stores by June shrink cost": """
SELECT store_id, banner, region, ROUND(SUM(shrink_cost),2) AS shrink_cost
FROM monthly_item_store
WHERE month='2026-06' AND dept IN ('Produce','Dairy','Meat','Bakery','Deli')
GROUP BY store_id, banner, region
ORDER BY shrink_cost DESC
""",
"Strawberry sales trend": """
SELECT substr(s.date,1,7) AS month, i.description, i.unit_of_measure,
       SUM(s.units_sold) AS units_sold, ROUND(SUM(s.net_sales),2) AS net_sales
FROM sales_daily s JOIN items i ON i.item_id=s.item_id
WHERE lower(i.description) LIKE '%strawber%'
GROUP BY 1,2,3 ORDER BY 1,2
""",
}

for name, sql in queries.items():
    print("\n==", name, "==")
    cols, rows = query(sql)
    print(cols)
    for r in rows[:20]:
        print(r)
