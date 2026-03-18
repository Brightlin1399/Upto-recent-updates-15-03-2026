from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, Header, HTTPException, Path, Body
import database
from helpers.pcr_helpers import get_therapeutic_area_for_brand, from_eur_to, get_current_price_eur
from models import UpdateReimbVatRequest

router = APIRouter()


# ---------- Helpers ----------

async def _get_user_scope(user_id: int) -> dict | None:
    """Return {user_id, role, region, therapeutic_areas} for the user, or None if not found.
    therapeutic_areas comes from user_therapeutic_areas only."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            "SELECT id AS user_id, role, region FROM users WHERE id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return None
        out = dict(row)
        async with conn.execute(
            "SELECT therapeutic_area FROM user_therapeutic_areas WHERE user_id = ? ORDER BY therapeutic_area",
            (user_id,),
        ) as cur:
            tas = await cur.fetchall()
        out["therapeutic_areas"] = [t["therapeutic_area"] for t in tas] if tas else []
        return out
    finally:
        await conn.close()


async def _is_country_user_for(user_id: int | None, country: str | None) -> bool:
    """True if user is Local and has this country in user_countries (can edit reimb/VAT on product page)."""
    if not user_id or not (country or "").strip():
        return False
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT 1 FROM users u JOIN user_countries uc ON uc.user_id = u.id WHERE u.id = ? AND u.role = 'Local' AND uc.country = ? LIMIT 1",
            (user_id, (country or "").strip()),
        ) as cur:
            return (await cur.fetchone()) is not None
    finally:
        await conn.close()


# ---------- Filters (left sidebar) ----------

@router.get("/product-360/regions")
async def list_regions(
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """List regions for the filter. Product 360 is visible to all (Local/Regional/Global) for all countries; all roles see all regions."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute("SELECT code, name FROM regions ORDER BY name") as cur:
            rows = await cur.fetchall()
        return {"regions": [dict(r) for r in rows]}
    finally:
        await conn.close()


@router.get("/product-360/countries")
async def list_countries(
    region: str = Query(None, description="Optional: filter by region code (e.g. APAC, EMEA)"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """List countries. Product 360 is visible to all (Local/Regional/Global) for all countries; all roles see all countries (optionally filtered by region)."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        if region:
            async with conn.execute(
                "SELECT code, name, region FROM countries WHERE region = ? ORDER BY name",
                (region,),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with conn.execute(
                "SELECT code, name, region FROM countries ORDER BY name"
            ) as cur:
                rows = await cur.fetchall()
        return {"countries": [dict(r) for r in rows]}
    finally:
        await conn.close()


@router.get("/product-360/therapeutic-areas")
async def list_therapeutic_areas(
    region: Optional[str] = Query(None, description="Optional: filter by region (only TAs with marketed data in that region)"),
    country: Optional[str] = Query(None, description="Optional: filter by country (only TAs with marketed data in that country)"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """List therapeutic areas. Product 360 is visible to all for all countries; all roles see all TAs (optionally filtered by region/country)."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        if country:
            async with conn.execute(
                """SELECT DISTINCT m.therapeutic_area
                   FROM sku_mdgm_master m
                   WHERE m.country = ?
                   ORDER BY m.therapeutic_area""",
                (country.strip(),),
            ) as cur:
                rows = await cur.fetchall()
        elif region:
            async with conn.execute(
                """SELECT DISTINCT m.therapeutic_area
                   FROM sku_mdgm_master m
                   LEFT JOIN countries c ON c.code = m.country
                   WHERE (m.region = ? OR c.region = ?)
                   ORDER BY m.therapeutic_area""",
                (region.strip(), region.strip()),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with conn.execute(
                """SELECT DISTINCT therapeutic_area FROM sku_mdgm_master
                   ORDER BY therapeutic_area""",
            ) as cur:
                rows = await cur.fetchall()
        return {"therapeutic_areas": [{"therapeutic_area": r["therapeutic_area"]} for r in rows]}
    finally:
        await conn.close()


@router.get("/product-360/brands")
async def list_brands(
    country: str = Query(..., description="Country code. Returns only brands that have data for this country."),
    therapeutic_area: Optional[str] = Query(None, description="Optional: filter by therapeutic area (Region → Country → TA → Brand)."),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """
    List brands for the selected country. Product 360 is visible to all (Local/Regional/Global) for all countries.
    """
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        if therapeutic_area:
            async with conn.execute(
                """SELECT DISTINCT m.brand, m.therapeutic_area
                   FROM sku_mdgm_master m
                   WHERE m.therapeutic_area = ?
                   AND (EXISTS (SELECT 1 FROM sku_mdgm_master m2 WHERE m2.brand = m.brand AND m2.country = ? AND m2.therapeutic_area = ?)
                        OR EXISTS (SELECT 1 FROM pcrs p WHERE p.therapeutic_area = m.therapeutic_area AND p.country = ?))
                   ORDER BY m.brand""",
                (therapeutic_area, country, therapeutic_area, country),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with conn.execute(
                """SELECT DISTINCT m.brand, m.therapeutic_area
                   FROM sku_mdgm_master m
                   WHERE EXISTS (SELECT 1 FROM sku_mdgm_master m2 WHERE m2.brand = m.brand AND m2.country = ?)
                   OR EXISTS (SELECT 1 FROM pcrs p WHERE p.therapeutic_area = m.therapeutic_area AND p.country = ?)
                   ORDER BY m.brand""",
                (country, country),
            ) as cur:
                rows = await cur.fetchall()
        return {"country": country, "therapeutic_area": therapeutic_area, "brands": [dict(r) for r in rows]}
    finally:
        await conn.close()


@router.get("/product-360/skus")
async def list_skus(
    brand: str = Query(..., description="Brand name"),
    country: str = Query(..., description="Country code"),
    therapeutic_area: Optional[str] = Query(None, description="Optional: filter by therapeutic area (only SKUs in this TA for this brand+country)."),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """List SKUs for brand + country. Product 360 is visible to all (Local/Regional/Global) for all countries."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        if therapeutic_area:
            async with conn.execute(
                """SELECT DISTINCT sku_id FROM sku_mdgm_master
                   WHERE brand = ? AND country = ? AND therapeutic_area = ?
                   ORDER BY sku_id""",
                (brand, country, therapeutic_area),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with conn.execute(
                """SELECT DISTINCT sku_id FROM sku_mdgm_master
                   WHERE brand = ? AND country = ?
                   ORDER BY sku_id""",
                (brand, country),
            ) as cur:
                rows = await cur.fetchall()
        skus = [r["sku_id"] for r in rows]
        return {"brand": brand, "country": country, "therapeutic_area": therapeutic_area, "skus": skus}
    finally:
        await conn.close()

@router.get("/product-360/overview")
async def get_overview(
    brand: str = Query(..., description="Brand name"),
    country: Optional[str] = Query(None, description="Optional country filter (e.g. IN)."),
    region: Optional[str] = Query(None, description="Optional region filter if no country (e.g. APAC)."),
    therapeutic_area: Optional[str] = Query(None, description="Optional: filter by therapeutic area (Region → Country → TA → Brand)."),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """
    Overview tab for Product 360.
    - Left: region → country → brand (filters).
    - Center map: always show all countries where this brand is marketed (countries_marketed).
    - Right: product hierarchy + Price Request # for the selected country (pcr_count for that country).
    Product 360 is visible to all (Local/Regional/Global) for all countries.
    """
    if country and "|" in country:
        country = country.split("|")[0].strip() or None
    if region and "|" in region:
        region = region.split("|")[0].strip() or None
    effective_ta = therapeutic_area or await get_therapeutic_area_for_brand(brand)

    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        # 1) Countries where this brand has SKUs (marketed or non-marketed) for the center map. Optional therapeutic_area filter.
        if therapeutic_area:
            async with conn.execute(
                """SELECT DISTINCT m.country AS country, COALESCE(m.region, c.region) AS region
                   FROM sku_mdgm_master m
                   LEFT JOIN countries c ON c.code = m.country
                   WHERE m.brand = ? AND m.therapeutic_area = ?                    
                   ORDER BY m.country""",
                (brand, therapeutic_area),
            ) as cur:
                countries_marketed = await cur.fetchall()
        else:
            async with conn.execute(
                """SELECT DISTINCT m.country AS country, COALESCE(m.region, c.region) AS region
                   FROM sku_mdgm_master m
                   LEFT JOIN countries c ON c.code = m.country
                   WHERE m.brand = ?                    
                   ORDER BY m.country""",
                (brand,),
            ) as cur:
                countries_marketed = await cur.fetchall()

        # 2) PCR counts per country (filter by brand's therapeutic_area; no brand_therapeutic_area table)
        if effective_ta:
            if country:
                async with conn.execute(
                    """SELECT p.country, c.region AS region, COUNT(*) AS pcr_count
                       FROM pcrs p
                       LEFT JOIN countries c ON c.code = p.country
                       WHERE p.therapeutic_area = ? AND p.country = ?
                       GROUP BY p.country, c.region""",
                    (effective_ta, country),
                ) as cur:
                    pcr_counts = await cur.fetchall()
            else:
                async with conn.execute(
                    """SELECT p.country, c.region AS region, COUNT(*) AS pcr_count
                       FROM pcrs p
                       LEFT JOIN countries c ON c.code = p.country
                       WHERE p.therapeutic_area = ?
                       GROUP BY p.country, c.region""",
                    (effective_ta,),
                ) as cur:
                    pcr_counts = await cur.fetchall()
        else:
            pcr_counts = []

        out = {
            "brand": brand,
            "therapeutic_area": therapeutic_area,
            "countries_marketed": [dict(r) for r in countries_marketed],
            "pcr_count_by_country": [dict(r) for r in pcr_counts],
        }
        if country:
            out["selected_country"] = {"country": country, "region": None}
            async with conn.execute("SELECT region FROM countries WHERE code = ?", (country,)) as cur:
                row = await cur.fetchone()
            if row:
                out["selected_country"]["region"] = row["region"]
        return out
    finally:
        await conn.close()


@router.get("/product-360/pricing")
async def get_pricing(
    brand: str = Query(..., description="Brand name"),
    country: str = Query(..., description="Country code"),
    therapeutic_area: Optional[str] = Query(None, description="Optional: filter by therapeutic area (uses brand's TA if not provided)."),
    currency: Optional[str] = Query(None, description="Target currency for bracketed value (e.g. EUR, USD, BAM)"),
    target_fx_date: Optional[str] = Query(None, description="Date for FX rate (YYYY-MM-DD); used with currency for bracketed price"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """
    Pricing tab: one row per (SKU, channel, price_type) for this brand + country.
    Product 360 is visible to all (Local/Regional/Global) for all countries.
    """
    currency = currency.strip() if currency else None
    target_fx_date = target_fx_date.strip() if target_fx_date else None
    if currency and target_fx_date:
        try:
            date.fromisoformat(target_fx_date.strip())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="target_fx_date must be YYYY-MM-DD (e.g. 2026-03-03)",
            )
    if not therapeutic_area:
        therapeutic_area = await get_therapeutic_area_for_brand(brand)
    if not therapeutic_area:
        return {"brand": brand, "country": country, "therapeutic_area": None, "pricing": []}

    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        # 1) SKUs for this brand + country (+ therapeutic_area when provided)
        if therapeutic_area:
            async with conn.execute(
                """SELECT DISTINCT sku_id FROM sku_mdgm_master
                   WHERE brand = ? AND country = ? AND therapeutic_area = ? ORDER BY sku_id""",
                (brand, country, therapeutic_area),
            ) as cur:
                sku_rows = await cur.fetchall()
        else:
            async with conn.execute(
                """SELECT DISTINCT sku_id FROM sku_mdgm_master
                   WHERE brand = ? AND country = ? ORDER BY sku_id""",
                (brand, country),
            ) as cur:
                sku_rows = await cur.fetchall()
        sku_ids = [r["sku_id"] for r in sku_rows]
        if not sku_ids:
            return {"brand": brand, "country": country, "therapeutic_area": therapeutic_area, "pricing": []}

        placeholders = ",".join("?" * len(sku_ids))

        # 2) Base rows from MDGM: one per SKU/channel/price_type with currency (filter by therapeutic_area)
        if therapeutic_area:
            async with conn.execute(
                f"""
                SELECT sku_id, channel, price_type, currency
                FROM sku_mdgm_master
                WHERE brand = ? AND country = ? AND therapeutic_area = ? AND sku_id IN ({placeholders})
                ORDER BY sku_id, channel, price_type
                """,
                (brand, country, therapeutic_area, *sku_ids),
            ) as cur:
                mdgm_rows = await cur.fetchall()
        else:
            async with conn.execute(
                f"""
                SELECT sku_id, channel, price_type, currency
                FROM sku_mdgm_master
                WHERE brand = ? AND country = ? AND sku_id IN ({placeholders})
                ORDER BY sku_id, channel, price_type
                """,
                (brand, country, *sku_ids),
            ) as cur:
                mdgm_rows = await cur.fetchall()

        # 3) Build pricing rows (currency comes from each MDGM row)
        use_target_currency = currency and target_fx_date
        pricing = []
        for r in mdgm_rows:
            sku_id = r["sku_id"]
            channel = r["channel"]
            price_type = r["price_type"]
            if not price_type:
                continue

            current_eur = await get_current_price_eur(
                sku_id, country, therapeutic_area, channel, price_type
            )
            row = {
                "sku_id": sku_id,
                "channel": channel,
                "price_type": price_type,
                "current_price_eur": current_eur,
                "currency": r.get("currency") or "EUR",
            }
            if use_target_currency:
                row["current_price_in_target"] = await from_eur_to(
                    current_eur, currency, target_fx_date
                )
                row["target_currency"] = currency.upper()
                row["target_fx_date"] = target_fx_date
            pricing.append(row)

        out = {
            "brand": brand,
            "country": country,
            "therapeutic_area": therapeutic_area,
            "pricing": pricing,
        }
        if use_target_currency:
            out["target_currency"] = currency.upper()
            out["target_fx_date"] = target_fx_date
        return out
    finally:
        await conn.close()


async def _skus_with_current_price_flag(
    brand: str,
    country: str,
    therapeutic_area: str,
    channel: str,
    price_type: Optional[str],
) -> list[dict]:
    """
    Return list of {"sku_id": ..., "has_current_price": bool} for brand+country+TA+channel+price_type.
    Uses the same current-price logic as PCR submit (history → MDGM fallback).
    """
    conn = await database.get_connection()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    try:
        async with conn.execute(
            """
            SELECT DISTINCT sku_id
            FROM sku_mdgm_master
            WHERE brand = ? AND country = ? AND therapeutic_area = ?
            ORDER BY sku_id
            """,
            (brand, country, therapeutic_area),
        ) as cur:
            sku_rows = await cur.fetchall()
        sku_ids = [r["sku_id"] for r in sku_rows]
        if not sku_ids:
            return []

        flags: list[dict] = []
        ch = (channel or "Retail").strip()
        pt = price_type.strip() if price_type else None
        for sku in sku_ids:
            current = await get_current_price_eur(
                sku_id=sku,
                country=country,
                therapeutic_area=therapeutic_area,
                channel=ch,
                price_type=pt,
            )
            flags.append({"sku_id": sku, "has_current_price": current is not None})
        return flags
    finally:
        await conn.close()


@router.get("/product-360/eligible-skus")
async def get_eligible_skus_for_price_change(
    brand: str = Query(..., description="Brand name"),
    country: str = Query(..., description="Country code"),
    therapeutic_area: str = Query(..., description="Therapeutic area"),
    channel: str = Query("Retail", description="Channel, default Retail"),
    price_type: Optional[str] = Query(None, description="Price type (e.g. NSP Minimum)"),
    price_change_type: str = Query(..., description="Price Change Type selected in PCR (e.g. New Product Launch)"),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """
    Eligible SKUs for Create PCR, partitioned by whether they have a current price.

    Frontend logic:
      - New Product Launch       -> use skus_without_price
      - Other price-change types -> use skus_with_price
    Product 360 is visible to all for all countries; no country access check here.
    """
    sku_flags = await _skus_with_current_price_flag(
        brand=brand,
        country=country,
        therapeutic_area=therapeutic_area,
        channel=channel,
        price_type=price_type,
    )
    skus_with_price = [r["sku_id"] for r in sku_flags if r["has_current_price"]]
    skus_without_price = [r["sku_id"] for r in sku_flags if not r["has_current_price"]]

    return {
        "brand": brand,
        "country": country,
        "therapeutic_area": therapeutic_area,
        "channel": channel,
        "price_type": price_type,
        "price_change_type": price_change_type,
        "skus_with_price": skus_with_price,
        "skus_without_price": skus_without_price,
    }


@router.get("/product-360/mdgm-details")
async def get_mdgm_details(
    brand: str = Query(..., description="Brand name"),
    country: str = Query(..., description="Country code"),
    therapeutic_area: Optional[str] = Query(None, description="Optional: filter by therapeutic area"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """
    SKU-MDGM DETAILS tab: MDGM rows for this brand + country.
    Product 360 is visible to all (Local/Regional/Global) for all countries.
    """
    ta = therapeutic_area or await get_therapeutic_area_for_brand(brand)
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        from database import MDGM_COLS
        if therapeutic_area:
            async with conn.execute(
                f"""SELECT {MDGM_COLS} FROM sku_mdgm_master
                   WHERE brand = ? AND country = ? AND therapeutic_area = ?
                   ORDER BY sku_id, channel, price_type""",
                (brand, country, therapeutic_area),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with conn.execute(
                f"""SELECT {MDGM_COLS} FROM sku_mdgm_master
                   WHERE brand = ? AND country = ?
                   ORDER BY sku_id, channel, price_type""",
                (brand, country),
            ) as cur:
                rows = await cur.fetchall()
        out_rows = []
        for r in rows:
            row = dict(r)
            sku_id = row["sku_id"]
            ch = row["channel"]
            pt = row.get("price_type")
            if ta and pt:
                current_eur = await get_current_price_eur(sku_id, country, ta, ch, pt)
                row["current_price_eur"] = current_eur
            out_rows.append(row)
        reimb_vat_editable_by_user = await _is_country_user_for(x_user_id, country) if x_user_id else False
        return {
            "brand": brand,
            "country": country,
            "therapeutic_area": therapeutic_area,
            "rows": out_rows,
            "reimb_vat_editable_by_user": reimb_vat_editable_by_user,
        }
    finally:
        await conn.close()


@router.patch("/product-360/mdgm-row/{row_id}/reimb-vat")
async def update_mdgm_reimb_vat(
    row_id: int = Path(..., description="MDGM row id"),
    request: UpdateReimbVatRequest = Body(...),
    x_user_id: int = Header(..., alias="X-User-Id"),
):
    """
    Update only reimbursement and VAT fields on an MDGM row. Allowed only for country users
    (Local users with this row's country in user_countries). Used from Product page SKU-MDGM tab.
    """
    conn = await database.get_connection()
    try:
        from database import MDGM_COLS
        async with conn.execute(
            f"SELECT id, country FROM sku_mdgm_master WHERE id = ?",
            (row_id,),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="MDGM row not found")
        row_country = (row[1] or "").strip() if len(row) > 1 else ""
        if not await _is_country_user_for(x_user_id, row_country):
            raise HTTPException(
                status_code=403,
                detail="Only country users (Local users assigned to this country) can edit reimbursement and VAT on the product page.",
            )
        updates, params = [], []
        if request.reimbursement_price_local is not None:
            updates.append("reimbursement_price_local = ?")
            params.append(request.reimbursement_price_local)
        if request.reimbursement_price_eur is not None:
            updates.append("reimbursement_price_eur = ?")
            params.append(request.reimbursement_price_eur)
        if request.reimbursement_status is not None:
            updates.append("reimbursement_status = ?")
            params.append(request.reimbursement_status.strip())
        if request.reimbursement_type is not None:
            updates.append("reimbursement_type = ?")
            params.append(request.reimbursement_type.strip())
        if request.reimbursement_rate is not None:
            updates.append("reimbursement_rate = ?")
            params.append(request.reimbursement_rate)
        if request.vat_rate is not None:
            updates.append("vat_rate = ?")
            params.append(request.vat_rate)
        if not updates:
            raise HTTPException(status_code=400, detail="Provide at least one reimb or VAT field to update")
        params.append(row_id)
        await conn.execute(
            "UPDATE sku_mdgm_master SET " + ", ".join(updates) + " WHERE id = ?",
            tuple(params),
        )
        await conn.commit()
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(f"SELECT {MDGM_COLS} FROM sku_mdgm_master WHERE id = ?", (row_id,)) as cur:
            updated_row = await cur.fetchone()
        out = dict(updated_row) if updated_row else {}
        try:
            await database.log_audit(
                user_id=x_user_id,
                action="MDGM reimb/VAT update (country user)",
                entity_type="mdgm",
                entity_id=str(row_id),
                brand=out.get("brand"),
                country=out.get("country"),
                details=None,
                sku_ids=[out.get("sku_id")] if out.get("sku_id") else None,
            )
        except Exception:
            pass
        return {"message": "Reimbursement/VAT updated", "id": row_id, "row": out}
    finally:
        await conn.close()


@router.get("/product-360/audit-trail")
async def get_audit_trail(
    x_user_id: int = Header(..., alias="X-User-Id"),
    brand: Optional[str] = Query(None, description="Filter by brand (product name)"),
    country: Optional[str] = Query(None, description="Filter by country"),
    sku_id: Optional[str] = Query(None, description="When selecting a SKU: return only that SKU's audit log"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Optional max entries; omit to return all"),
):
    """
    AUDIT TRAIL tab in Product 360. Product 360 is visible to all (Local/Regional/Global) for all countries.
    Filters: brand (exact or prefix), country, sku_id.
    """
    scope = await _get_user_scope(x_user_id)
    if not scope:
        raise HTTPException(status_code=400, detail="User not found")
    conditions: list[str] = []
    params: list = []
    # Brand filter (same as before)
    if brand:
        conditions.append("(a.brand = ? OR a.brand LIKE ?)")
        params.extend([brand, brand + "%"])
    # SKU filter (same as before)
    if sku_id:
        conditions.append("a.sku_id = ?")
        params.append(sku_id)
    # Country filter (Product 360 visible to all for all countries; no scope restriction)
    if country:
        conditions.append("a.country = ?")
        params.append(country)
    # Optional limit
    limit_clause = ""
    if limit is not None:
        limit_clause = " LIMIT ?"
        params.append(limit)
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    q = (
        """SELECT a.id, a.created_at, a.user_id, a.action, a.entity_type, a.entity_id, a.brand, a.country, a.details, a.sku_id,
           u.name AS user_name, u.email AS user_email
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id"""
        + where_clause
        + " ORDER BY a.created_at DESC"
        + limit_clause
    )
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(q, tuple(params)) as cur:
            rows = await cur.fetchall()
        return {"audit_entries": [dict(r) for r in rows]}
    finally:
        await conn.close()