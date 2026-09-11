from __future__ import annotations
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "freshflow.db"

SCHEMA = {
    "items": """
        CREATE TABLE items (
            item_id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            dept TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_of_measure TEXT NOT NULL,
            case_size INTEGER NOT NULL,
            unit_cost REAL NOT NULL
        )
    """,
    "shipments": """
        CREATE TABLE shipments (
            date TEXT NOT NULL,
            store_id INTEGER NOT NULL,
            banner TEXT NOT NULL,
            region TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            cases_received INTEGER NOT NULL
        )
    """,
    "sales_daily": """
        CREATE TABLE sales_daily (
            date TEXT NOT NULL,
            store_id INTEGER NOT NULL,
            banner TEXT NOT NULL,
            region TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            units_sold INTEGER NOT NULL,
            net_sales REAL NOT NULL
        )
    """,
}


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _load_csv(con: sqlite3.Connection, table: str, filename: str) -> None:
    with open(DATA_DIR / filename, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header, data = rows[0], rows[1:]
    placeholders = ",".join(["?"] * len(header))
    con.executemany(
        f"INSERT INTO {table} ({','.join(header)}) VALUES ({placeholders})", data
    )


def init_db(force: bool = False) -> None:
    if DB_PATH.exists() and not force:
        return
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = connect()
    try:
        for table, ddl in SCHEMA.items():
            con.execute(ddl)
        _load_csv(con, "items", "items.csv")
        _load_csv(con, "shipments", "shipments.csv")
        _load_csv(con, "sales_daily", "sales_daily.csv")
        con.executescript("""
            CREATE INDEX idx_shipments_date_item_store ON shipments(date, item_id, store_id);
            CREATE INDEX idx_sales_date_item_store ON sales_daily(date, item_id, store_id);
            CREATE INDEX idx_items_dept ON items(dept);

            CREATE VIEW shipment_units AS
            SELECT
                sh.date,
                sh.store_id,
                sh.banner,
                sh.region,
                sh.item_id,
                i.description,
                i.dept,
                i.category,
                i.unit_of_measure,
                i.case_size,
                i.unit_cost,
                sh.cases_received,
                sh.cases_received * i.case_size AS shipped_units
            FROM shipments sh
            JOIN items i ON i.item_id = sh.item_id;

            CREATE VIEW sales_enriched AS
            SELECT
                s.date,
                s.store_id,
                s.banner,
                s.region,
                s.item_id,
                i.description,
                i.dept,
                i.category,
                i.unit_of_measure,
                i.unit_cost,
                s.units_sold,
                s.net_sales
            FROM sales_daily s
            JOIN items i ON i.item_id = s.item_id;

            CREATE VIEW monthly_item_store AS
            WITH ship AS (
                SELECT substr(sh.date,1,7) AS month, sh.store_id, sh.banner, sh.region,
                       sh.item_id, SUM(sh.cases_received * i.case_size) AS shipped_units
                FROM shipments sh JOIN items i ON i.item_id = sh.item_id
                GROUP BY 1,2,3,4,5
            ),
            sale AS (
                SELECT substr(date,1,7) AS month, store_id, banner, region, item_id,
                       SUM(units_sold) AS units_sold, SUM(net_sales) AS net_sales
                FROM sales_daily
                GROUP BY 1,2,3,4,5
            )
            SELECT
                COALESCE(ship.month, sale.month) AS month,
                COALESCE(ship.store_id, sale.store_id) AS store_id,
                COALESCE(ship.banner, sale.banner) AS banner,
                COALESCE(ship.region, sale.region) AS region,
                i.item_id,
                i.description,
                i.dept,
                i.category,
                i.unit_of_measure,
                i.unit_cost,
                COALESCE(ship.shipped_units, 0) AS shipped_units,
                COALESCE(sale.units_sold, 0) AS units_sold,
                COALESCE(sale.net_sales, 0) AS net_sales,
                COALESCE(ship.shipped_units, 0) - COALESCE(sale.units_sold, 0) AS unit_shrink,
                (COALESCE(ship.shipped_units, 0) - COALESCE(sale.units_sold, 0)) * i.unit_cost AS shrink_cost
            FROM ship
            LEFT JOIN sale
              ON sale.month=ship.month AND sale.store_id=ship.store_id AND sale.item_id=ship.item_id
            JOIN items i ON i.item_id=ship.item_id
            UNION ALL
            SELECT
                sale.month, sale.store_id, sale.banner, sale.region,
                i.item_id, i.description, i.dept, i.category, i.unit_of_measure, i.unit_cost,
                0 AS shipped_units,
                sale.units_sold,
                sale.net_sales,
                -sale.units_sold AS unit_shrink,
                -sale.units_sold * i.unit_cost AS shrink_cost
            FROM sale
            LEFT JOIN ship
              ON ship.month=sale.month AND ship.store_id=sale.store_id AND ship.item_id=sale.item_id
            JOIN items i ON i.item_id=sale.item_id
            WHERE ship.item_id IS NULL;
        """)
        con.commit()
    finally:
        con.close()


def query(sql: str, params=()):
    init_db()
    con = connect()
    try:
        cur = con.execute(sql, params)
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, [tuple(r) for r in cur.fetchall()]
    finally:
        con.close()


def data_quality_summary() -> dict:
    init_db()
    con = connect()
    try:
        q = {}
        for t in ("items", "shipments", "sales_daily"):
            q[f"{t}_rows"] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        q["date_min"], q["date_max"] = con.execute(
            "SELECT MIN(date), MAX(date) FROM sales_daily"
        ).fetchone()
        q["orphan_shipments"] = con.execute(
            "SELECT COUNT(*) FROM shipments sh LEFT JOIN items i ON i.item_id=sh.item_id WHERE i.item_id IS NULL"
        ).fetchone()[0]
        q["orphan_sales"] = con.execute(
            "SELECT COUNT(*) FROM sales_daily s LEFT JOIN items i ON i.item_id=s.item_id WHERE i.item_id IS NULL"
        ).fetchone()[0]
        q["duplicate_items"] = con.execute(
            "SELECT COUNT(*) FROM (SELECT item_id FROM items GROUP BY item_id HAVING COUNT(*)>1)"
        ).fetchone()[0]
        q["uoms"] = [r[0] for r in con.execute("SELECT DISTINCT unit_of_measure FROM items ORDER BY 1")]
        return q
    finally:
        con.close()
