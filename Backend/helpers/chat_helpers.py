import database
async def _get_or_create_direct_chat(user_id_1: int, user_id_2: int):
    """Get existing direct chat between two users, or create new one."""
    if user_id_1 == user_id_2:
        return None
    conn = await database.get_connection()
    try:
        a, b = min(user_id_1, user_id_2), max(user_id_1, user_id_2)
        async with conn.execute(
            """
            SELECT c.id FROM chats c
            JOIN chat_participants p1 ON p1.chat_id = c.id AND p1.user_id = ?
            JOIN chat_participants p2 ON p2.chat_id = c.id AND p2.user_id = ?
            WHERE c.type = 'direct'
        """,
            (a, b),
        ) as cur:
            row = await cur.fetchone()
        if row:
            return row[0]
        await conn.execute("INSERT INTO chats (type) VALUES ('direct')")
        async with conn.execute("SELECT last_insert_rowid()") as cur:
            chat_id = (await cur.fetchone())[0]
        await conn.execute(
            "INSERT INTO chat_participants (chat_id, user_id) VALUES (?, ?), (?, ?)",
            (chat_id, user_id_1, chat_id, user_id_2),
        )
        await conn.commit()
        return chat_id
    finally:
        await conn.close()


async def _chat_is_participant(chat_id: int, user_id: int) -> bool:
    """Check if user is a participant in the chat."""
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT 1 FROM chat_participants WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        ) as cur:
            r = await cur.fetchone()
        return r is not None
    finally:
        await conn.close()
