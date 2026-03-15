from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, Header, HTTPException
import database
from helpers.pcr_helpers import get_therapeutic_area_for_brand, from_eur_to, get_current_price_eur

router = APIRouter()


# ---------- Helpers ----------

async def _require_admin(x_user_id: int) -> None:
    """Raise 403 if the user is not Admin. Used for Audit tab."""
    conn = await database.get_connection()
    try:
        async with conn.execute("SELECT role FROM users WHERE id = ?", (x_user_id,)) as cur:
            row = await cur.fetchone()
        if not row or row[0] != "Admin":
            raise HTTPException(status_code=403, detail="Audit Trail is only available to Admin users")
    finally:
        await conn.close()


async def _get_user_scope(user_id: int) -> dict | None:
    """Return {user_id, role, therapeutic_area, region} for the user, or None if not found.
    Used to enforce visibility: Local sees only their assigned countries, Regional only their region, Global/Admin see all."""
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        async with conn.execute(
            "SELECT id AS user_id, role, therapeutic_area, region FROM users WHERE id = ?",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def _ensure_can_access_country(scope: dict | None, country: str | None) -> None:
    """Raise 403 if scope is set and user cannot access this country."""
    if not scope or not country or not (country or "").strip():
        return
    role = (scope.get("role") or "").strip()
    if role in ("Admin", "Global"):
        return
    country = (country or "").strip()
    user_id = scope.get("user_id")
    if role == "Local":
        # Local: must have this country in user_countries
        conn = await database.get_connection()
        try:
            async with conn.execute(
                "SELECT 1 FROM user_countries WHERE user_id = ? AND country = ? LIMIT 1",
                (user_id, country),
            ) as cur:
                if not await cur.fetchone():
                    raise HTTPException(
                        status_code=403,
                        detail="You can only access data for your assigned countries",
                    )
        finally:
            await conn.close()
        return
    if role == "Regional":
        # Regional: country must be in their region (via countries table)
        conn = await database.get_connection()
        try:
            async with conn.execute(
                "SELECT 1 FROM countries WHERE code = ? AND region = ?",
                (country, (scope.get("region") or "").strip()),
            ) as cur:
                if not await cur.fetchone():
                    raise HTTPException(
                        status_code=403,
                        detail="You can only access data for countries in your region",
                    )
        finally:
            await conn.close()


# ---------- Filters (left sidebar) ----------

@router.get("/product-360/regions")
async def list_regions(
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """List regions for the filter. Send X-User-Id to restrict: Local sees only their country's region, Regional only their region, Admin/Global see all."""
    scope = await _get_user_scope(x_user_id) if x_user_id else None
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        if scope:
            role = (scope.get("role") or "").strip()
            user_id = scope.get("user_id")
            if role == "Local":
                # Regions for which the user has at least one assigned country
                async with conn.execute(
                    """SELECT DISTINCT r.code, r.name
                       FROM regions r
                       JOIN countries c ON c.region = r.code
                       JOIN user_countries uc ON uc.country = c.code
                       WHERE uc.user_id = ?
                       ORDER BY r.name""",
                    (user_id,),
                ) as cur:
                    rows = await cur.fetchall()
            elif role == "Regional":
                user_region = (scope.get("region") or "").strip()
                if user_region:
                    async with conn.execute(
                        "SELECT code, name FROM regions WHERE code = ? ORDER BY name",
                        (user_region,),
                    ) as cur:
                        rows = await cur.fetchall()
                else:
                    async with conn.execute("SELECT code, name FROM regions ORDER BY name") as cur:
                        rows = await cur.fetchall()
            else:
                async with conn.execute("SELECT code, name FROM regions ORDER BY name") as cur:
                    rows = await cur.fetchall()
        else:
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
    """List countries.
    Visibility:
      - Local: only countries assigned in user_countries.
      - Regional: only countries in their region.
      - Global/Admin/anonymous: all countries (optionally filtered by region).
    """
    scope = await _get_user_scope(x_user_id) if x_user_id else None
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        if scope:
            role = (scope.get("role") or "").strip()
            user_id = scope.get("user_id")
            user_region = (scope.get("region") or "").strip()
            if role == "Local":
                # Local: only assigned countries from user_countries
                if region:
                    async with conn.execute(
                        """SELECT c.code, c.name, c.region
                           FROM countries c
                           JOIN user_countries uc ON uc.country = c.code
                           WHERE uc.user_id = ? AND c.region = ?
                           ORDER BY c.name""",
                        (user_id, region),
                    ) as cur:
                        rows = await cur.fetchall()
                else:
                    async with conn.execute(
                        """SELECT c.code, c.name, c.region
                           FROM countries c
                           JOIN user_countries uc ON uc.country = c.code
                           WHERE uc.user_id = ?
                           ORDER BY c.name""",
                        (user_id,),
                    ) as cur:
                        rows = await cur.fetchall()
            elif role == "Regional":
                # Regional: only countries in their region
                effective_region = region.strip() if region else user_region
                if not effective_region:
                    # No region info; fallback to all countries (unlikely)
                    async with conn.execute(
                        "SELECT code, name, region FROM countries ORDER BY name"
                    ) as cur:
                        rows = await cur.fetchall()
                else:
                    async with conn.execute(
                        "SELECT code, name, region FROM countries WHERE region = ? ORDER BY name",
                        (effective_region,),
                    ) as cur:
                        rows = await cur.fetchall()
            else:
                # Global/Admin: all countries (optionally filtered by region)
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
        else:
            # No user scope: return all countries (optionally filtered by region)
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
    """List therapeutic areas. Send X-User-Id: Local sees only TAs for their country, Regional for their region's countries; Local/Regional are scoped to their TA when set."""
    scope = await _get_user_scope(x_user_id) if x_user_id else None
    conn = await database.get_connection()
    try:
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        if scope:
            role = (scope.get("role") or "").strip()
            user_id = scope.get("user_id")
            if role == "Local":
                # Local: country must be one of their assigned countries (if specified)
                requested_country = (country or "").strip()
                if requested_country:
                    conn_check = await database.get_connection()
                    try:
                        async with conn_check.execute(
                            "SELECT 1 FROM user_countries WHERE user_id = ? AND country = ? LIMIT 1",
                            (user_id, requested_country),
                        ) as cur2:
                            if not await cur2.fetchone():
                                raise HTTPException(
                                    status_code=403,
                                    detail="You can only view therapeutic areas for your assigned countries",
                                )
                    finally:
                        await conn_check.close()
                effective_country = requested_country or None

                if effective_country:
                    async with conn.execute(
                        """SELECT DISTINCT m.therapeutic_area
                           FROM sku_mdgm_master m
                           WHERE m.country = ?
                           ORDER BY m.therapeutic_area""",
                        (effective_country,),
                    ) as cur:
                        rows = await cur.fetchall()
                else:
                    # All TAs across all assigned countries
                    async with conn.execute(
                        """SELECT DISTINCT m.therapeutic_area
                           FROM sku_mdgm_master m
                           WHERE m.country IN (SELECT country FROM user_countries WHERE user_id = ?)
                           ORDER BY m.therapeutic_area""",
                        (user_id,),
                    ) as cur:
                        rows = await cur.fetchall()
            elif role == "Regional":
                user_region = (scope.get("region") or "").strip()
                if country and user_region:
                    async with conn.execute(
                        "SELECT 1 FROM countries WHERE code = ? AND region = ?",
                        (country.strip(), user_region),
                    ) as cur:
                        if not await cur.fetchone():
                            raise HTTPException(status_code=403, detail="You can only view therapeutic areas for countries in your region")
                if country:
                    async with conn.execute(
                        """SELECT DISTINCT m.therapeutic_area
                           FROM sku_mdgm_master m
                           WHERE m.country = ?                            
                           ORDER BY m.therapeutic_area""",
                        (country,),
                    ) as cur:
                        rows = await cur.fetchall()
                elif user_region:
                    async with conn.execute(
                        """SELECT DISTINCT m.therapeutic_area
                           FROM sku_mdgm_master m
                           LEFT JOIN countries c ON c.code = m.country
                           WHERE (m.region = ? OR c.region = ?)                            
                           ORDER BY m.therapeutic_area""",
                        (user_region, user_region),
                    ) as cur:
                        rows = await cur.fetchall()
                else:
                    async with conn.execute(
                        """SELECT DISTINCT therapeutic_area FROM sku_mdgm_master
                           ORDER BY therapeutic_area""",
                    ) as cur:
                        rows = await cur.fetchall()
            else:
                if country:
                    async with conn.execute(
                        """SELECT DISTINCT m.therapeutic_area
                           FROM sku_mdgm_master m
                           WHERE m.country = ?                            
                           ORDER BY m.therapeutic_area""",
                        (country,),
                    ) as cur:
                        rows = await cur.fetchall()
                elif region:
                    async with conn.execute(
                        """SELECT DISTINCT m.therapeutic_area
                           FROM sku_mdgm_master m
                           LEFT JOIN countries c ON c.code = m.country
                           WHERE (m.region = ? OR c.region = ?)                            
                           ORDER BY m.therapeutic_area""",
                        (region, region),
                    ) as cur:
                        rows = await cur.fetchall()
                else:
                    async with conn.execute(
                        """SELECT DISTINCT therapeutic_area FROM sku_mdgm_master
                           ORDER BY therapeutic_area""",
                    ) as cur:
                        rows = await cur.fetchall()
        else:
            if country:
                async with conn.execute(
                    """SELECT DISTINCT m.therapeutic_area
                       FROM sku_mdgm_master m
                       WHERE m.country = ?                        
                       ORDER BY m.therapeutic_area""",
                    (country,),
                ) as cur:
                    rows = await cur.fetchall()
            elif region:
                async with conn.execute(
                    """SELECT DISTINCT m.therapeutic_area
                       FROM sku_mdgm_master m
                       LEFT JOIN countries c ON c.code = m.country
                       WHERE (m.region = ? OR c.region = ?)                        
                       ORDER BY m.therapeutic_area""",
                    (region, region),
                ) as cur:
                    rows = await cur.fetchall()
            else:
                async with conn.execute(
                    """SELECT DISTINCT therapeutic_area FROM sku_mdgm_master
                       ORDER BY therapeutic_area""",
                ) as cur:
                    rows = await cur.fetchall()
        # If Local/Regional user has a therapeutic_area set, restrict list to that TA
        if scope:
            role = (scope.get("role") or "").strip()
            user_ta = (scope.get("therapeutic_area") or "").strip()
            if role in ("Local", "Regional") and user_ta:
                rows = [r for r in rows if (r.get("therapeutic_area") or "").strip() == user_ta]
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
    List brands for the selected country. Send X-User-Id: Local can only request their country, Regional only countries in their region, else 403.
    """
    scope = await _get_user_scope(x_user_id) if x_user_id else None
    if scope:
        role = (scope.get("role") or "").strip()
        user_id = scope.get("user_id")
        user_region = (scope.get("region") or "").strip()
        # user_ta = (scope.get("therapeutic_area") or "").strip()
        user_ta = None
        if role == "Local":
            # Local: requested country must be one of their assigned countries
            requested_country = (country or "").strip()
            conn_check = await database.get_connection()
            try:
                async with conn_check.execute(
                    "SELECT 1 FROM user_countries WHERE user_id = ? AND country = ? LIMIT 1",
                    (user_id, requested_country),
                ) as cur2:
                    if not await cur2.fetchone():
                        raise HTTPException(
                            status_code=403,
                            detail="You can only view brands for your assigned countries",
                        )
            finally:
                await conn_check.close()
        if role == "Regional" and user_region:
            conn_check = await database.get_connection()
            try:
                async with conn_check.execute(
                    "SELECT 1 FROM countries WHERE code = ? AND region = ?",
                    ((country or "").strip(), user_region),
                ) as cur:
                    if not await cur.fetchone():
                        raise HTTPException(status_code=403, detail="You can only view brands for countries in your region")
            finally:
                await conn_check.close()
        # Scope by therapeutic area for Local and Regional users when they have a TA set
        # if role in ("Local", "Regional") and user_ta:
        #     # if therapeutic_area and (therapeutic_area or "").strip() != user_ta:
        #     #     raise HTTPException(status_code=403, detail="You can only view brands for your therapeutic area")
        #     therapeutic_area = user_ta
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
    """List SKUs for brand + country. Send X-User-Id: Local can only request their country, Regional only countries in their region, else 403."""
    scope = await _get_user_scope(x_user_id) if x_user_id else None
    if scope:
        role = (scope.get("role") or "").strip()
        user_id = scope.get("user_id")
        user_region = (scope.get("region") or "").strip()
        # user_ta = (scope.get("therapeutic_area") or "").strip()
        user_ta = None
        if role == "Local":
            # Local: requested country must be one of their assigned countries
            requested_country = (country or "").strip()
            conn_check = await database.get_connection()
            try:
                async with conn_check.execute(
                    "SELECT 1 FROM user_countries WHERE user_id = ? AND country = ? LIMIT 1",
                    (user_id, requested_country),
                ) as cur2:
                    if not await cur2.fetchone():
                        raise HTTPException(
                            status_code=403,
                            detail="You can only view SKUs for your assigned countries",
                        )
            finally:
                await conn_check.close()
        if role == "Regional" and user_region:
            conn_check = await database.get_connection()
            try:
                async with conn_check.execute(
                    "SELECT 1 FROM countries WHERE code = ? AND region = ?",
                    ((country or "").strip(), user_region),
                ) as cur:
                    if not await cur.fetchone():
                        raise HTTPException(status_code=403, detail="You can only view SKUs for countries in your region")
            finally:
                await conn_check.close()
        # Scope by therapeutic area for Local and Regional users when they have a TA set
        # if role in ("Local", "Regional") and user_ta:
        #     # if therapeutic_area and (therapeutic_area or "").strip() != user_ta:
        #     #     raise HTTPException(status_code=403, detail="You can only view SKUs for your therapeutic area")
        #     therapeutic_area = user_ta
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
    Send X-User-Id: Local can only use their country, Regional only countries in their region.
    - Left: region → country → brand (filters).
    - Center map: always show all countries where this brand is marketed (countries_marketed).
    - Right: product hierarchy + Price Request # for the selected country (pcr_count for that country).
    So we always return full countries_marketed for the map; optional therapeutic_area filters that list.
    When country is selected, pcr_count_by_country is only that country (for right panel) and we return selected_country.
    """
    if country and "|" in country:
        country = country.split("|")[0].strip() or None
    if region and "|" in region:
        region = region.split("|")[0].strip() or None
    scope = await _get_user_scope(x_user_id) if x_user_id else None
    if scope:
        role = (scope.get("role") or "").strip()
        # user_ta = (scope.get("therapeutic_area") or "").strip()
        user_ta = None
        # if role in ("Local", "Regional") and user_ta:
        #     # if therapeutic_area and (therapeutic_area or "").strip() != user_ta:
        #     #     raise HTTPException(status_code=403, detail="You can only access data for your therapeutic area")
        #     therapeutic_area = user_ta
    await _ensure_can_access_country(scope, country)
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
    Send X-User-Id: Local can only request their country, Regional only countries in their region.
    """
    scope = await _get_user_scope(x_user_id) if x_user_id else None
    if scope:
        role = (scope.get("role") or "").strip()
        # user_ta = (scope.get("therapeutic_area") or "").strip()
        user_ta = None
        # if role in ("Local", "Regional") and user_ta:
        #     # if therapeutic_area and (therapeutic_area or "").strip() != user_ta:
        #     #     raise HTTPException(status_code=403, detail="You can only access pricing for your therapeutic area")
        #     therapeutic_area = user_ta
    await _ensure_can_access_country(scope, country)
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


@router.get("/product-360/mdgm-details")
async def get_mdgm_details(
    brand: str = Query(..., description="Brand name"),
    country: str = Query(..., description="Country code"),
    therapeutic_area: Optional[str] = Query(None, description="Optional: filter by therapeutic area"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
):
    """
    SKU-MDGM DETAILS tab: MDGM rows for this brand + country.
    Send X-User-Id: Local can only request their country, Regional only countries in their region.
    """
    scope = await _get_user_scope(x_user_id) if x_user_id else None
    if scope:
        role = (scope.get("role") or "").strip()
        # user_ta = (scope.get("therapeutic_area") or "").strip()
        user_ta = None
        # if role in ("Local", "Regional") and user_ta:
        #     # if therapeutic_area and (therapeutic_area or "").strip() != user_ta:
        #     #     raise HTTPException(status_code=403, detail="You can only view MDGM details for your therapeutic area")
        #     therapeutic_area = user_ta
    await _ensure_can_access_country(scope, country)
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
        return {
            "brand": brand,
            "country": country,
            "therapeutic_area": therapeutic_area,
            "rows": out_rows,
        }
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
    AUDIT TRAIL tab in Product 360.
    Visibility:
      - Local: only audit entries for their country.
      - Regional: only audit entries for countries in their region.
      - Global/Admin: all countries/regions.
    Filters:
      - brand: filters on a.brand (exact or prefix).
      - country: must be within user's scope (enforced by _ensure_can_access_country).
      - sku_id: filters on a.sku_id.
    """
    # Get user scope
    scope = await _get_user_scope(x_user_id)
    if not scope:
        raise HTTPException(status_code=400, detail="User not found")
    role = (scope.get("role") or "").strip()
    user_region = (scope.get("region") or "").strip()
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
    # Country / scope filter
    if country:
        # Enforce that the user is allowed to see this country
        await _ensure_can_access_country(scope, country)
        conditions.append("a.country = ?")
        params.append(country)
    else:
        # No explicit country param: restrict by scope for Local and Regional
        if role == "Local":
            conditions.append(
                "a.country IN (SELECT country FROM user_countries WHERE user_id = ?)"
            )
            params.append(scope.get("user_id"))
        elif role == "Regional" and user_region:
            conditions.append(
                "EXISTS (SELECT 1 FROM countries c WHERE c.code = a.country AND c.region = ?)"
            )
            params.append(user_region)
        # Global/Admin: no extra country restriction
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