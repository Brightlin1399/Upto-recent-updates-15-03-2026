from fastapi import APIRouter
router = APIRouter()
import database


@router.get("/users")
async def get_users():
    """Get all users with assigned countries (read-only). User creation and country assignment are developers-only."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            "SELECT id, name, email, role, therapeutic_area, region FROM users ORDER BY id"
        ) as cur:
            rows = await cur.fetchall()
        users = [dict(r) for r in rows]
        # Attach assigned countries from user_countries (read-only; assignment is developers-only)
        for u in users:
            async with conn.execute(
                "SELECT country FROM user_countries WHERE user_id = ? ORDER BY country",
                (u["id"],),
            ) as cur:
                countries = await cur.fetchall()
            u["countries"] = [c["country"] for c in countries] if countries else []
        return {"users": users}
    finally:
        await conn.close()

