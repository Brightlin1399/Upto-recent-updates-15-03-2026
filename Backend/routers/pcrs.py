from fastapi import APIRouter, HTTPException, Path, Body, Query, Header
router = APIRouter()
import sqlite3
import database
import notification_rules
from helpers.pcr_helpers import (
    _therapeutic_area_for_brand,
    _user_can_approve_for_pcr,
    _parse_price,
    get_current_price_eur,
    run_submit_approval_flow,
    get_brand_from_mdgm,
)
from models import (
    SubmitPCRRequest,
    ApproveRejectRequest,
    UpdatePCRRequest,
    RegionalEditPCRRequest,
    FinalisePCRRequest,
    ResubmitPCRRequest,
)


@router.post("/pcrs", status_code=201)
async def submit_pcr(request: SubmitPCRRequest, x_user_id: int = Header(..., alias="X-User-Id")):
    """Submit a new PCR (Country, Brand, SKUs). Only Local can submit; caller must be the submitter (X-User-Id must equal submitted_by)."""
    try:
        submitted_by = request.submitted_by
        if submitted_by != x_user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only submit a PCR as yourself. X-User-Id must equal submitted_by.",
            )
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
                "SELECT role, country, therapeutic_area, region FROM users WHERE id = ?",
                (submitted_by,),
            ) as cur:
                user = await cur.fetchone()
            if not user:
                raise HTTPException(status_code=400, detail=f"User id {submitted_by} not found")
            if user[0] != "Local":
                raise HTTPException(status_code=403, detail="Only Local users can submit PCRs")
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
            initial_status = "draft" if getattr(request, "save_as_draft", False) else "submitted"
            try:
                await conn.execute(
                    """INSERT INTO pcrs (
                        pcr_id_display, product_id, product_name, submitted_by, status,
                        proposed_price, country, therapeutic_area, product_skus,
                        channel, price_type,
                        price_change_type, expected_response_date, price_change_reason,
                        price_change_reason_comments, submission_context, proposed_percent,
                        effective_date, is_discontinue_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        pcr_id_display,
                        request.product_id,
                        request.product_name,
                        submitted_by,
                        initial_status,
                        request.proposed_price,
                        country,
                        brand_ta,
                        product_skus_str,
                        request.channel,
                        request.price_type,
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
            except sqlite3.IntegrityError as e:
                if "pcr_id_display" in str(e) or "UNIQUE" in str(e):
                    raise HTTPException(
                        status_code=400,
                        detail=f"A PCR with ID '{pcr_id_display}' already exists. Please use a unique PCR ID.",
                    ) from e
                raise
        finally:
            await conn.close()

        if initial_status == "draft":
            return {"message": "PCR saved as draft", "pcr_id": pcr_id_display, "draft": True}

        return await run_submit_approval_flow(pcr_id_display, submitted_by)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/pcrs/{pcr_id}/regional-approve")
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
            raise HTTPException(status_code=403, detail="You are not allowed to approve this PCR.")
        async with conn.execute(
            """SELECT status, country, therapeutic_area, channel, product_skus, proposed_price, price_type, product_name
               FROM pcrs WHERE pcr_id_display = ?""",
            (pcr_id,),
        ) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        status, country, therapeutic_area, channel, product_skus_str, proposed_price, price_type, product_name = (
            pcr[0],
            pcr[1],
            pcr[2],
            pcr[3],
            pcr[4],
            pcr[5],
            pcr[6],
            pcr[7] if len(pcr) > 7 else None,
        )
        sku_list_regional = [s.strip() for s in (product_skus_str or "").split(",") if s.strip()] if product_skus_str else []
        if status != "local_approved":
            raise HTTPException(status_code=400, detail=f"PCR is in '{pcr[0]}' status. Can only approve when status is local_approved.")
        from helpers.pcr_helpers import _parse_price
        proposed_eur = _parse_price(proposed_price)

        await conn.execute(
            """UPDATE pcrs
               SET regional_approved_by = ?,
                   status = 'regional_approved',
                   regional_approved_price_eur = ?,
                   updated_at = CURRENT_TIMESTAMP
             WHERE pcr_id_display = ?""",
            (approved_by, proposed_eur, pcr_id),
        )
        await conn.commit()
    finally:
        await conn.close()
    try:
        audit_brand = await get_brand_from_mdgm(sku_list_regional[0], country, therapeutic_area) if sku_list_regional and country and therapeutic_area else (product_name or None)
        await database.log_audit(
            user_id=approved_by,
            action="Regional approved",
            entity_type="pcr",
            entity_id=pcr_id,
            brand=audit_brand,
            country=country or None,
            details=None,
            sku_ids=sku_list_regional,
        )
    except Exception:
        pass
    await notification_rules.notify_on_regional_approve_reject(pcr_id, "approved")
    return {"message": "PCR approved by Regional", "pcr_id": pcr_id, "status": "regional_approved"}

@router.put("/pcrs/{pcr_id}/regional-reject")
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
            raise HTTPException(status_code=403, detail="You are not allowed to reject this PCR.")
        async with conn.execute("SELECT status, country, therapeutic_area, product_name, product_skus FROM pcrs WHERE pcr_id_display = ?", (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] != "local_approved":
            raise HTTPException(status_code=400, detail=f"PCR is in '{pcr[0]}' status. Can only reject when status is local_approved.")
        pcr_country = pcr[1] if len(pcr) > 1 else None
        therapeutic_area_rej = pcr[2] if len(pcr) > 2 else None
        product_name = pcr[3] if len(pcr) > 3 else None
        product_skus_str_rej = pcr[4] if len(pcr) > 4 else None
        sku_list_reject = [s.strip() for s in (product_skus_str_rej or "").split(",") if s.strip()] if product_skus_str_rej else []
        await conn.execute(
            """UPDATE pcrs SET regional_approved_by = NULL, local_approved_by = NULL, escalated_by = NULL, global_approved_by = NULL,
                   regional_approved_price_eur = NULL, global_approved_price_eur = NULL, status = 'draft' WHERE pcr_id_display = ?""",
            (pcr_id,),
        )
        await conn.commit()
    finally:
        await conn.close()
    try:
        audit_brand = await get_brand_from_mdgm(sku_list_reject[0], pcr_country, therapeutic_area_rej) if sku_list_reject and pcr_country and therapeutic_area_rej else (product_name or None)
        await database.log_audit(
            user_id=rejected_by,
            action="Regional rejected",
            entity_type="pcr",
            entity_id=pcr_id,
            brand=audit_brand,
            country=pcr_country or None,
            details=None,
            sku_ids=sku_list_reject,
        )
    except Exception:
        pass
    await notification_rules.notify_on_regional_approve_reject(pcr_id, "rejected")
    return {"message": "PCR rejected by Regional; back to draft for Local", "pcr_id": pcr_id, "status": "draft"}


@router.put("/pcrs/{pcr_id}/global-approve")
async def global_approve(pcr_id: str = Path(...), request: ApproveRejectRequest = Body(...)):
    """Global approves an escalated PCR."""
    approved_by = request.approved_by
    if not approved_by:
        raise HTTPException(status_code=400, detail="approved_by is required")
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (approved_by,)) as cur:
            approver = await cur.fetchone()
        if not approver or approver[0] != "Global":
            raise HTTPException(status_code=400, detail="Only Global users can approve at Global level")
        if not await _user_can_approve_for_pcr(approved_by, pcr_id):
            raise HTTPException(status_code=403, detail="You are not allowed to approve this PCR at Global level.")
        async with conn.execute(
            """SELECT status, proposed_price, country, therapeutic_area, product_name, product_skus FROM pcrs WHERE pcr_id_display = ?""",
            (pcr_id,),
        ) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        status, proposed_price = pcr[0], pcr[1]
        pcr_country = pcr[2] if len(pcr) > 2 else None
        therapeutic_area_ga = pcr[3] if len(pcr) > 3 else None
        product_name = pcr[4] if len(pcr) > 4 else None
        product_skus_str_ga = pcr[5] if len(pcr) > 5 else None
        sku_list_global = [s.strip() for s in (product_skus_str_ga or "").split(",") if s.strip()] if product_skus_str_ga else []
        if status != "escalated_to_global":
            raise HTTPException(status_code=400, detail=f"Can only approve when status is escalated_to_global. Current: {status}")

        from helpers.pcr_helpers import _parse_price  # local import to avoid cycles

        proposed_eur = _parse_price(proposed_price)
        await conn.execute(
            """UPDATE pcrs
               SET global_approved_by = ?,
                   status = 'global_approved',
                   global_approved_price_eur = ?,
                   updated_at = CURRENT_TIMESTAMP
             WHERE pcr_id_display = ?""",
            (approved_by, proposed_eur, pcr_id),
        )
        await conn.commit()
    finally:
        await conn.close()
    try:
        audit_brand = await get_brand_from_mdgm(sku_list_global[0], pcr_country, therapeutic_area_ga) if sku_list_global and pcr_country and therapeutic_area_ga else (product_name or None)
        await database.log_audit(
            user_id=approved_by,
            action="Global approved",
            entity_type="pcr",
            entity_id=pcr_id,
            brand=audit_brand,
            country=pcr_country or None,
            details=None,
            sku_ids=sku_list_global,
        )
    except Exception:
        pass
    await notification_rules.notify_on_global_approve_reject(pcr_id, "approved")
    return {"message": "PCR approved by Global", "pcr_id": pcr_id, "status": "global_approved"}


@router.put("/pcrs/{pcr_id}/global-reject")
async def global_reject(pcr_id: str = Path(...), request: ApproveRejectRequest = Body(...)):
    """Global rejects an escalated PCR; status becomes draft, back to Local."""
    rejected_by = request.rejected_by
    if not rejected_by:
        raise HTTPException(status_code=400, detail="rejected_by is required")
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (rejected_by,)) as cur:
            approver = await cur.fetchone()
        if not approver or approver[0] != "Global":
            raise HTTPException(status_code=400, detail="Only Global users can reject at Global level")
        if not await _user_can_approve_for_pcr(rejected_by, pcr_id):
            raise HTTPException(status_code=403, detail="You are not allowed to reject this PCR at Global level.")
        async with conn.execute("SELECT status, country, therapeutic_area, product_name, product_skus FROM pcrs WHERE pcr_id_display = ?", (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] != "escalated_to_global":
            raise HTTPException(status_code=400, detail=f"Can only reject when status is escalated_to_global. Current: {pcr[0]}")
        pcr_country = pcr[1] if len(pcr) > 1 else None
        therapeutic_area_gr = pcr[2] if len(pcr) > 2 else None
        product_name = pcr[3] if len(pcr) > 3 else None
        product_skus_str_gr = pcr[4] if len(pcr) > 4 else None
        sku_list_global_rej = [s.strip() for s in (product_skus_str_gr or "").split(",") if s.strip()] if product_skus_str_gr else []
        await conn.execute(
            """UPDATE pcrs SET status = 'draft', global_approved_by = NULL, escalated_by = NULL,
                   local_approved_by = NULL, regional_approved_by = NULL,
                   regional_approved_price_eur = NULL, global_approved_price_eur = NULL WHERE pcr_id_display = ?""",
            (pcr_id,),
        )
        await conn.commit()
    finally:
        await conn.close()
    try:
        audit_brand = await get_brand_from_mdgm(sku_list_global_rej[0], pcr_country, therapeutic_area_gr) if sku_list_global_rej and pcr_country and therapeutic_area_gr else (product_name or None)
        await database.log_audit(
            user_id=rejected_by,
            action="Global rejected",
            entity_type="pcr",
            entity_id=pcr_id,
            brand=audit_brand,
            country=pcr_country or None,
            details=None,
            sku_ids=sku_list_global_rej,
        )
    except Exception:
        pass
    await notification_rules.notify_on_global_approve_reject(pcr_id, "rejected")
    return {"message": "PCR rejected by Global; back to draft for Local", "pcr_id": pcr_id, "status": "draft"}


@router.get("/pcrs")
async def get_all_pcrs(user_id: int = Header(..., alias="X-User-Id")):
    """Get PCRs visible to the current user. Each PCR includes current_price_at_proposal_eur (first SKU, at proposal time).

    Local: only PCRs for their country.
    Regional: only PCRs for countries in their region.
    Global: only PCRs with status escalated_to_global.
    Admin: all PCRs.
    """
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        # Lookup current user
        async with conn.execute(
            "SELECT role, country, region FROM users WHERE id = ?",
            (user_id,),
        ) as cur:
            user = await cur.fetchone()
        if not user:
            raise HTTPException(status_code=400, detail=f"User id {user_id} not found")
        role = user.get("role")
        user_country = user.get("country")
        user_region = user.get("region")

        base_sql = """
            SELECT p.*,
                   co.region AS region,
                   s.name AS submitter_name, s.email AS submitter_email,
                   la.name AS local_approver_name,
                   ra.name AS regional_approver_name
            FROM pcrs p
            LEFT JOIN countries co ON co.code = p.country
            LEFT JOIN users s ON p.submitted_by = s.id
            LEFT JOIN users la ON p.local_approved_by = la.id
            LEFT JOIN users ra ON p.regional_approved_by = ra.id
        """
        params: list[object] = []

        if role == "Local":
            # Local: see only PCRs for their country
            base_sql += " WHERE p.country = ?"
            params.append(user_country)
        elif role == "Regional":
            # Regional: see PCRs for countries in their region
            base_sql += " WHERE co.region = ?"
            params.append(user_region)
        elif role == "Global":
            # Global: see only escalated PCRs
            base_sql += " WHERE p.status = 'escalated_to_global'"
        # Admin: no filter (all PCRs)

        base_sql += " ORDER BY p.created_at DESC"

        async with conn.execute(base_sql, tuple(params)) as cur:
            pcrs = await cur.fetchall()
        out_list = [dict(row) for row in pcrs]
        import datetime
        for r in out_list:
            country = (r.get("country") or "").strip()
            ta = (r.get("therapeutic_area") or "").strip()
            ch = (r.get("channel") or "Retail").strip()
            pt = (r.get("price_type") or "").strip()
            product_skus_str = (r.get("product_skus") or "").strip()
            sku_list = [s.strip() for s in product_skus_str.split(",") if s.strip()]
            if not (country and ta and ch and pt and sku_list):
                r["current_price_at_proposal_eur"] = None
                continue
            if r.get("status") == "finalised":
                ref_date_str = r.get("effective_date") or ((r.get("finalized_at") or "")[:10]) or ((r.get("created_at") or "")[:10])
                if ref_date_str:
                    try:
                        ref_date = datetime.date.fromisoformat(ref_date_str[:10])
                        as_of_date = (ref_date - datetime.timedelta(days=1)).isoformat()
                    except ValueError:
                        as_of_date = None
                else:
                    as_of_date = None
            else:
                as_of_date = ((r.get("created_at") or "")[:10]) or None
            at_proposal = await get_current_price_eur(sku_list[0], country, ta, ch, pt, as_of_date=as_of_date)
            r["current_price_at_proposal_eur"] = float(at_proposal) if at_proposal is not None else None
        return {"pcrs": out_list}
    finally:
        await conn.close()


@router.get("/pcrs/{pcr_id}")
async def get_pcr(
    pcr_id: str = Path(...),
    user_id: int | None = Header(None, alias="X-User-Id"),
):
    """Get a single PCR by display ID. Optional X-User-Id enforces visibility. skus_pricing uses current_price_at_proposal_eur (not live)."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT p.*,
                   co.region AS region,
                   s.name AS submitter_name, s.email AS submitter_email,
                   la.name AS local_approver_name,
                   ra.name AS regional_approver_name
            FROM pcrs p
            LEFT JOIN countries co ON co.code = p.country
            LEFT JOIN users s ON p.submitted_by = s.id
            LEFT JOIN users la ON p.local_approved_by = la.id
            LEFT JOIN users ra ON p.regional_approved_by = ra.id
            WHERE p.pcr_id_display = ?
        """, (pcr_id,)) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        out = dict(pcr)

        # Enforce visibility when user_id is provided
        if user_id is not None:
            async with conn.execute(
                "SELECT role, country, region FROM users WHERE id = ?", (user_id,)
            ) as cur:
                user = await cur.fetchone()
            if user:
                role = user.get("role")
                user_country = user.get("country")
                user_region = user.get("region")
                pcr_country = out.get("country")
                pcr_region = out.get("region")
                pcr_status = out.get("status")
                if role == "Local" and pcr_country != user_country:
                    raise HTTPException(status_code=403, detail="You cannot view this PCR.")
                if role == "Regional" and pcr_region != user_region:
                    raise HTTPException(status_code=403, detail="You cannot view this PCR.")
                if role == "Global" and pcr_status != "escalated_to_global":
                    raise HTTPException(status_code=403, detail="You cannot view this PCR.")

        # Add per-SKU pricing at proposal time (current at proposal, not live)
        product_skus_str = (out.get("product_skus") or "").strip()
        country = out.get("country") or ""
        therapeutic_area = out.get("therapeutic_area") or ""
        channel = (out.get("channel") or "Retail").strip()
        price_type = (out.get("price_type") or "").strip()
        proposed_price = out.get("proposed_price")
        from helpers.pcr_helpers import _parse_price
        import datetime
        proposed_eur = _parse_price(proposed_price) if proposed_price else None

        if out.get("status") == "finalised":
            ref_date_str = out.get("effective_date") or ((out.get("finalized_at") or "")[:10]) or ((out.get("created_at") or "")[:10])
            if ref_date_str:
                try:
                    ref_date = datetime.date.fromisoformat(ref_date_str[:10])
                    as_of_date = (ref_date - datetime.timedelta(days=1)).isoformat()
                except ValueError:
                    as_of_date = None
            else:
                as_of_date = None
        else:
            as_of_date = ((out.get("created_at") or "")[:10]) or None

        skus_pricing = []
        if country and therapeutic_area and channel and price_type:
            sku_list = [s.strip() for s in product_skus_str.split(",") if s.strip()]
            for sku_id in sku_list:
                current_eur = await get_current_price_eur(
                    sku_id, country, therapeutic_area, channel, price_type, as_of_date=as_of_date
                )
                skus_pricing.append({
                    "sku_id": sku_id,
                    "current_price_at_proposal_eur": float(current_eur) if current_eur is not None else None,
                    "proposed_price_eur": float(proposed_eur) if proposed_eur is not None else None,
                })
        out["skus_pricing"] = skus_pricing
        return out
    finally:
        await conn.close()

@router.put("/pcrs/{pcr_id}")
async def update_pcr(pcr_id: str = Path(...), request: UpdatePCRRequest = Body(...)):
    """Update a PCR. Only Local users can update. Allowed when status is draft, rejected, or approved but not yet finalised (local_approved, regional_approved)."""
    edited_by = request.edited_by
    editable_statuses = ("draft", "global_rejected", "regional_rejected", "local_approved", "regional_approved")
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT id, role, country, therapeutic_area FROM users WHERE id = ?",
            (edited_by,),
        ) as cur:
            editor = await cur.fetchone()
        if not editor or editor[1] != "Local":
            raise HTTPException(
                status_code=400,
                detail="Only Local users can update PCRs. Regional cannot edit or resubmit.",
            )
        async with conn.execute(
            "SELECT status, country, therapeutic_area FROM pcrs WHERE pcr_id_display = ?",
            (pcr_id,),
        ) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] not in editable_statuses:
            raise HTTPException(status_code=400, detail=f"Can only edit draft, rejected, or approved (pre-finalisation) PCRs. Current status: {pcr[0]}")
        if pcr[1] != editor[2] or pcr[2] != editor[3]:
            raise HTTPException(
                status_code=403,
                detail="You can only update PCRs for your own country and therapeutic area.",
            )
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
        if request.price_type is not None:
            updates.append("price_type = ?")
            params.append(request.price_type)
        if not updates:
            raise HTTPException(status_code=400, detail="Provide at least one field to update")
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(pcr_id)
        await conn.execute("UPDATE pcrs SET " + ", ".join(updates) + " WHERE pcr_id_display = ?", tuple(params))
        await conn.commit()
        return {"message": "PCR updated", "pcr_id": pcr_id}
    finally:
        await conn.close()


@router.put("/pcrs/{pcr_id}/finalise")
async def finalise_pcr(pcr_id: str = Path(...), request: FinalisePCRRequest = Body(...)):
    """Finalise an approved PCR. Writes each SKU's approved price to sku_price_history with effective_from = PCR effective_date (or today).

    Only Local users can finalise, and only for PCRs in their own country and therapeutic_area."""
    finalised_by = request.finalised_by
    conn = await database.get_connection()
    try:
        # Finaliser must be Local and must match PCR's country and therapeutic area
        async with conn.execute(
            "SELECT role, country, therapeutic_area FROM users WHERE id = ?",
            (finalised_by,),
        ) as cur:
            user = await cur.fetchone()
        if not user or user[0] != "Local":
            raise HTTPException(status_code=400, detail="Only Local users can finalise PCRs.")
        async with conn.execute(
            """SELECT status, country, therapeutic_area, channel, product_skus, proposed_price,
                      effective_date, price_type, regional_approved_price_eur, global_approved_price_eur, product_name
               FROM pcrs WHERE pcr_id_display = ?""",
            (pcr_id,),
        ) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        status, country, therapeutic_area, channel, product_skus_str, proposed_price, effective_date, price_type, regional_approved_price_eur, global_approved_price_eur, product_name = (
            pcr[0],
            pcr[1] or "",
            pcr[2] or "",
            (pcr[3] or "Retail").strip(),
            (pcr[4] or "").strip(),
            pcr[5],
            pcr[6],
            pcr[7],
            pcr[8],
            pcr[9],
            (pcr[10] or "").strip() if len(pcr) > 10 else "",
        )

        user_country, user_ta = user[1], user[2]
        if country != user_country or therapeutic_area != user_ta:
            raise HTTPException(
                status_code=403,
                detail="You can only finalise PCRs for your own country and therapeutic area.",
            )
        if status not in ("regional_approved", "global_approved"):
            raise HTTPException(
                status_code=400,
                detail="Can only finalise when status is regional_approved or global_approved.",
            )

        from helpers.pcr_helpers import _parse_price, get_current_price_eur
        import datetime

        price_eur = _parse_price(proposed_price) if proposed_price else None
        if not (country and therapeutic_area and channel and product_skus_str and price_eur is not None and price_type):
            raise HTTPException(status_code=400, detail="PCR missing required pricing context for finalisation")

        sku_list = [s.strip() for s in product_skus_str.split(",") if s.strip()]
        if not sku_list:
            raise HTTPException(status_code=400, detail="No SKUs found on PCR for finalisation")

        # Require current price for every SKU at finalisation
        today = datetime.date.today().isoformat()
        current_by_sku: dict[str, float] = {}
        for sku_id in sku_list:
            current_eur = await get_current_price_eur(
                sku_id, country, therapeutic_area, channel, price_type, as_of_date=today
            )
            if current_eur is None:
                raise HTTPException(
                    status_code=400,
                    detail="Missing current price at finalisation time; ensure MDGM current or history exists for all SKUs.",
                )
            current_by_sku[sku_id] = float(current_eur)

        if status == "regional_approved":
            if regional_approved_price_eur is None:
                raise HTTPException(status_code=400, detail="Regional approved price not recorded; cannot finalise.")
            if price_eur < regional_approved_price_eur:
                raise HTTPException(status_code=400, detail="Proposed price is lower than the Regional-approved price; please re-submit for approval.")
        elif status == "global_approved":
            if global_approved_price_eur is None:
                raise HTTPException(status_code=400, detail="Global approved price not recorded; cannot finalise.")
            if price_eur < global_approved_price_eur:
                raise HTTPException(status_code=400, detail="Proposed price is lower than the Global-approved price; please re-submit for approval.")

        # Write history and mark finalised (floor_price_eur column kept for schema compat; we pass NULL)
        effective_from = effective_date if effective_date else datetime.date.today().isoformat()
        for sku_id in sku_list:
            await conn.execute(
                """INSERT INTO sku_price_history (sku_id, country, therapeutic_area, channel, price_type,
                                                  price_eur, floor_price_eur, effective_from, pcr_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sku_id, country, therapeutic_area, channel, price_type, price_eur, None, effective_from, pcr_id),
            )

        # Update PCR row: set current_price to the finalised price so list/detail show it; set status and finalized_at
        current_price_str = str(int(price_eur)) if price_eur == int(price_eur) else str(price_eur)
        published_val = 1 if request.published else 0 if request.published is not None else None
        if published_val is not None:
            await conn.execute(
                "UPDATE pcrs SET current_price = ?, finalized_at = CURRENT_TIMESTAMP, status = 'finalised', updated_at = CURRENT_TIMESTAMP, published = ? WHERE pcr_id_display = ?",
                (current_price_str, published_val, pcr_id),
            )
        else:
            await conn.execute(
                "UPDATE pcrs SET current_price = ?, finalized_at = CURRENT_TIMESTAMP, status = 'finalised', updated_at = CURRENT_TIMESTAMP WHERE pcr_id_display = ?",
                (current_price_str, pcr_id),
            )
        await conn.commit()
    finally:
        await conn.close()
    await notification_rules.notify_on_finalise(pcr_id)
    try:
        details = f"Effective from {effective_from}"
        audit_brand = await get_brand_from_mdgm(sku_list[0], country, therapeutic_area) if sku_list and country and therapeutic_area else (product_name or None)
        await database.log_audit(
            user_id=finalised_by,
            action="PCR finalised",
            entity_type="pcr",
            entity_id=pcr_id,
            brand=audit_brand,
            country=country or None,
            details=details,
            sku_ids=sku_list,
        )
    except Exception:
        pass
    return {"message": "PCR finalised", "pcr_id": pcr_id, "status": "finalised"}


@router.put("/pcrs/{pcr_id}/resubmit")
async def re_submit_pcr(pcr_id: str = Path(...), request: ResubmitPCRRequest = Body(...)):
    """Resubmit a draft or rejected PCR. Only Local users can resubmit; Regional cannot. Rejected PCRs stay in draft until Local resubmits."""
    re_submitted_by = request.re_submitted_by
    rejected_cases = ("global_rejected", "regional_rejected", "draft")
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT status, country, therapeutic_area, product_name, product_skus FROM pcrs WHERE pcr_id_display = ?",
            (pcr_id,),
        ) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            raise HTTPException(status_code=404, detail="PCR not found")
        if pcr[0] not in rejected_cases:
            raise HTTPException(status_code=400, detail=f"Can only resubmit draft or rejected PCRs. Current status: {pcr[0]}")
        pcr_country = pcr[1] if len(pcr) > 1 else None
        product_name = pcr[3] if len(pcr) > 3 else None
        product_skus_str_rs = pcr[4] if len(pcr) > 4 else None
        sku_list_resubmit = [s.strip() for s in (product_skus_str_rs or "").split(",") if s.strip()] if product_skus_str_rs else []
        async with conn.execute(
            "SELECT id, role, country, therapeutic_area FROM users WHERE id = ?",
            (re_submitted_by,),
        ) as cur:
            re_submitter = await cur.fetchone()
        if not re_submitter or re_submitter[1] != "Local":
            raise HTTPException(
                status_code=400,
                detail="Only Local users can resubmit PCRs. Regional cannot edit or resubmit.",
            )
        if pcr[1] != re_submitter[2] or pcr[2] != re_submitter[3]:
            raise HTTPException(
                status_code=403,
                detail="You can only resubmit PCRs for your own country and therapeutic area.",
            )
        await conn.execute(
            """
            UPDATE pcrs SET status = 'submitted',
                submitted_by = ?, local_approved_by = NULL, regional_approved_by = NULL, escalated_by = NULL, global_approved_by = NULL,
                regional_approved_price_eur = NULL, global_approved_price_eur = NULL
            WHERE pcr_id_display = ?
        """,
            (re_submitted_by, pcr_id),
        )
        await conn.commit()
    finally:
        await conn.close()
    try:
        therapeutic_area_rs = pcr[2] if len(pcr) > 2 else None
        audit_brand = await get_brand_from_mdgm(sku_list_resubmit[0], pcr_country, therapeutic_area_rs) if sku_list_resubmit and pcr_country and therapeutic_area_rs else (product_name or None)
        await database.log_audit(
            user_id=re_submitted_by,
            action="PCR resubmitted",
            entity_type="pcr",
            entity_id=pcr_id,
            brand=audit_brand,
            country=pcr_country or None,
            details=None,
            sku_ids=sku_list_resubmit,
        )
    except Exception:
        pass
    return await run_submit_approval_flow(pcr_id, re_submitted_by)


@router.get("/products/by-name/{product_name}/pcrs")
async def get_product_pcr_history_by_name(product_name: str = Path(...)):
    """Get all PCRs for a product by product_name (instead of product_id)."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT p.pcr_id_display,
                   p.country,
                   co.region AS region,
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
            LEFT JOIN countries co ON co.code = p.country
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


@router.get("/skus/{sku_id}/pcrs")
async def get_sku_pcr_history(sku_id: str = Path(..., description="SKU ID (e.g. SKU-AT-001)")):
    """Get all PCRs (history) for a single presentation SKU. Returns only PCRs where product_skus contains this SKU.
    Each PCR has: current_price (DB, price after this PCR was finalised, or null); current_price_at_proposal_eur (current price at proposal time)."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("""
            SELECT p.pcr_id_display,
                   p.product_name,
                   p.country,
                   co.region AS region,
                   p.status,
                   p.current_price,
                   p.proposed_price,
                   p.created_at,
                   p.updated_at,
                   p.finalized_at,
                   p.effective_date,
                   p.product_skus,
                   p.submitted_by,
                   p.local_approved_by,
                   p.regional_approved_by,
                   p.therapeutic_area,
                   p.channel,
                   p.price_type,
                   s.name AS submitter_name,
                   s.email AS submitter_email,
                   la.name AS local_approver_name,
                   ra.name AS regional_approver_name
            FROM pcrs p
            LEFT JOIN countries co ON co.code = p.country
            LEFT JOIN users s ON p.submitted_by = s.id
            LEFT JOIN users la ON p.local_approved_by = la.id
            LEFT JOIN users ra ON p.regional_approved_by = ra.id
            WHERE (',' || COALESCE(p.product_skus, '') || ',') LIKE ?
            ORDER BY p.created_at DESC
        """, ("%," + sku_id + ",%",)) as cur:
            pcrs = await cur.fetchall()
        if not pcrs:
            raise HTTPException(status_code=404, detail=f"No PCRs found for SKU '{sku_id}'")
        import datetime
        from helpers.pcr_helpers import get_current_price_eur
        out = []
        for row in pcrs:
            r = dict(row)
            r["sku_id"] = sku_id
            r["product_skus"] = r.get("product_skus") or sku_id
            # Current price at proposal time (for history): use as_of_date so we get price before this PCR took effect
            country = r.get("country") or ""
            ta = (r.get("therapeutic_area") or "").strip()
            ch = (r.get("channel") or "Retail").strip()
            pt = (r.get("price_type") or "").strip()
            if country and ta and ch and pt:
                # Current price at proposal time: for finalised PCRs use day before effective_date so we get price before this PCR took effect
                if r.get("status") == "finalised":
                    ref_date_str = r.get("effective_date") or ((r.get("finalized_at") or "")[:10]) or ((r.get("created_at") or "")[:10])
                    if ref_date_str:
                        try:
                            ref_date = datetime.date.fromisoformat(ref_date_str[:10])
                            as_of_date = (ref_date - datetime.timedelta(days=1)).isoformat()
                        except ValueError:
                            as_of_date = None
                    else:
                        as_of_date = None
                else:
                    # Not finalised: use created_at date (price on submission day)
                    as_of_date = ((r.get("created_at") or "")[:10]) or None
                at_proposal_eur = await get_current_price_eur(sku_id, country, ta, ch, pt, as_of_date=as_of_date)
                r["current_price_at_proposal_eur"] = float(at_proposal_eur) if at_proposal_eur is not None else None
            else:
                r["current_price_at_proposal_eur"] = None
            out.append(r)
        return {"sku_id": sku_id, "pcrs": out}
    finally:
        await conn.close()


@router.get("/countries/{country}/skus/{sku_id}/price-history")
async def get_sku_price_history(
    country: str = Path(..., description="Country code (e.g. IN)"),
    sku_id: str = Path(..., description="SKU ID"),
    therapeutic_area: str = Query(None, description="Filter by therapeutic area (optional)"),
    channel: str = Query(None, description="Filter by channel (optional)"),
    price_type: str = Query(None, description="Filter by price type (optional)"),
):
    """Get full price history for a SKU from sku_price_history. Returns all rows (each finalisation adds one) ordered by effective_from DESC.
    Each row includes previous_price_eur = current price before this change (so you see 'from X to Y on date')."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        sql = """
            SELECT sku_id, country, therapeutic_area, channel, price_type,
                   price_eur, effective_from, pcr_id, created_at
            FROM sku_price_history
            WHERE sku_id = ? AND country = ?
        """
        params = [sku_id, country]
        if therapeutic_area:
            sql += " AND therapeutic_area = ?"
            params.append(therapeutic_area)
        if channel:
            sql += " AND channel = ?"
            params.append(channel)
        if price_type:
            sql += " AND price_type = ?"
            params.append(price_type)
        sql += " ORDER BY effective_from DESC, created_at DESC"
        async with conn.execute(sql, tuple(params)) as cur:
            rows = await cur.fetchall()
        history_list = [dict(r) for r in rows]
        # Add previous_price_eur: price in effect before this row (so UI can show "from X to Y")
        if history_list:
            from helpers.pcr_helpers import get_current_price_eur
            import datetime
            for i, entry in enumerate(history_list):
                if i + 1 < len(history_list):
                    entry["previous_price_eur"] = history_list[i + 1].get("price_eur")
                else:
                    eff = entry.get("effective_from")
                    if eff:
                        try:
                            ref = datetime.date.fromisoformat(str(eff)[:10])
                            as_of = (ref - datetime.timedelta(days=1)).isoformat()
                            ta = (entry.get("therapeutic_area") or "").strip()
                            ch = (entry.get("channel") or "Retail").strip()
                            pt = (entry.get("price_type") or "").strip()
                            prev = await get_current_price_eur(sku_id, country, ta, ch, pt, as_of_date=as_of) if ta and ch and pt else None
                            entry["previous_price_eur"] = float(prev) if prev is not None else None
                        except ValueError:
                            entry["previous_price_eur"] = None
                    else:
                        entry["previous_price_eur"] = None
        return {
            "sku_id": sku_id,
            "country": country,
            "history": history_list,
        }
    finally:
        await conn.close()


@router.get("/countries/{country}/skus/{sku_id}/current-price")
async def get_sku_current_price(
    country: str = Path(..., description="Country code (e.g. IN)"),
    sku_id: str = Path(..., description="SKU ID"),
    therapeutic_area: str = Query("CMC", description="Therapeutic area (e.g. from PCR)"),
    channel: str = Query("Retail", description="Channel (e.g. Retail)"),
    price_type: str = Query("NSP Minimum", description="Price type (e.g. NSP Minimum, EXF)"),
):
    """Get current price for a SKU in the given country/TA/channel and price_type from sku_price_history (latest effective_from <= today)."""
    price_eur = await get_current_price_eur(sku_id, country, therapeutic_area, channel, price_type)
    if price_eur is None:
        raise HTTPException(status_code=404, detail=f"No current price found for SKU '{sku_id}' in country '{country}' (therapeutic_area={therapeutic_area}, channel={channel}, price_type={price_type})")
    return {
        "sku_id": sku_id,
        "country": country,
        "therapeutic_area": therapeutic_area,
        "channel": channel,
        "price_type": price_type,
        "current_price": str(price_eur),
    }


@router.get("/countries/{country}/skus/{sku_id}/prices")
async def get_sku_prices_all_channels(
    country: str = Path(..., description="Country code (e.g. IN)"),
    sku_id: str = Path(..., description="SKU ID"),
    therapeutic_area: str = Query(..., description="Therapeutic area (e.g. from PCR)"),
    price_type: str = Query(..., description="Price type (e.g. NSP Minimum, EXF)"),
):
    """Get current price for all channels for this SKU/country/TA and price_type.

    For each channel found in sku_mdgm_master, returns channel and current_price_eur.
    """
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            """
            SELECT DISTINCT channel
            FROM sku_mdgm_master
            WHERE sku_id = ? AND country = ? AND therapeutic_area = ? AND price_type = ?
            ORDER BY channel
            """,
            (sku_id, country, therapeutic_area, price_type),
        ) as cur:
            rows = await cur.fetchall()
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No channels defined for SKU '{sku_id}' in country '{country}' (therapeutic_area={therapeutic_area})",
            )
    finally:
        await conn.close()

    out = []
    for row in rows:
        channel = row["channel"]
        current_price = await get_current_price_eur(
            sku_id, country, therapeutic_area, channel, price_type
        )
        out.append(
            {
                "channel": channel,
                "current_price_eur": current_price,
            }
        )
    return {
        "sku_id": sku_id,
        "country": country,
        "therapeutic_area": therapeutic_area,
        "price_type": price_type,
        "prices": out,
    }
