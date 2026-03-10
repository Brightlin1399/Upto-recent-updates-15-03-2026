from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Path, Body, Header
from fastapi.middleware.cors import CORSMiddleware
import database
import notification_rules

from models import (
    SubmitPCRRequest,
    ApproveRejectRequest,
    UpdatePCRRequest,
    RegionalEditPCRRequest,
    FinalisePCRRequest,
    ResubmitPCRRequest,
    DirectChatCreate,
    SendMessageRequest,
    GroupChatCreate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield


app = FastAPI(title="Price Tool API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


async def _therapeutic_area_for_brand(brand: str) -> str | None:
    """Return therapeutic_area for a brand from brand_therapeutic_area table."""
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT therapeutic_area FROM brand_therapeutic_area WHERE brand = ?",
            (brand,),
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None
    finally:
        await conn.close()


async def _user_can_approve_for_pcr(user_id: int, pcr_id: str) -> bool:
    """Check if user can approve this PCR (same country + therapeutic_area)."""
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT country, therapeutic_area FROM pcrs WHERE pcr_id_display = ?",
            (pcr_id,),
        ) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            return False
        async with conn.execute(
            "SELECT country, therapeutic_area FROM users WHERE id = ?",
            (user_id,),
        ) as cur:
            user = await cur.fetchone()
        if not user:
            return False
        return pcr[0] == user[0] and pcr[1] == user[1]
    finally:
        await conn.close()
def _parse_price(s: str | None) -> float | None:
    """Parse price string like 'EUR 2.11' or '2,11' to float. Returns None if invalid."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip().upper()
    for prefix in ("EUR", "USD", "GBP", "INR"):
        if s.startswith(prefix):
            s = s[len(prefix):].strip()
            break
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None
@app.post("/api/chats/direct", status_code=201)
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


@app.get("/api/chats")
async def list_my_chats(x_user_id: int = Header(..., alias="X-User-Id")):
    await database.ensure_system_groups()
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


@app.get("/api/chats/{chat_id}/messages")
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


@app.post("/api/chats/{chat_id}/messages", status_code=201)
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    print("[GET /api/health] Health check called")
    return {"status": "ok", "message": "Backend is running"}


@app.get("/api/users")
async def get_users():
    """Get all users"""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("SELECT id, name, email, role, country, therapeutic_area FROM users ORDER BY id") as cur:
            users = await cur.fetchall()
        return {"users": [dict(row) for row in users]}
    finally:
        await conn.close()


@app.post("/api/pcrs", status_code=201)
async def submit_pcr(request: SubmitPCRRequest):
    """Submit a new PCR (Country, Brand, SKUs). Local can only create for their country and therapeutic area."""
    try:
        submitted_by = request.submitted_by
        pcr_id_display = request.pcr_id
        country = request.country
        brand = request.brand
        product_skus_str = ",".join(request.product_skus) if request.product_skus else None
        brand_ta = await _therapeutic_area_for_brand(brand)
        if not brand_ta:
            raise HTTPException(status_code=400, detail=f"Unknown brand: {brand}")

        conn = await database.get_connection()
        try:
            async with conn.execute(
                "SELECT role, country, therapeutic_area FROM users WHERE id = ?",
                (submitted_by,),
            ) as cur:
                user = await cur.fetchone()
            if not user:
                raise HTTPException(status_code=400, detail=f"User id {submitted_by} not found")
            if user[0] != "Local":
                raise HTTPException(status_code=400, detail="Only Local users can submit PCRs")
            user_country = user[1]
            user_ta = user[2]
            if country != user_country:
                raise HTTPException(
                    status_code=403,
                    detail=f"You can only create PCRs for your country ({user_country}). Requested: {country}",
                )
            if brand_ta != user_ta:
                raise HTTPException(
                    status_code=403,
                    detail=f"Brand '{brand}' is in therapeutic area '{brand_ta}'. You can only create for your therapeutic area ({user_ta}).",
                )
            await conn.execute(
                """INSERT INTO pcrs (
                    pcr_id_display, product_id, product_name, submitted_by, status,
                    current_price, proposed_price, country, therapeutic_area, product_skus,
                    price_change_type, expected_response_date, price_change_reason,
                    price_change_reason_comments, submission_context, proposed_percent,
                    effective_date, is_discontinue_price
                ) VALUES (?, ?, ?, ?, 'submitted', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pcr_id_display,
                    request.product_id,
                    request.product_name,
                    submitted_by,
                    request.current_price,
                    request.proposed_price,
                    country,
                    brand_ta,
                    product_skus_str,
                    request.price_change_type,
                    request.expected_response_date,
                    request.price_change_reason,
                    request.price_change_reason_comments,
                    request.submission_context,
                    request.proposed_percent,
                    request.effective_date,
                    1 if request.is_discontinue_price else 0,
                ),
            )
            await conn.commit()
        finally:
            await conn.close()

        return {"message": "PCR submitted successfully", "pcr_id": pcr_id_display}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/pcrs/{pcr_id}/regional-approve")
async def regional_approve(pcr_id: str = Path(...), request: ApproveRejectRequest = Body(...)):
    """Approve PCR at Regional level"""
    approved_by = request.approved_by
    if not approved_by:
        raise HTTPException(status_code=400, detail="approved_by is required")
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (approved_by,)) as cur:
            approver = await cur.fetchone()
        if not approver or approver[0] != "Regional":
            raise HTTPException(status_code=400, detail="Only Regional users can approve at Regional level")
        if not await _user_can_approve_for_pcr(approved_by, pcr_id):
            raise HTTPException(status_code=403, detail="You can only approve PCRs for your country and therapeutic area")
        async with conn.execute("SELECT status FROM pcrs WHERE pcr_id_display = ?", (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] != "local_approved":
            raise HTTPException(status_code=400, detail=f"PCR is in '{pcr[0]}' status. Can only approve when status is local_approved.")
        await conn.execute(
            """UPDATE pcrs SET regional_approved_by=?,status='regional_approved' WHERE pcr_id_display=?""",
            (approved_by, pcr_id),
        )
        await conn.commit()
    finally:
        await conn.close()
    await notification_rules.notify_on_regional_approve_reject(pcr_id, "approved")
    return {"message": "PCR approved by Regional", "pcr_id": pcr_id}

@app.put("/api/pcrs/{pcr_id}/regional-reject")
async def regional_reject(pcr_id: str = Path(...), request: ApproveRejectRequest = Body(...)):
    """Reject PCR at Regional level"""
    rejected_by = request.rejected_by
    if not rejected_by:
        raise HTTPException(status_code=400, detail="rejected_by is required")
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (rejected_by,)) as cur:
            approver = await cur.fetchone()
        if not approver or approver[0] != "Regional":
            raise HTTPException(status_code=400, detail="Only Regional users can reject at Regional level")
        if not await _user_can_approve_for_pcr(rejected_by, pcr_id):
            raise HTTPException(status_code=403, detail="You can only reject PCRs for your country and therapeutic area")
        async with conn.execute("SELECT status FROM pcrs WHERE pcr_id_display = ?", (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] != "local_approved":
            raise HTTPException(status_code=400, detail=f"PCR is in '{pcr[0]}' status. Can only reject when status is local_approved.")
        await conn.execute(
            """UPDATE pcrs SET regional_approved_by=?,status='regional_rejected' WHERE pcr_id_display=?""",
            (rejected_by, pcr_id),
        )
        await conn.commit()
    finally:
        await conn.close()
    await notification_rules.notify_on_regional_approve_reject(pcr_id, "rejected")
    return {"message": "PCR rejected by Regional", "pcr_id": pcr_id}

@app.get("/api/pcrs")
async def get_all_pcrs():
    """Get all PCRs"""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT p.*,
                   s.name AS submitter_name, s.email AS submitter_email,
                   la.name AS local_approver_name,
                   ra.name AS regional_approver_name
            FROM pcrs p
            LEFT JOIN users s ON p.submitted_by = s.id
            LEFT JOIN users la ON p.local_approved_by = la.id
            LEFT JOIN users ra ON p.regional_approved_by = ra.id
            ORDER BY p.created_at DESC
        """) as cur:
            pcrs = await cur.fetchall()
        return {"pcrs": [dict(row) for row in pcrs]}
    finally:
        await conn.close()


@app.get("/api/pcrs/{pcr_id}")
async def get_pcr(pcr_id: str = Path(...)):
    """Get a single PCR by display ID"""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT p.*,
                   s.name AS submitter_name, s.email AS submitter_email,
                   la.name AS local_approver_name,
                   ra.name AS regional_approver_name
            FROM pcrs p
            LEFT JOIN users s ON p.submitted_by = s.id
            LEFT JOIN users la ON p.local_approved_by = la.id
            LEFT JOIN users ra ON p.regional_approved_by = ra.id
            WHERE p.pcr_id_display = ?
        """, (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        return dict(pcr)
    finally:
        await conn.close()

@app.put("/api/pcrs/{pcr_id}")
async def update_pcr(pcr_id: str = Path(...), request: UpdatePCRRequest = Body(...)):
    """Update a rejected PCR (Local only, all summary + price fields)."""
    edited_by = request.edited_by
    rejected_cases = ("local_rejected", "regional_rejected")
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT id, role FROM users WHERE id = ?", (edited_by,)) as cur:
            editor = await cur.fetchone()
        if not editor or editor[1] != "Local":
            raise HTTPException(status_code=400, detail="Only Local users can edit PCRs")
        async with conn.execute("SELECT status FROM pcrs WHERE pcr_id_display = ?", (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] not in rejected_cases:
            raise HTTPException(status_code=400, detail=f"Can only edit rejected PCRs. Current status: {pcr[0]}")
        updates = []
        params = []
        if request.pcr_id_display is not None:
            updates.append("pcr_id_display = ?")
            params.append(request.pcr_id_display)
        if request.product_id is not None:
            updates.append("product_id = ?")
            params.append(request.product_id)
        if request.product_name is not None:
            updates.append("product_name = ?")
            params.append(request.product_name)
        if request.current_price is not None:
            updates.append("current_price = ?")
            params.append(request.current_price)
        if request.proposed_price is not None:
            updates.append("proposed_price = ?")
            params.append(request.proposed_price)
        if request.product_skus is not None:
            updates.append("product_skus = ?")
            params.append(request.product_skus)
        if request.price_change_type is not None:
            updates.append("price_change_type = ?")
            params.append(request.price_change_type)
        if request.expected_response_date is not None:
            updates.append("expected_response_date = ?")
            params.append(request.expected_response_date)
        if request.price_change_reason is not None:
            updates.append("price_change_reason = ?")
            params.append(request.price_change_reason)
        if request.price_change_reason_comments is not None:
            updates.append("price_change_reason_comments = ?")
            params.append(request.price_change_reason_comments)
        if request.submission_context is not None:
            updates.append("submission_context = ?")
            params.append(request.submission_context)
        if request.proposed_percent is not None:
            updates.append("proposed_percent = ?")
            params.append(request.proposed_percent)
        if request.is_discontinue_price is not None:
            updates.append("is_discontinue_price = ?")
            params.append(1 if request.is_discontinue_price else 0)
        if request.effective_date is not None:
            updates.append("effective_date = ?")
            params.append(request.effective_date)
        if not updates:
            raise HTTPException(status_code=400, detail="Provide at least one field to update")
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(pcr_id)
        await conn.execute("UPDATE pcrs SET " + ", ".join(updates) + " WHERE pcr_id_display = ?", tuple(params))
        await conn.commit()
        return {"message": "PCR updated", "pcr_id": pcr_id}
    finally:
        await conn.close()

@app.put("/api/pcrs/{pcr_id}/regional-edit")
async def regional_edit_pcr(pcr_id: str = Path(...), request: RegionalEditPCRRequest = Body(...)):
    """Regional edit after approval (cannot change proposed_price / current_price)."""
    edited_by = request.edited_by
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (edited_by,)) as cur:
            editor = await cur.fetchone()
        if not editor or editor[0] != "Regional":
            raise HTTPException(status_code=400, detail="Only Regional users can use regional-edit")
        if not await _user_can_approve_for_pcr(edited_by, pcr_id):
            raise HTTPException(status_code=403, detail="You can only edit PCRs for your country and therapeutic area")
        async with conn.execute("SELECT status FROM pcrs WHERE pcr_id_display = ?", (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] != "regional_approved":
            raise HTTPException(status_code=400, detail="Can only edit when status is regional_approved.")
        updates = []
        params = []
        if request.price_change_type is not None:
            updates.append("price_change_type = ?")
            params.append(request.price_change_type)
        if request.expected_response_date is not None:
            updates.append("expected_response_date = ?")
            params.append(request.expected_response_date)
        if request.price_change_reason is not None:
            updates.append("price_change_reason = ?")
            params.append(request.price_change_reason)
        if request.price_change_reason_comments is not None:
            updates.append("price_change_reason_comments = ?")
            params.append(request.price_change_reason_comments)
        if request.submission_context is not None:
            updates.append("submission_context = ?")
            params.append(request.submission_context)
        if request.product_skus is not None:
            updates.append("product_skus = ?")
            params.append(request.product_skus)
        if request.proposed_percent is not None:
            updates.append("proposed_percent = ?")
            params.append(request.proposed_percent)
        if request.is_discontinue_price is not None:
            updates.append("is_discontinue_price = ?")
            params.append(1 if request.is_discontinue_price else 0)
        if request.effective_date is not None:
            updates.append("effective_date = ?")
            params.append(request.effective_date)
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(pcr_id)
            await conn.execute("UPDATE pcrs SET " + ", ".join(updates) + " WHERE pcr_id_display = ?", tuple(params))
        await conn.commit()
        return {"message": "PCR updated by Regional", "pcr_id": pcr_id}
    finally:
        await conn.close()


@app.put("/api/pcrs/{pcr_id}/finalise")
async def finalise_pcr(pcr_id: str = Path(...), request: FinalisePCRRequest = Body(...)):
    """Finalise a regionally approved PCR. Updates current price for each SKU in the PCR."""
    finalised_by = request.finalised_by
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (finalised_by,)) as cur:
            user = await cur.fetchone()
        if not user or user[0] != "Regional":
            raise HTTPException(status_code=400, detail="Only Regional users can finalise")
        if not await _user_can_approve_for_pcr(finalised_by, pcr_id):
            raise HTTPException(status_code=403, detail="You can only finalise PCRs for your country and therapeutic area")
        async with conn.execute(
            """SELECT status, country, therapeutic_area, channel, product_skus, proposed_price, effective_date FROM pcrs WHERE pcr_id_display = ?""",
            (pcr_id,),
        ) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] != "regional_approved":
            raise HTTPException(status_code=400, detail="Can only finalise when status is regional_approved.")
        await conn.execute(
            "UPDATE pcrs SET finalized_at = CURRENT_TIMESTAMP, status = 'finalised', updated_at = CURRENT_TIMESTAMP WHERE pcr_id_display = ?",
            (pcr_id,),
        )
        country = pcr[1] or ""
        therapeutic_area = pcr[2] or ""
        channel = (pcr[3] or "Retail").strip()
        product_skus_str = (pcr[4] or "").strip()
        proposed_price = pcr[5]
        import datetime
        effective_from = (pcr[6] or datetime.date.today().isoformat())
        price_eur = _parse_price(proposed_price) if proposed_price else None
        if country and therapeutic_area and channel and product_skus_str and price_eur is not None:
            sku_list = [s.strip() for s in product_skus_str.split(",") if s.strip()]
            for sku_id in sku_list:
                await conn.execute(
                    """INSERT INTO sku_price_history (sku_id, country, therapeutic_area, channel, price_eur, effective_from, pcr_id) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (sku_id, country, therapeutic_area, channel, price_eur, effective_from, pcr_id),
                )
        await conn.commit()
        return {"message": "PCR finalised", "pcr_id": pcr_id}
    finally:
        await conn.close()

@app.put("/api/pcrs/{pcr_id}/resubmit")
async def re_submit_pcr(pcr_id: str = Path(...), request: ResubmitPCRRequest = Body(...)):
    """Resubmit a rejected PCR"""
    re_submitted_by = request.re_submitted_by
    rejected_cases = ("local_rejected", "regional_rejected")
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT status FROM pcrs WHERE pcr_id_display=?", (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] not in rejected_cases:
            raise HTTPException(status_code=400, detail=f"Can only re-submit rejected PCRs. Current status: {pcr[0]}")
        async with conn.execute("SELECT id,role FROM users WHERE id=?", (re_submitted_by,)) as cur:
            re_submitter = await cur.fetchone()
        if not re_submitter or re_submitter[1] != "Local":
            raise HTTPException(status_code=400, detail="PCR should be re-submitted by Local users")
        await conn.execute(
            """
            UPDATE pcrs SET status = 'submitted',
                submitted_by = ?, local_approved_by = NULL, regional_approved_by = NULL
            WHERE pcr_id_display = ?
        """,
            (re_submitted_by, pcr_id),
        )
        await conn.commit()
        return {"message": "PCR resubmitted successfully. Status changed to Draft. Click Submit to notify approvers.", "pcr_id": pcr_id}
    finally:
        await conn.close()

@app.get("/api/users/{user_id}/notifications")
async def get_user_notifications(user_id: int = Path(...)):
    """Get notifications for a user"""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT n.*, p.product_name, p.status as pcr_status, p.pcr_id_display
            FROM notifications n
            JOIN pcrs p ON n.pcr_id = p.pcr_id_display
            WHERE n.user_id = ?
            ORDER BY n.created_at DESC
            LIMIT 50
        """, (user_id,)) as cur:
            notifications = await cur.fetchall()
        return {"notifications": [dict(row) for row in notifications]}
    finally:
        await conn.close()


@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int = Path(...)):
    """Mark a notification as read"""
    conn = await database.get_connection()
    try:
        await conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        await conn.commit()
        return {"message": "Notification marked as read"}
    finally:
        await conn.close()


@app.put("/api/users/{user_id}/notifications/read-all")
async def mark_all_notifications_read(user_id: int = Path(...)):
    """Mark all notifications as read for a user"""
    conn = await database.get_connection()
    try:
        await conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        await conn.commit()
        return {"message": "All notifications marked as read"}
    finally:
        await conn.close()

@app.get("/api/products/by-name/{product_name}/pcrs")
async def get_product_pcr_history_by_name(product_name: str = Path(...)):
    """Get all PCRs for a product by product_name (instead of product_id)."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT p.pcr_id_display,
                   p.status,
                   p.current_price,
                   p.proposed_price,
                   p.created_at,
                   p.updated_at,
                   p.submitted_by,
                   p.local_approved_by,
                   p.regional_approved_by,
                   s.name AS submitter_name,
                   s.email AS submitter_email,
                   la.name AS local_approver_name,
                   ra.name AS regional_approver_name
            FROM pcrs p
            LEFT JOIN users s ON p.submitted_by = s.id
            LEFT JOIN users la ON p.local_approved_by = la.id
            LEFT JOIN users ra ON p.regional_approved_by = ra.id
            WHERE p.product_name = ?
            ORDER BY p.created_at DESC
        """, (product_name,)) as cur:
            pcrs = await cur.fetchall()
        if not pcrs:
            raise HTTPException(status_code=404, detail=f"No PCRs found for product '{product_name}'")
        return {"product_name": product_name, "pcrs": [dict(row) for row in pcrs]}
    finally:
        await conn.close()


@app.get("/api/skus/{sku_id}/pcrs")
async def get_sku_pcr_history(sku_id: str = Path(..., description="SKU ID (e.g. SKU-AT-001)")):
    """Get all PCRs (history) for a single presentation SKU. Returns only PCRs where product_skus contains this SKU."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT p.pcr_id_display,
                   p.product_name,
                   p.status,
                   p.current_price,
                   p.proposed_price,
                   p.created_at,
                   p.updated_at,
                   p.finalized_at,
                   p.submitted_by,
                   p.local_approved_by,
                   p.regional_approved_by,
                   s.name AS submitter_name,
                   s.email AS submitter_email,
                   la.name AS local_approver_name,
                   ra.name AS regional_approver_name
            FROM pcrs p
            LEFT JOIN users s ON p.submitted_by = s.id
            LEFT JOIN users la ON p.local_approved_by = la.id
            LEFT JOIN users ra ON p.regional_approved_by = ra.id
            WHERE (',' || COALESCE(p.product_skus, '') || ',') LIKE ?
            ORDER BY p.created_at DESC
        """, ("%," + sku_id + ",%",)) as cur:
            pcrs = await cur.fetchall()
        if not pcrs:
            raise HTTPException(status_code=404, detail=f"No PCRs found for SKU '{sku_id}'")
        out = []
        for row in pcrs:
            r = dict(row)
            r["sku_id"] = sku_id
            r["product_skus"] = sku_id
            out.append(r)
        return {"sku_id": sku_id, "pcrs": out}
    finally:
        await conn.close()


@app.get("/api/countries/{country}/skus/{sku_id}/current-price")
async def get_sku_current_price(country: str = Path(..., description="Country code (e.g. IN)"), sku_id: str = Path(..., description="SKU ID")):
    """Get current price for a SKU in the given country from sku_price_history (latest effective_from <= today)."""
    import datetime
    conn = await database.get_connection()
    try:
        today = datetime.date.today().isoformat()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            """SELECT sku_id, country, therapeutic_area, channel, price_eur, effective_from, pcr_id FROM sku_price_history
               WHERE sku_id = ? AND country = ? AND effective_from <= ? ORDER BY effective_from DESC LIMIT 1""",
            (sku_id, country, today),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"No current price found for SKU '{sku_id}' in country '{country}'")
        out = dict(row)
        out["current_price"] = str(out.pop("price_eur", ""))
        return out
    finally:
        await conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
