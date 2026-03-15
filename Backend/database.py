import os
import sqlite3
import aiosqlite

DB_path = os.path.join(os.path.dirname(__file__), "price_tool.db")

# Full sku_mdgm_master columns for details and admin (single source of truth).
# Note: floor_price_eur exists in the DB schema as a legacy column but is not exposed via APIs.
MDGM_COLS = (
    "id, country, region, therapeutic_area, brand, global_product_name, local_product_name, sku_id,"
    " pu, measure, dimension, volume_of_container, container, strength, currency, erp_applicable, pack_size,"
    " reimbursement_price_local, reimbursement_price_eur, reimbursement_status, reimbursement_rate,"
    " marketed_status, channel, price_type, last_pricing_update, current_price_eur"
)


async def get_connection():
    """Return an aiosqlite connection. Caller must await conn.close() when done."""
    return await aiosqlite.connect(DB_path)


async def log_audit(
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    brand: str | None = None,
    country: str | None = None,
    details: str | None = None,
    sku_ids: list[str] | None = None,
):
    """Append row(s) to audit_log. Pass sku_ids to store one row per SKU (so we can retrieve by sku_id). If sku_ids is None or empty, one row with sku_id NULL."""
    ids = sku_ids or []
    conn = await get_connection()
    try:
        if not ids:
            await conn.execute(
                """INSERT INTO audit_log (user_id, action, entity_type, entity_id, brand, country, details, sku_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, action, entity_type, entity_id, brand, country, details, None),
            )
        else:
            for sku_id in ids:
                await conn.execute(
                    """INSERT INTO audit_log (user_id, action, entity_type, entity_id, brand, country, details, sku_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, action, entity_type, entity_id, brand, country, details, sku_id),
                )
        await conn.commit()
    finally:
        await conn.close()


async def ensure_system_groups():
    """Create one system group chat with all users."""
    conn = await get_connection()
    try:
        async with conn.execute("SELECT id FROM users") as cur:
            rows = await cur.fetchall()
        user_ids = [r[0] for r in rows]
        if not user_ids:
            return

        async with conn.execute("SELECT id FROM chats WHERE type = 'group' AND name = 'All'") as cur:
            existing = await cur.fetchone()
        if existing:
            chat_id = existing[0]
            await conn.execute("DELETE FROM chat_participants WHERE chat_id = ?", (chat_id,))
        else:
            await conn.execute("INSERT INTO chats (type, name) VALUES ('group', 'All')")
            async with conn.execute("SELECT last_insert_rowid()") as cur:
                chat_id = (await cur.fetchone())[0]

        for uid in user_ids:
            await conn.execute(
                "INSERT OR IGNORE INTO chat_participants (chat_id, user_id) VALUES (?, ?)",
                (chat_id, uid),
            )
        await conn.commit()
    finally:
        await conn.close()


async def init_db():
    conn = await get_connection()
    conn.row_factory = sqlite3.Row
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                region TEXT
            );
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL CHECK(role IN('Local', 'Regional', 'Global', 'Admin')),
        therapeutic_area TEXT,
        region TEXT
        );
        """)
        async with conn.execute("PRAGMA table_info(users)") as cur:
            user_cols = [row[1] for row in await cur.fetchall()]
        if "region" not in user_cols:
            await conn.execute("ALTER TABLE users ADD COLUMN region TEXT")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pcrs (
                pcr_id_display TEXT PRIMARY KEY,
                product_id TEXT,
                product_name TEXT,
                submitted_by INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'submitted',
                local_approved_by INTEGER,
                regional_approved_by INTEGER,
                current_price TEXT,
                proposed_price TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                country TEXT,
                therapeutic_area TEXT,
                product_skus TEXT,
                submission_attachments TEXT,
                price_change_type TEXT,
                expected_response_date TEXT,
                price_change_reason TEXT,
                price_change_reason_comments TEXT,
                submission_context TEXT,
                proposed_percent TEXT,
                effective_date TEXT,
                finalized_at TEXT,
                is_discontinue_price INTEGER DEFAULT 0,
                published INTEGER DEFAULT 0,
                channel TEXT NOT NULL DEFAULT 'Retail',
                price_type TEXT,
                floor_price TEXT,
                escalated_by INTEGER,
                escalated_at TEXT,
                global_approved_by INTEGER,
                regional_approved_price_eur REAL,
                global_approved_price_eur REAL,
                FOREIGN KEY (submitted_by) REFERENCES users(id),
                FOREIGN KEY (local_approved_by) REFERENCES users(id),
                FOREIGN KEY (regional_approved_by) REFERENCES users(id),
                FOREIGN KEY (escalated_by) REFERENCES users(id),
                FOREIGN KEY (global_approved_by) REFERENCES users(id)
            );
        """)
        # Ensure new approval reference price and attachment columns exist on existing databases
        async with conn.execute("PRAGMA table_info(pcrs)") as cur:
            pcr_cols = [row[1] for row in await cur.fetchall()]
        if "regional_approved_price_eur" not in pcr_cols:
            await conn.execute("ALTER TABLE pcrs ADD COLUMN regional_approved_price_eur REAL")
        if "global_approved_price_eur" not in pcr_cols:
            await conn.execute("ALTER TABLE pcrs ADD COLUMN global_approved_price_eur REAL")
        # Submission attachments (Local -> Regional): optional, stored as comma-separated presigned URLs.
        if "submission_attachments" not in pcr_cols:
            await conn.execute("ALTER TABLE pcrs ADD COLUMN submission_attachments TEXT")
        # Escalation metadata (Regional -> Global). Stored as comma-separated attachment references and optional comments.
        if "escalation_attachments" not in pcr_cols:
            await conn.execute("ALTER TABLE pcrs ADD COLUMN escalation_attachments TEXT")
        if "escalation_comments" not in pcr_cols:
            await conn.execute("ALTER TABLE pcrs ADD COLUMN escalation_comments TEXT")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sku_channel_prices (
                sku_id TEXT NOT NULL,
                country TEXT NOT NULL,
                therapeutic_area TEXT NOT NULL,
                channel TEXT NOT NULL,
                price_type TEXT NOT NULL,
                floor_price_eur REAL,
                current_price_eur REAL,
                effective_from TEXT,
                pcr_id TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (sku_id, country, therapeutic_area, channel, price_type)
            );
        """)
        async with conn.execute("PRAGMA table_info(sku_channel_prices)") as cur:
            scp_cols = [row[1] for row in await cur.fetchall()]
        if "current_price_eur" not in scp_cols:
            await conn.execute("ALTER TABLE sku_channel_prices ADD COLUMN current_price_eur REAL")
        if "effective_from" not in scp_cols:
            await conn.execute("ALTER TABLE sku_channel_prices ADD COLUMN effective_from TEXT")
        if "pcr_id" not in scp_cols:
            await conn.execute("ALTER TABLE sku_channel_prices ADD COLUMN pcr_id TEXT")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sku_price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku_id TEXT NOT NULL,
                country TEXT NOT NULL,
                therapeutic_area TEXT NOT NULL,
                channel TEXT NOT NULL,
                price_type TEXT,
                price_eur REAL NOT NULL,
                floor_price_eur REAL,
                effective_from DATE NOT NULL,
                pcr_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pcr_id) REFERENCES pcrs(pcr_id_display)
            );
        """)
        async with conn.execute("PRAGMA table_info(sku_price_history)") as cur:
            cols = [row[1] for row in await cur.fetchall()]
        if "floor_price_eur" not in cols:
            await conn.execute("ALTER TABLE sku_price_history ADD COLUMN floor_price_eur REAL")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pcr_id TEXT,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                is_read INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pcr_escalation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pcr_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                proposed_list_price TEXT,
                list_floor TEXT,
                escalation TEXT,
                FOREIGN KEY (pcr_id) REFERENCES pcrs(pcr_id_display) ON DELETE CASCADE
            );
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('direct', 'group')),
            name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_participants (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (chat_id, user_id),
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES users(id)
        );
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            brand TEXT,
            country TEXT,
            details TEXT,
            sku_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        async with conn.execute("PRAGMA table_info(audit_log)") as cur:
            audit_cols = [row[1] for row in await cur.fetchall()]
        if "sku_id" not in audit_cols:
            await conn.execute("ALTER TABLE audit_log ADD COLUMN sku_id TEXT")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS sku_mdgm_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            region TEXT,
            therapeutic_area TEXT NOT NULL,
            brand TEXT NOT NULL,
            global_product_name TEXT,
            local_product_name TEXT,
            sku_id TEXT NOT NULL,
            pu INTEGER,
            measure TEXT,
            dimension TEXT,
            volume_of_container TEXT,
            container TEXT,
            strength TEXT,
            currency TEXT,
            erp_applicable TEXT,
            pack_size INTEGER,
            reimbursement_price_local REAL,
            reimbursement_price_eur REAL,
            reimbursement_status TEXT,
            reimbursement_rate REAL,
            marketed_status TEXT,
            channel TEXT NOT NULL DEFAULT 'Retail',
            price_type TEXT,
            floor_price_eur REAL,
            last_pricing_update DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sku_id, country, channel, price_type)
        );
        """)
        # Ensure floor_price_eur, price_type, and current_price_eur exist on existing databases
        async with conn.execute("PRAGMA table_info(sku_mdgm_master)") as cur:
            mdgm_cols = [row[1] for row in await cur.fetchall()]
        if "floor_price_eur" not in mdgm_cols:
            await conn.execute("ALTER TABLE sku_mdgm_master ADD COLUMN floor_price_eur REAL")
        if "price_type" not in mdgm_cols:
            await conn.execute("ALTER TABLE sku_mdgm_master ADD COLUMN price_type TEXT")
        if "current_price_eur" not in mdgm_cols:
            await conn.execute("ALTER TABLE sku_mdgm_master ADD COLUMN current_price_eur REAL")
        async with conn.execute("SELECT COUNT(*) FROM regions") as cur:
            if (await cur.fetchone())[0] == 0:
                await conn.execute(
                    "INSERT INTO regions (code, name) VALUES (?, ?), (?, ?)",
                    ("EMEA", "EMEA", "APAC", "APAC"),
                )
        async with conn.execute("SELECT COUNT(*) FROM countries") as cur:
            if (await cur.fetchone())[0] == 0:
                await conn.execute(
                    "INSERT INTO countries (code, name, region) VALUES (?, ?, ?), (?, ?, ?), (?, ?, ?), (?, ?, ?)",
                    ("IN", "India", "APAC", "JP", "Japan", "APAC", "AL", "Albania", "EMEA", "BA", "Bosnia and Herzegovina", "EMEA"),
                )
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_countries (
                user_id INTEGER NOT NULL,
                country TEXT NOT NULL,
                PRIMARY KEY (user_id, country),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (country) REFERENCES countries(code)
            );
            """)
        async with conn.execute("SELECT COUNT(*) FROM users") as cur:
            count = (await cur.fetchone())[0]
        if count == 0:
            await conn.executescript("""
                INSERT INTO users (name, email, role, therapeutic_area, region) VALUES
                    ('Vishal', 'vishal@gmail.com', 'Local', 'CMC', 'APAC'),
                    ('Rajesh', 'rajesh@gmail.com', 'Local', 'CMC', 'APAC'),
                    ('Rati', 'rati@gmail.com', 'Regional', 'CMC', 'APAC'),
                    ('Ramya', 'ramya@gmail.com', 'Regional', 'Oncology', 'APAC'),
                    ('Michael', 'micheal@gmail.com', 'Global', NULL, NULL),
                    ('Sarah', 'sarah@gmail.com', 'Admin', NULL, NULL);
                INSERT INTO user_countries (user_id, country)
                SELECT id, 'IN' FROM users WHERE email IN ('vishal@gmail.com', 'rajesh@gmail.com');
                INSERT INTO user_countries (user_id, country)
                SELECT id, 'JP' FROM users WHERE email = 'vishal@gmail.com';
            """)
            print("Added 6 users (Local, Regional, Global, Admin) and user_countries for Local (Vishal: IN, JP; Rajesh: IN)")
        await conn.commit()
    finally:
        await conn.close()
    await ensure_system_groups()


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    print("Database Ready")
