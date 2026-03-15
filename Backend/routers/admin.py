"""Admin-only endpoints. Master data: Admin CRUD on sku_mdgm_master (create/update/delete SKU rows)."""
from typing import Optional
import sqlite3
from fastapi import APIRouter, Header, HTTPException, Query, Path, Body

router = APIRouter()
import database
from database import MDGM_COLS
from models import CreateMDGMRequest, UpdateMDGMRequest, AdminPCRUpdateRequest
from helpers.pcr_helpers import get_brand_from_mdgm
from notification_rules import notify_admin_action


async def _require_admin(x_user_id: int) -> None:
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (x_user_id,)) as cur:
            row = await cur.fetchone()
        if not row or row[0] != "Admin":
            raise HTTPException(status_code=403, detail="Only Admin users can perform this action")
    finally:
        await conn.close()


# ---- MDGM (sku_mdgm_master): Admin create/update/delete SKU rows ----


@router.get("/admin/mdgm")
async def list_mdgm(
    x_user_id: int = Header(..., alias="X-User-Id"),
    sku_id: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    therapeutic_area: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=500),
):
    """List MDGM rows with optional filters. Admin only."""
    await _require_admin(x_user_id)
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        conditions, params = [], []
        if sku_id:
            conditions.append("sku_id = ?")
            params.append(sku_id)
        if country:
            conditions.append("country = ?")
            params.append(country)
        if brand:
            conditions.append("brand = ?")
            params.append(brand)
        if therapeutic_area:
            conditions.append("therapeutic_area = ?")
            params.append(therapeutic_area)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        limit_clause = f" LIMIT {int(limit)}" if limit else ""
        async with conn.execute(
            f"SELECT {MDGM_COLS} FROM sku_mdgm_master{where} ORDER BY sku_id, country, channel, price_type{limit_clause}",
            tuple(params),
        ) as cur:
            rows = await cur.fetchall()
        return {"rows": [dict(r) for r in rows]}
    finally:
        await conn.close()


@router.post("/admin/mdgm", status_code=201)
async def create_mdgm(
    request: CreateMDGMRequest = Body(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """Create one MDGM row. Unique key (sku_id, country, channel, price_type). Duplicate returns 400. Admin only. All columns supported."""
    await _require_admin(x_user_id)
    conn = await database.get_connection()
    try:
        await conn.execute(
            """INSERT INTO sku_mdgm_master
               (country, region, therapeutic_area, brand, global_product_name, local_product_name, sku_id, pu, measure,
                dimension, volume_of_container, container, strength, currency, erp_applicable, pack_size,
                reimbursement_price_local, reimbursement_price_eur, reimbursement_status, reimbursement_rate,
                marketed_status, channel, price_type, current_price_eur)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request.country.strip(),
                request.region.strip() if request.region else None,
                request.therapeutic_area.strip(),
                request.brand.strip(),
                request.global_product_name.strip() if request.global_product_name else None,
                request.local_product_name.strip() if request.local_product_name else None,
                request.sku_id.strip(),
                request.pu,
                request.measure.strip() if request.measure else None,
                request.dimension.strip() if request.dimension else None,
                request.volume_of_container.strip() if request.volume_of_container else None,
                request.container.strip() if request.container else None,
                request.strength.strip() if request.strength else None,
                request.currency.strip() if request.currency else None,
                request.erp_applicable.strip() if request.erp_applicable else None,
                request.pack_size,
                request.reimbursement_price_local,
                request.reimbursement_price_eur,
                request.reimbursement_status.strip() if request.reimbursement_status else None,
                request.reimbursement_rate,
                request.marketed_status.strip() if request.marketed_status else None,
                request.channel.strip() or "Retail",
                request.price_type.strip() if request.price_type else None,
                request.current_price_eur,
            ),
        )
        await conn.commit()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        pt = request.price_type.strip() if request.price_type else None
        ch = request.channel.strip() or "Retail"
        if pt is None:
            async with conn.execute(
                f"SELECT {MDGM_COLS} FROM sku_mdgm_master WHERE sku_id = ? AND country = ? AND channel = ? AND price_type IS NULL ORDER BY id DESC LIMIT 1",
                (request.sku_id.strip(), request.country.strip(), ch),
            ) as cur:
                row = await cur.fetchone()
        else:
            async with conn.execute(
                f"SELECT {MDGM_COLS} FROM sku_mdgm_master WHERE sku_id = ? AND country = ? AND channel = ? AND price_type = ? ORDER BY id DESC LIMIT 1",
                (request.sku_id.strip(), request.country.strip(), ch, pt),
            ) as cur:
                row = await cur.fetchone()
        if row:
            created = dict(row)
            try:
                await notify_admin_action(
                    created.get("country"),
                    created.get("therapeutic_area"),
                    "addition",
                    f"SKU {created.get('sku_id', '')} added",
                    pcr_id=None,
                )
            except Exception:
                pass
            try:
                await database.log_audit(
                    user_id=x_user_id,
                    action="MDGM create",
                    entity_type="mdgm",
                    entity_id=str(created.get("id")),
                    brand=created.get("brand"),
                    country=created.get("country"),
                    details=None,
                    sku_ids=[created.get("sku_id")] if created.get("sku_id") else None,
                )
            except Exception:
                pass
            return created
        async with conn.execute("SELECT " + MDGM_COLS + " FROM sku_mdgm_master ORDER BY id DESC LIMIT 1") as cur:
            row = await cur.fetchone()
        fallback = dict(row) if row else {}
        if fallback:
            try:
                await notify_admin_action(
                    fallback.get("country"),
                    fallback.get("therapeutic_area"),
                    "addition",
                    f"SKU {fallback.get('sku_id', '')} added",
                    pcr_id=None,
                )
            except Exception:
                pass
            try:
                await database.log_audit(
                    user_id=x_user_id,
                    action="MDGM create",
                    entity_type="mdgm",
                    entity_id=str(fallback.get("id")),
                    brand=fallback.get("brand"),
                    country=fallback.get("country"),
                    details=None,
                    sku_ids=[fallback.get("sku_id")] if fallback.get("sku_id") else None,
                )
            except Exception:
                pass
        return fallback
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"A row for sku_id={request.sku_id!r}, country={request.country!r}, channel={request.channel!r}, price_type={request.price_type!r} already exists.",
            )
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await conn.close()


@router.put("/admin/mdgm/{row_id}")
async def update_mdgm(
    row_id: int = Path(...),
    request: UpdateMDGMRequest = Body(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """Update one MDGM row by id. Admin only. All columns supported; only provided fields are updated."""
    await _require_admin(x_user_id)
    updates, params = [], []
    # Build SET for every field that is not None (partial update)
    if request.sku_id is not None:
        updates.append("sku_id = ?")
        params.append(request.sku_id.strip())
    if request.country is not None:
        updates.append("country = ?")
        params.append(request.country.strip())
    if request.therapeutic_area is not None:
        updates.append("therapeutic_area = ?")
        params.append(request.therapeutic_area.strip())
    if request.brand is not None:
        updates.append("brand = ?")
        params.append(request.brand.strip())
    if request.channel is not None:
        updates.append("channel = ?")
        params.append(request.channel.strip())
    if request.price_type is not None:
        updates.append("price_type = ?")
        params.append(request.price_type.strip())
    if request.region is not None:
        updates.append("region = ?")
        params.append(request.region.strip())
    if request.global_product_name is not None:
        updates.append("global_product_name = ?")
        params.append(request.global_product_name.strip())
    if request.local_product_name is not None:
        updates.append("local_product_name = ?")
        params.append(request.local_product_name.strip())
    if request.pu is not None:
        updates.append("pu = ?")
        params.append(request.pu)
    if request.measure is not None:
        updates.append("measure = ?")
        params.append(request.measure.strip())
    if request.dimension is not None:
        updates.append("dimension = ?")
        params.append(request.dimension.strip())
    if request.volume_of_container is not None:
        updates.append("volume_of_container = ?")
        params.append(request.volume_of_container.strip())
    if request.container is not None:
        updates.append("container = ?")
        params.append(request.container.strip())
    if request.strength is not None:
        updates.append("strength = ?")
        params.append(request.strength.strip())
    if request.currency is not None:
        updates.append("currency = ?")
        params.append(request.currency.strip())
    if request.erp_applicable is not None:
        updates.append("erp_applicable = ?")
        params.append(request.erp_applicable.strip())
    if request.pack_size is not None:
        updates.append("pack_size = ?")
        params.append(request.pack_size)
    if request.reimbursement_price_local is not None:
        updates.append("reimbursement_price_local = ?")
        params.append(request.reimbursement_price_local)
    if request.reimbursement_price_eur is not None:
        updates.append("reimbursement_price_eur = ?")
        params.append(request.reimbursement_price_eur)
    if request.reimbursement_status is not None:
        updates.append("reimbursement_status = ?")
        params.append(request.reimbursement_status.strip())
    if request.reimbursement_rate is not None:
        updates.append("reimbursement_rate = ?")
        params.append(request.reimbursement_rate)
    if request.marketed_status is not None:
        updates.append("marketed_status = ?")
        params.append(request.marketed_status.strip())
    if request.current_price_eur is not None:
        updates.append("current_price_eur = ?")
        params.append(request.current_price_eur)
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    params.append(row_id)
    conn = await database.get_connection()
    try:
        async with conn.execute(f"SELECT {MDGM_COLS} FROM sku_mdgm_master WHERE id = ?", (row_id,)) as cur:
            existing = await cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="MDGM row not found")
        await conn.execute(
            "UPDATE sku_mdgm_master SET " + ", ".join(updates) + " WHERE id = ?",
            tuple(params),
        )
        await conn.commit()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(f"SELECT {MDGM_COLS} FROM sku_mdgm_master WHERE id = ?", (row_id,)) as cur:
            row = await cur.fetchone()
        updated = dict(row) if row else {}
        if updated:
            try:
                await notify_admin_action(
                    updated.get("country"),
                    updated.get("therapeutic_area"),
                    "update",
                    f"SKU {updated.get('sku_id', '')} updated",
                    pcr_id=None,
                )
            except Exception:
                pass
            try:
                await database.log_audit(
                    user_id=x_user_id,
                    action="MDGM update",
                    entity_type="mdgm",
                    entity_id=str(updated.get("id")),
                    brand=updated.get("brand"),
                    country=updated.get("country"),
                    details=None,
                    sku_ids=[updated.get("sku_id")] if updated.get("sku_id") else None,
                )
            except Exception:
                pass
        return updated
    finally:
        await conn.close()


@router.delete("/admin/mdgm/{row_id}")
async def delete_mdgm(
    row_id: int = Path(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """Delete one MDGM row by id. Admin only."""
    await _require_admin(x_user_id)
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(f"SELECT {MDGM_COLS} FROM sku_mdgm_master WHERE id = ?", (row_id,)) as cur:
            existing = await cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="MDGM row not found")
        existing_row = dict(existing)
        try:
            await notify_admin_action(
                existing_row.get("country"),
                existing_row.get("therapeutic_area"),
                "deletion",
                f"SKU {existing_row.get('sku_id', '')} removed",
                pcr_id=None,
            )
        except Exception:
            pass
        await conn.execute("DELETE FROM sku_mdgm_master WHERE id = ?", (row_id,))
        await conn.commit()
        try:
            await database.log_audit(
                user_id=x_user_id,
                action="MDGM delete",
                entity_type="mdgm",
                entity_id=str(row_id),
                brand=existing_row.get("brand"),
                country=existing_row.get("country"),
                details=None,
                sku_ids=[existing_row.get("sku_id")] if existing_row.get("sku_id") else None,
            )
        except Exception:
            pass
        return {"message": "MDGM row deleted", "id": row_id}
    finally:
        await conn.close()


# ---- Admin: PCR actions (delete, update status/fields) ----

@router.delete("/admin/pcrs/{pcr_id}")
async def admin_delete_pcr(
    pcr_id: str = Path(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """Delete a PCR. Admin only. Audit: PCR admin delete."""
    await _require_admin(x_user_id)
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            "SELECT pcr_id_display, country, therapeutic_area, product_skus FROM pcrs WHERE pcr_id_display = ?",
            (pcr_id,),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="PCR not found")
        row_d = dict(row)
        try:
            await notify_admin_action(
                row_d.get("country"),
                row_d.get("therapeutic_area"),
                "deletion",
                f"PCR {pcr_id} deleted",
                pcr_id=pcr_id,
            )
        except Exception:
            pass
        await conn.execute("DELETE FROM pcrs WHERE pcr_id_display = ?", (pcr_id,))
        await conn.commit()
        sku_list = [s.strip() for s in (row_d.get("product_skus") or "").split(",") if s.strip()] if row_d.get("product_skus") else []
        audit_brand = await get_brand_from_mdgm(sku_list[0], row_d.get("country"), row_d.get("therapeutic_area")) if sku_list and row_d.get("country") and row_d.get("therapeutic_area") else None
        try:
            await database.log_audit(
                user_id=x_user_id,
                action="PCR admin delete",
                entity_type="pcr",
                entity_id=pcr_id,
                brand=audit_brand,
                country=row_d.get("country"),
                details=None,
                sku_ids=sku_list or None,
            )
        except Exception:
            pass
        return {"message": "PCR deleted", "pcr_id": pcr_id}
    finally:
        await conn.close()


@router.put("/admin/pcrs/{pcr_id}")
async def admin_update_pcr(
    pcr_id: str = Path(...),
    request: AdminPCRUpdateRequest = Body(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """Update a PCR (status or other fields). Admin only. Audit: PCR admin update."""
    await _require_admin(x_user_id)
    updates, params = [], []
    if request.status is not None:
        updates.append("status = ?")
        params.append(request.status.strip())
    if request.proposed_price is not None:
        updates.append("proposed_price = ?")
        params.append(request.proposed_price.strip())
    if request.product_name is not None:
        updates.append("product_name = ?")
        params.append(request.product_name.strip())
    if request.product_id is not None:
        updates.append("product_id = ?")
        params.append(request.product_id.strip())
    if request.current_price is not None:
        updates.append("current_price = ?")
        params.append(request.current_price.strip())
    if request.country is not None:
        updates.append("country = ?")
        params.append(request.country.strip())
    if request.therapeutic_area is not None:
        updates.append("therapeutic_area = ?")
        params.append(request.therapeutic_area.strip())
    if request.product_skus is not None:
        updates.append("product_skus = ?")
        params.append(request.product_skus.strip())
    if request.channel is not None:
        updates.append("channel = ?")
        params.append(request.channel.strip())
    if request.price_type is not None:
        updates.append("price_type = ?")
        params.append(request.price_type.strip())
    if request.effective_date is not None:
        updates.append("effective_date = ?")
        params.append(request.effective_date.strip())
    if request.price_change_reason is not None:
        updates.append("price_change_reason = ?")
        params.append(request.price_change_reason.strip())
    if request.price_change_reason_comments is not None:
        updates.append("price_change_reason_comments = ?")
        params.append(request.price_change_reason_comments.strip())
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        # Disallow editing finalised PCRs: any further change must go via a new PCR
        async with conn.execute(
            "SELECT status, country, therapeutic_area, product_skus FROM pcrs WHERE pcr_id_display = ?",
            (pcr_id,),
        ) as cur:
            existing = await cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="PCR not found")
        if (existing.get("status") or "").strip() == "finalised":
            raise HTTPException(
                status_code=400,
                detail="Finalised PCRs cannot be edited. Create a new PCR for further changes.",
            )
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(pcr_id)
        await conn.execute(
            "UPDATE pcrs SET " + ", ".join(updates) + " WHERE pcr_id_display = ?",
            tuple(params),
        )
        await conn.commit()
        async with conn.execute(
            "SELECT country, therapeutic_area, product_skus FROM pcrs WHERE pcr_id_display = ?",
            (pcr_id,),
        ) as cur:
            after = await cur.fetchone()
        pcr_country = after.get("country") if after else existing.get("country")
        pcr_ta = after.get("therapeutic_area") if after else existing.get("therapeutic_area")
        product_skus_str = after.get("product_skus") if after else existing.get("product_skus")
        sku_list = [s.strip() for s in (product_skus_str or "").split(",") if s.strip()] if product_skus_str else []
        audit_brand = await get_brand_from_mdgm(sku_list[0], pcr_country, pcr_ta) if sku_list and pcr_country and pcr_ta else None
        details = "Admin updated: " + ", ".join(f.replace(" = ?", "") for f in updates if f != "updated_at = CURRENT_TIMESTAMP")
        try:
            await notify_admin_action(
                pcr_country,
                pcr_ta,
                "update",
                f"PCR {pcr_id} updated",
                pcr_id=pcr_id,
            )
        except Exception:
            pass
        try:
            await database.log_audit(
                user_id=x_user_id,
                action="PCR admin update",
                entity_type="pcr",
                entity_id=pcr_id,
                brand=audit_brand,
                country=pcr_country,
                details=details,
                sku_ids=sku_list or None,
            )
        except Exception:
            pass
        return {"message": "PCR updated by Admin", "pcr_id": pcr_id}
    finally:
        await conn.close()
