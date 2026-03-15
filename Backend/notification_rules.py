import database


async def create_notification(user_id, notification_type, title, message, pcr_id=None):
    """Create an in-app notification. pcr_id may be None for admin/MDGM-only actions."""
    try:
        conn = await database.get_connection()
        try:
            await conn.execute(
                "INSERT INTO notifications (user_id,pcr_id,type,title,message) VALUES (?,?,?,?,?)",
                (user_id, pcr_id, notification_type, title, message),
            )
            await conn.commit()
        finally:
            await conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to create notification: {e}")


async def get_pcr_with_users(pcr_id_display):
    """Get PCR with user details and region (from countries). Uses LEFT JOIN for submitter
    so we still get the PCR if the submitter user is missing; we can send notifications
    to Regional users by region+TA."""
    if not pcr_id_display:
        return None
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            """SELECT p.pcr_id_display, p.product_name, p.country, p.therapeutic_area,
               co.region AS region,
               p.submitted_by, p.local_approved_by, p.regional_approved_by,
               p.escalated_by, p.global_approved_by,
               s.name AS submitter_name, s.email AS submitter_email,
               la.email AS local_approver_email, la.name AS local_approver_name,
               ra.email AS regional_approver_email, ra.name AS regional_approver_name,
               ga.email AS global_approver_email, ga.name AS global_approver_name
               FROM pcrs p
               LEFT JOIN countries co ON co.code = p.country
               LEFT JOIN users s ON p.submitted_by = s.id
               LEFT JOIN users la ON p.local_approved_by = la.id
               LEFT JOIN users ra ON p.regional_approved_by = ra.id
               LEFT JOIN users ga ON p.global_approved_by = ga.id
               WHERE p.pcr_id_display = ?""",
            (pcr_id_display,),
        ) as cur:
            row = await cur.fetchone()
        return row
    finally:
        await conn.close()


def _pcr_label(pcr):
    """Use real PCR ID in messages (e.g. PCR-614201), fallback to id if not set."""
    return pcr.get("pcr_id_display") or ("PCR-#%s" % pcr.get("id", ""))


async def notify_on_local_approve(pcr_id):
    """Notify submitter, Regional users in the same region (and TA), and local approver when a PCR receives Local approval (on submit)."""
    pcr = await get_pcr_with_users(pcr_id)
    if not pcr:
        return
    region = pcr.get("region")
    therapeutic_area = pcr.get("therapeutic_area")
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        if region is not None and therapeutic_area is not None:
            async with conn.execute(
                "SELECT id, email FROM users WHERE role = 'Regional' AND region = ? AND therapeutic_area = ?",
                (region, therapeutic_area),
            ) as cur:
                regional = await cur.fetchall()
        elif region is not None:
            async with conn.execute(
                "SELECT id, email FROM users WHERE role = 'Regional' AND region = ?",
                (region,),
            ) as cur:
                regional = await cur.fetchall()
        else:
            async with conn.execute("SELECT id, email FROM users WHERE role = 'Regional'") as cur:
                regional = await cur.fetchall()
    finally:
        await conn.close()
    label = _pcr_label(pcr)
    approver_name = pcr.get("local_approver_name") or "A Local user"
    title = f"{label} Approved by Local"
    message = f"{approver_name} approved the Price Change Request."

    if pcr["submitted_by"] != pcr.get("local_approved_by"):
        await create_notification(
            pcr["submitted_by"],
            "approved",
            title,
            message,
            pcr_id=pcr_id,
        )
    for row in regional:
        await create_notification(
            row["id"],
            "approved",
            title,
            message,
            pcr_id=pcr_id,
        )
    if pcr.get("local_approved_by"):
        await create_notification(
            pcr["local_approved_by"],
            "approved",
            f"{label} You approved at Local",
            "You approved the Price Change Request at Local level.",
            pcr_id=pcr_id,
        )
    print("[DEBUG] Created notifications for Local approval")


async def notify_on_regional_approve_reject(pcr_id, action):
    pcr = await get_pcr_with_users(pcr_id)
    if not pcr:
        return
    action_text = "approved" if action == "approved" else "rejected"
    label = _pcr_label(pcr)
    approver_name = pcr.get("regional_approver_name") or "A Regional user"
    title = f"{label} {action_text.capitalize()} by Regional"
    message = f"{approver_name} {action_text} the Price Change Request."

    if pcr["submitted_by"] != pcr.get("regional_approved_by"):
        await create_notification(
            pcr["submitted_by"], action, title, message, pcr_id=pcr_id
        )
    if pcr.get("local_approved_by") and pcr.get("local_approved_by") != pcr.get("regional_approved_by"):
        await create_notification(
            pcr["local_approved_by"], action, title, message, pcr_id=pcr_id
        )
    if pcr.get("regional_approved_by"):
        await create_notification(
            pcr["regional_approved_by"],
            action,
            f"{label} You {action_text} at Regional",
            f"You {action_text} the Price Change Request at Regional level.",
            pcr_id=pcr_id,
        )
    print(f"[DEBUG] Creating notifications for Regional approve/reject: {action_text}")


async def notify_on_escalate_to_global(pcr_id):
    """Notify all Global users when a PCR is escalated to Global (Global can act on escalated PCRs from any country)."""
    pcr = await get_pcr_with_users(pcr_id)
    if not pcr:
        return
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("SELECT id FROM users WHERE role = 'Global'") as cur:
            global_list = await cur.fetchall()
    finally:
        await conn.close()
    label = _pcr_label(pcr)
    title = f"{label} Escalated to Global"
    message = "PCR has been escalated to Global. Please review, edit if needed, approve or reject, and finalise."
    for row in global_list:
        await create_notification(
            row["id"], "escalated_to_global", title, message, pcr_id=pcr_id
        )


async def notify_on_global_approve_reject(pcr_id, action):
    """When Global approves or rejects an escalated PCR, notify submitter, local approver, regional approver, and the global approver."""
    pcr = await get_pcr_with_users(pcr_id)
    if not pcr:
        return
    action_text = "approved" if action == "approved" else "rejected"
    label = _pcr_label(pcr)
    approver_name = pcr.get("global_approver_name") or "A Global user"
    title = f"{label} {action_text.capitalize()} by Global"
    message = f"{approver_name} {action_text} the Price Change Request at Global level."

    if pcr.get("submitted_by"):
        await create_notification(
            pcr["submitted_by"], action, title, message, pcr_id=pcr_id
        )
    if pcr.get("local_approved_by") and pcr["local_approved_by"] != pcr.get("global_approved_by"):
        await create_notification(
            pcr["local_approved_by"], action, title, message, pcr_id=pcr_id
        )
    if pcr.get("regional_approved_by") and pcr["regional_approved_by"] != pcr.get("global_approved_by"):
        await create_notification(
            pcr["regional_approved_by"], action, title, message, pcr_id=pcr_id
        )
    if pcr.get("escalated_by"):
        await create_notification(
            pcr["escalated_by"], action, title, message, pcr_id=pcr_id
        )
    if pcr.get("global_approved_by"):
        await create_notification(
            pcr["global_approved_by"],
            action,
            f"{label} You {action_text} at Global",
            f"You {action_text} the Price Change Request at Global level.",
            pcr_id=pcr_id,
        )


async def notify_on_finalise(pcr_id):
    """When a PCR is finalised (by Local), notify the submitter and everyone who approved it (local_approved_by, regional_approved_by, global_approved_by if set). Only those involved get the finalise notification."""
    pcr = await get_pcr_with_users(pcr_id)
    if not pcr:
        return
    label = _pcr_label(pcr)
    title = f"{label} Finalised"
    message = "The Price Change Request has been finalised. Current price has been updated per effective date."

    for user_id_key in ("submitted_by", "local_approved_by", "regional_approved_by", "global_approved_by"):
        uid = pcr.get(user_id_key)
        if uid:
            await create_notification(
                uid, "finalised", title, message, pcr_id=pcr_id
            )


async def get_region_for_country(country):
    """Return region code for a country from countries table, or None."""
    if not country:
        return None
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT region FROM countries WHERE code = ?", (country,)) as cur:
            row = await cur.fetchone()
        return row[0] if row else None
    finally:
        await conn.close()


async def notify_admin_action(country, therapeutic_area, action_kind, entity_label, pcr_id=None):
    """Notify Local (for country+TA) and Regional (for region+TA) users when Admin adds/updates/deletes a PCR or MDGM row.
    action_kind: 'addition' | 'update' | 'deletion'. entity_label: e.g. 'PCR PCR-123 deleted' or 'SKU XYZ added'.
    pcr_id is optional (None for MDGM-only actions)."""
    if not country and not therapeutic_area:
        return
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        region = await get_region_for_country(country) if country else None
        user_ids = set()
        if country and therapeutic_area:
            async with conn.execute(
                """SELECT u.id FROM users u
                   JOIN user_countries uc ON uc.user_id = u.id
                   WHERE u.role = 'Local' AND uc.country = ? AND u.therapeutic_area = ?""",
                (country, therapeutic_area),
            ) as cur:
                for row in await cur.fetchall():
                    user_ids.add(row["id"])
        if country and therapeutic_area and region:
            async with conn.execute(
                "SELECT id FROM users WHERE role = 'Regional' AND region = ? AND therapeutic_area = ?",
                (region, therapeutic_area),
            ) as cur:
                for row in await cur.fetchall():
                    user_ids.add(row["id"])
        elif region and therapeutic_area:
            async with conn.execute(
                "SELECT id FROM users WHERE role = 'Regional' AND region = ? AND therapeutic_area = ?",
                (region, therapeutic_area),
            ) as cur:
                for row in await cur.fetchall():
                    user_ids.add(row["id"])
        title = f"Admin: {entity_label}"
        message = f"An admin performed an {action_kind} affecting your country/region and therapeutic area."
        for uid in user_ids:
            await create_notification(
                uid, "admin_action", title, message, pcr_id=pcr_id
            )
    finally:
        await conn.close()
