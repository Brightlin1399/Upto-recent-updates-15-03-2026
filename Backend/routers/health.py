from fastapi import APIRouter
import database

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    print("[GET /api/health] Health check called")
    return {"status": "ok", "message": "Backend is running"}


@router.get("/debug/sku-no-history")
async def debug_sku_no_history():
    """Check if SKU-NO-HISTORY exists in the API's DB (for 404 debugging)."""
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT sku_id, country, channel, price_type, current_price_eur FROM sku_mdgm_master WHERE sku_id = ?",
            ("SKU-NO-HISTORY",),
        ) as cur:
            rows = await cur.fetchall()
        return {
            "db_path": database.DB_path,
            "row_count": len(rows),
            "rows": [{"sku_id": r[0], "country": r[1], "channel": r[2], "price_type": r[3], "current_price_eur": r[4]} for r in rows],
        }
    finally:
        await conn.close()
