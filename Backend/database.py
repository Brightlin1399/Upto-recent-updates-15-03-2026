import os
import sqlite3
import aiosqlite

DB_path = os.path.join(os.path.dirname(__file__), "price_tool.db")

# Full sku_mdgm_master columns for details and admin (single source of truth).
# Note: floor_price_eur exists in the DB schema as a legacy column but is not exposed via APIs.
MDGM_COLS = (
    "id, country, region, therapeutic_area, brand, global_product_name, local_product_name, sku_id,"
    " pu, measure, dimension, volume_of_container, container, strength, currency, erp_applicable, pack_size,"
    " reimbursement_price_local, reimbursement_price_eur, reimbursement_status, reimbursement_type, reimbursement_rate, vat_rate,"
    " marketed_status, channel, price_type, last_pricing_update, current_price_eur"
)


async def get_connection():
    """Return an aiosqlite connection. Caller must await conn.close() when done."""
    return await aiosqlite.connect(DB_path)


def _split_csv(value: str | None, *, upper: bool = False) -> list[str]:
    """Split comma-separated values into a normalized, de-duplicated list."""
    if not value or not isinstance(value, str):
        return []
    parts = [p.strip() for p in value.split(",")]
    parts = [p for p in parts if p]
    if upper:
        parts = [p.upper() for p in parts]
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


async def sync_user_mappings_from_users(conn: aiosqlite.Connection) -> None:
    """Sync user_countries and user_therapeutic_areas from users.{countries, therapeutic_areas}.

    Intended usage: call after tables exist. Safe to run on each startup.
    """
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    async with conn.execute(
        "SELECT id, countries, therapeutic_areas FROM users"
    ) as cur:
        users = await cur.fetchall()

    for u in users:
        uid = u["id"]
        countries = _split_csv(u.get("countries"), upper=True)
        tas = _split_csv(u.get("therapeutic_areas"), upper=False)

        # Replace per-user mappings to avoid drift if CSV changes
        await conn.execute("DELETE FROM user_countries WHERE user_id = ?", (uid,))
        await conn.execute("DELETE FROM user_therapeutic_areas WHERE user_id = ?", (uid,))

        for c in countries:
            await conn.execute(
                "INSERT OR IGNORE INTO user_countries (user_id, country) VALUES (?, ?)",
                (uid, c),
            )
        for ta in tas:
            await conn.execute(
                "INSERT OR IGNORE INTO user_therapeutic_areas (user_id, therapeutic_area) VALUES (?, ?)",
                (uid, ta),
            )


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
        region TEXT,
        countries TEXT,
        therapeutic_areas TEXT
        );
        """)
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

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sku_price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku_id TEXT NOT NULL,
                country TEXT NOT NULL,
                therapeutic_area TEXT NOT NULL,
                channel TEXT NOT NULL,
                price_type TEXT,
                price_eur REAL NOT NULL,
                effective_from DATE NOT NULL,
                pcr_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pcr_id) REFERENCES pcrs(pcr_id_display)
            );
        """)

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
        # pcr_escalation table removed; escalation is tracked on pcrs (escalated_by, escalation_attachments, etc.)
        await conn.execute("DROP TABLE IF EXISTS pcr_escalation")
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
            reimbursement_type TEXT,
            reimbursement_rate REAL,
            vat_rate REAL,
            marketed_status TEXT,
            channel TEXT NOT NULL DEFAULT 'Retail',
            price_type TEXT,
            last_pricing_update DATETIME DEFAULT CURRENT_TIMESTAMP,
            current_price_eur REAL,
            UNIQUE(sku_id, country, channel, price_type)
        );
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS sku_mdgm_overrides (
            sku_id TEXT NOT NULL,
            country TEXT NOT NULL,
            therapeutic_area TEXT NOT NULL,
            channel TEXT NOT NULL DEFAULT 'Retail',
            price_type TEXT,

            -- editable launched/current price
            current_price_eur REAL,
            effective_from DATE,
            expiration_date DATE,

            -- editable business fields
            marketed_status TEXT,
            reimbursement_price_local REAL,
            reimbursement_price_eur REAL,
            reimbursement_status TEXT,
            reimbursement_type TEXT,
            reimbursement_rate REAL,
            vat_rate REAL,

            -- audit (optional)
            source TEXT,
            source_ref TEXT,
            updated_by INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (sku_id, country, therapeutic_area, channel, price_type)
        );
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sku_mdgm_overrides_lookup
            ON sku_mdgm_overrides (country, therapeutic_area, channel, price_type, sku_id)
        """)
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
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_therapeutic_areas (
                user_id INTEGER NOT NULL,
                therapeutic_area TEXT NOT NULL,
                PRIMARY KEY (user_id, therapeutic_area),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """)
        # Populate mapping tables from users CSV columns (countries, therapeutic_areas)
        await sync_user_mappings_from_users(conn)
        await conn.commit()
    finally:
        await conn.close()
    await ensure_system_groups()


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    print("Database Ready")
