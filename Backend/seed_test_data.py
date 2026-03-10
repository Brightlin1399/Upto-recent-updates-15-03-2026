"""
Seed all tables needed for testing: regions, countries, users,
MDGM (sku_mdgm_master), price history, and sample PCRs. Safe to run multiple times (INSERT OR IGNORE / REPLACE).
Run from Backend folder: python seed_test_data.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database
from seed_data_mdgm import REGIONS, COUNTRIES, MDGM_ROWS


async def seed():
    await database.init_db()
    conn = await database.get_connection()
    try:
        # 1) Regions
        for code, name in REGIONS:
            await conn.execute("INSERT OR IGNORE INTO regions (code, name) VALUES (?, ?)", (code, name))

        # 2) Countries
        for code, name, region in COUNTRIES:
            await conn.execute(
                "INSERT OR IGNORE INTO countries (code, name, region) VALUES (?, ?, ?)",
                (code, name, region),
            )

        # 3) Users: Local, Regional, Global, Admin
        for name, email, role, country, ta, region in [
            ("Vishal", "vishal@gmail.com", "Local", "IN", "CMC", "APAC"),
            ("Rajesh", "rajesh@gmail.com", "Local", "IN", "CMC", "APAC"),
            ("Rati", "rati@gmail.com", "Regional", "IN", "CMC", "APAC"),
            ("Ramya", "ramya@gmail.com", "Regional", "JP", "Oncology", "APAC"),
            ("Michael", "micheal@gmail.com", "Global", None, None, None),
            ("Sarah", "sarah@gmail.com", "Admin", None, None, None),
        ]:
            await conn.execute(
                "INSERT OR IGNORE INTO users (name, email, role, country, therapeutic_area, region) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, role, country, ta, region),
            )

        # 4) MDGM: ~100 rows with region, marketed_status, currency
        for row in MDGM_ROWS:
            (sku_id, country, region, therapeutic_area, brand, channel, price_type, current_price_eur, marketed_status, currency) = row
            await conn.execute(
                """INSERT OR REPLACE INTO sku_mdgm_master
                   (sku_id, country, region, therapeutic_area, brand, channel, price_type, current_price_eur, marketed_status, currency)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sku_id, country, region, therapeutic_area, brand, channel, price_type, current_price_eur, marketed_status, currency),
            )

        # 5) Price history (subset for key SKUs; do NOT add SKU-NO-HISTORY)
        for sku_id, country, ta, ch, pt, price in [
            ("SKU-001", "IN", "CMC", "Retail", "NSP Minimum", 100.0),
            ("SKU-002", "IN", "CMC", "Retail", "NSP Minimum", 98.0),
            ("SKU-IN-001", "IN", "CMC", "Retail", "NSP Minimum", 105.0),
            ("SKU-001", "IN", "CMC", "Retail", "List Price", 2.11),
            ("SKU-002", "IN", "CMC", "Retail", "List Price", 2.05),
            ("SKU-IN-001", "IN", "CMC", "Retail", "List Price", 2.20),
        ]:
            await conn.execute(
                "INSERT INTO sku_price_history (sku_id, country, therapeutic_area, channel, price_type, price_eur, effective_from) VALUES (?, ?, ?, ?, ?, ?, date('now'))",
                (sku_id, country, ta, ch, pt, price),
            )

        # 6) Sample PCRs
        async with conn.execute("SELECT id FROM users WHERE email = 'vishal@gmail.com' LIMIT 1") as cur:
            row = await cur.fetchone()
        if row:
            uid = row[0]
            await conn.execute(
                """INSERT OR REPLACE INTO pcrs (pcr_id_display, product_name, submitted_by, status, country, therapeutic_area, product_skus, proposed_price, current_price, floor_price, channel, price_type)
                   VALUES ('PCR-TEST-001', 'EUTHYROX', ?, 'draft', 'IN', 'CMC', 'SKU-001,SKU-002', '110', '100', NULL, 'Retail', 'NSP Minimum')""",
                (uid,),
            )
            await conn.execute(
                """INSERT OR REPLACE INTO pcrs (pcr_id_display, product_name, submitted_by, status, country, therapeutic_area, product_skus, proposed_price, current_price, floor_price, channel, price_type)
                   VALUES ('PCR-TEST-002', 'EUTHYROX', ?, 'local_approved', 'IN', 'CMC', 'SKU-001', '108', '100', NULL, 'Retail', 'NSP Minimum')""",
                (uid,),
            )

        await conn.commit()

        # Verify
        async with conn.execute("SELECT COUNT(*) FROM sku_mdgm_master") as cur:
            n_mdgm = (await cur.fetchone())[0]
        async with conn.execute(
            "SELECT sku_id, country, therapeutic_area, channel, price_type, current_price_eur FROM sku_mdgm_master WHERE sku_id = 'SKU-NO-HISTORY'"
        ) as cur:
            no_hist = await cur.fetchall()
        db_path = os.path.abspath(database.DB_path)
        print("Seed done: regions, countries, users, MDGM (current), history, sample PCRs.")
        print(f"  Database file: {db_path}")
        print(f"  sku_mdgm_master rows: {n_mdgm}")
        if no_hist:
            print(f"  SKU-NO-HISTORY in MDGM: {no_hist[0]}")
        else:
            print("  WARNING: SKU-NO-HISTORY not in sku_mdgm_master.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
