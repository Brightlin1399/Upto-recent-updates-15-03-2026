from fastapi import APIRouter, HTTPException, Header
router = APIRouter()
import database
from models import DirectChatCreate, SendMessageRequest
from helpers.chat_helpers import _get_or_create_direct_chat, _chat_is_participant

@router.post("/chats/direct", status_code=201)
async def create_direct_chat(request: DirectChatCreate, x_user_id: int = Header(..., alias="X-User-Id")):
    try:
        chat_id = await _get_or_create_direct_chat(x_user_id, request.user_id)
        if chat_id is None:
            raise HTTPException(status_code=400, detail="Cannot chat with yourself")
        return {"chat_id": chat_id, "type": "direct", "participant_ids": [x_user_id, request.user_id]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats")
async def list_my_chats(x_user_id: int = Header(..., alias="X-User-Id")):
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            """
            SELECT c.id AS chat_id, c.type, c.name, c.created_at
            FROM chats c
            JOIN chat_participants p ON p.chat_id = c.id
            WHERE p.user_id = ?
            ORDER BY c.type = 'group' DESC, c.created_at DESC
        """,
            (x_user_id,),
        ) as cur:
            rows = await cur.fetchall()
        chats = []
        for r in rows:
            ch = dict(r)
            async with conn.execute("SELECT user_id FROM chat_participants WHERE chat_id = ?", (ch["chat_id"],)) as cur2:
                parts = await cur2.fetchall()
            ch["participant_ids"] = [p["user_id"] for p in parts]
            chats.append(ch)
        return {"chats": chats}
    finally:
        await conn.close()


@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: int, x_user_id: int = Header(..., alias="X-User-Id")):
    if not await _chat_is_participant(chat_id, x_user_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            """
            SELECT m.id, m.chat_id, m.sender_id, m.body, m.created_at
            FROM messages m WHERE m.chat_id = ? ORDER BY m.created_at ASC
        """,
            (chat_id,),
        ) as cur:
            messages = await cur.fetchall()
        return {"messages": [dict(m) for m in messages]}
    finally:
        await conn.close()


@router.post("/chats/{chat_id}/messages", status_code=201)
async def send_chat_message(chat_id: int, request: SendMessageRequest, x_user_id: int = Header(..., alias="X-User-Id")):
    if not await _chat_is_participant(chat_id, x_user_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    conn = await database.get_connection()
    try:
        await conn.execute("INSERT INTO messages (chat_id, sender_id, body) VALUES (?, ?, ?)", (chat_id, x_user_id, request.body))
        await conn.commit()
        async with conn.execute("SELECT last_insert_rowid()") as cur:
            msg_id = (await cur.fetchone())[0]
        return {"id": msg_id, "chat_id": chat_id, "sender_id": x_user_id, "body": request.body}
    finally:
        await conn.close()

