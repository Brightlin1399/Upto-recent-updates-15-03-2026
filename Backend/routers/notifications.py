from fastapi import APIRouter, Path
router = APIRouter()
import database

@router.get("/users/{user_id}/notifications")
async def get_user_notifications(user_id: int = Path(...)):
    """Get notifications for a user"""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT n.*, p.product_name, p.status as pcr_status, p.pcr_id_display
            FROM notifications n
            LEFT JOIN pcrs p ON n.pcr_id = p.pcr_id_display
            WHERE n.user_id = ?
            ORDER BY n.created_at DESC
            LIMIT 50
        """, (user_id,)) as cur:
            notifications = await cur.fetchall()
        # For admin/MDGM notifications, pcr_id is NULL so p.* columns are NULL
        return {"notifications": [dict(row) for row in notifications]}
    finally:
        await conn.close()


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int = Path(...)):
    """Mark a notification as read"""
    conn = await database.get_connection()
    try:
        await conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        await conn.commit()
        return {"message": "Notification marked as read"}
    finally:
        await conn.close()


@router.put("/users/{user_id}/notifications/read-all")
async def mark_all_notifications_read(user_id: int = Path(...)):
    """Mark all notifications as read for a user"""
    conn = await database.get_connection()
    try:
        await conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        await conn.commit()
        return {"message": "All notifications marked as read"}
    finally:
        await conn.close()
