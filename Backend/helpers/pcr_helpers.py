import database
from datetime import date
from fastapi import HTTPException
import notification_rules

# In-memory cache: date_str -> { "USD": rate_to_eur, "GBP": ..., "INR": ... }
# Frankfurter API returns 1 EUR = X USD; we store 1/X so amount_usd * rate = amount_eur
_fx_cache: dict[str, dict[str, float]] = {}
_FALLBACK_RATES = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17, "INR": 0.011}


async def _get_fx_rates_for_date(as_of: date | None = None) -> dict[str, float]:
    """Fetch EUR-based FX rates for a date from Frankfurter API. Cached per date. Falls back to static if API fails.
    API expects YYYY-MM-DD and has no rates for future dates; if as_of is in the future we use today."""
    today = date.today()
    requested = as_of or today
    if requested > today:
        requested = today
    date_str = requested.isoformat()
    if date_str in _fx_cache:
        return _fx_cache[date_str]
    try:
        import httpx
        # AsyncClient: HTTP client that does requests without blocking the server.
        # "async" = other requests can run while we wait for the external API.
        # timeout=5.0: if the API doesn't respond within 5 seconds, stop waiting and raise an error.
        async with httpx.AsyncClient(timeout=5.0) as client:
            # API URL must be YYYY-MM-DD (e.g. 2026-02-28). API has no rates for future dates.
            r = await client.get(f"https://api.frankfurter.app/{date_str}")
            # raise_for_status(): if the server returned 4xx or 5xx (e.g. 404, 500), raise an exception
            # so we don't treat an error response as success. Without this we might parse error HTML as JSON.
            r.raise_for_status()
            # r.json(): parse the response body (e.g. {"base":"EUR","rates":{"USD":1.09}}) into a Python dict.
            data = r.json()
        # API returns 1 EUR = X USD; to convert USD->EUR we use 1/X
        rates_eur_to_other = data.get("rates") or {}
        to_eur = {"EUR": 1.0}
        for curr, rate in rates_eur_to_other.items():
            if rate and rate != 0:
                to_eur[curr] = 1.0 / rate
        _fx_cache[date_str] = to_eur
        return to_eur
    except Exception:
        return _FALLBACK_RATES.copy()


def _to_eur_static(amount: float | None, currency: str) -> float | None:
    """Convert amount to EUR using static fallback rates (no API)."""
    if amount is None:
        return None
    rate = _FALLBACK_RATES.get(currency.upper(), 1.0)
    return round(amount * rate, 2)


async def to_eur(amount: float | None, currency: str, as_of_date: date | str | None = None) -> float | None:
    """Convert amount to EUR using that day's FX rates (Frankfurter API). Cached per date. Falls back to static if API fails."""
    if amount is None:
        return None
    currency = currency.upper()
    if currency == "EUR":
        return round(amount, 2)
    if as_of_date is None:
        d = None
    elif isinstance(as_of_date, str):
        d = date.fromisoformat(as_of_date) if as_of_date else None
    else:
        d = as_of_date
    rates = await _get_fx_rates_for_date(d)
    rate = rates.get(currency)
    if rate is None:
        rate = _FALLBACK_RATES.get(currency, 1.0)
    return round(amount * rate, 2)


async def from_eur_to(
    amount_eur: float | None,
    to_currency: str,
    as_of_date: date | str | None = None,
) -> float | None:
    """Convert amount in EUR to target currency using that day's FX rates (for Pricing tab bracketed value).
    Uses same Frankfurter API / cache as to_eur. to_currency e.g. EUR, USD, BAM."""
    if amount_eur is None:
        return None
    to_currency = to_currency.upper()
    if to_currency == "EUR":
        return round(amount_eur, 2)
    if as_of_date is None:
        d = None
    elif isinstance(as_of_date, str):
        d = date.fromisoformat(as_of_date) if as_of_date else None
    else:
        d = as_of_date
    # rates = other -> EUR (multiply amount in other by rate to get EUR), so EUR -> other = 1/rate
    rates_to_eur = await _get_fx_rates_for_date(d)
    rate_other_to_eur = rates_to_eur.get(to_currency) or _FALLBACK_RATES.get(to_currency, 1.0)
    if rate_other_to_eur and rate_other_to_eur != 0:
        return round(amount_eur / rate_other_to_eur, 2)
    return round(amount_eur, 2)


async def _therapeutic_area_for_brand(brand: str) -> str | None:
    """Return therapeutic_area for a brand from sku_mdgm_master (first row for that brand)."""
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT therapeutic_area FROM sku_mdgm_master WHERE brand = ? LIMIT 1",
            (brand,),
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None
    finally:
        await conn.close()


# Public alias so Product 360 and others can use one shared "get TA for brand" without duplicating queries.
get_therapeutic_area_for_brand = _therapeutic_area_for_brand


async def _brand_from_mdgm(sku_id: str, country: str, therapeutic_area: str) -> str | None:
    """Return brand from sku_mdgm_master for audit log (so filter brand=EUTHYROX matches)."""
    conn = await database.get_connection()
    try:
        async with conn.execute(
            "SELECT brand FROM sku_mdgm_master WHERE sku_id = ? AND country = ? AND therapeutic_area = ? LIMIT 1",
            (sku_id, country, therapeutic_area),
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None
    finally:
        await conn.close()


get_brand_from_mdgm = _brand_from_mdgm  # for audit log brand (Product 360 filter)


async def _user_can_approve_for_pcr(user_id: int, pcr_id: str) -> bool:
    """Check if user can approve/reject/edit this PCR (used for Regional/Global only; Local uses country+TA in each endpoint).
    Admin: cannot approve/reject.
    Global: can act on any PCR with status = escalated_to_global.
    Regional: can act on PCRs in their region (PCR's country.region = user.region)."""
    conn = await database.get_connection()
    try:
        async with conn.execute(
            """
            SELECT p.country,
                   p.therapeutic_area,
                   p.status,
                   co.region AS pcr_region
            FROM pcrs p
            LEFT JOIN countries co ON co.code = p.country
            WHERE p.pcr_id_display = ?
            """,
            (pcr_id,),
        ) as cur:
            pcr = await cur.fetchone()
        if not pcr:
            return False
        pcr_country, pcr_ta, pcr_status, pcr_region = (
            pcr[0],
            pcr[1],
            (pcr[2] or ""),
            pcr[3],
        )
        async with conn.execute(
            "SELECT role, country, therapeutic_area, region FROM users WHERE id = ?",
            (user_id,),
        ) as cur:
            user = await cur.fetchone()
        if not user:
            return False
        role, user_country, user_ta, user_region = user[0], user[1], user[2], user[3]
        if role == "Admin":
            return False
        if role == "Global":
            # Global can act on any escalated PCR (no region/country restriction)
            return pcr_status == "escalated_to_global"
        # Local/Regional: can act on PCRs in their region
        if pcr_region is None or user_region is None:
            return False
        return pcr_region == user_region
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

async def get_current_price_eur(
    sku_id: str,
    country: str,
    therapeutic_area: str,
    channel: str,
    price_type: str,
    as_of_date: str | None = None,
    fallback_to_master: bool = True,
) -> float | None:
    """Current price in EUR for this SKU/country/TA/channel/price_type as of a date.

    Source of truth: sku_price_history (latest row with effective_from <= as_of_date).
    When history is empty and fallback_to_master is True, returns current_price_eur from
    sku_mdgm_master (same dimensions). Floor and current are separate in MDGM."""
    import datetime

    if as_of_date:
        try:
            as_of = datetime.date.fromisoformat(as_of_date)
        except ValueError:
            as_of = datetime.date.today()
    else:
        as_of = datetime.date.today()
    as_of_str = as_of.isoformat()

    conn = await database.get_connection()
    try:
        async with conn.execute(
            """
            SELECT price_eur
            FROM sku_price_history
            WHERE sku_id = ?
              AND country = ?
              AND therapeutic_area = ?
              AND channel = ?
              AND price_type = ?
              AND effective_from <= ?
            ORDER BY effective_from DESC
            LIMIT 1
            """,
            (sku_id, country, therapeutic_area, channel, price_type, as_of_str),
        ) as cur:
            row = await cur.fetchone()
        if row and row[0] is not None:
            return row[0]
        if not fallback_to_master:
            return None
        # No history: use current_price_eur from sku_mdgm_master. Match on UNIQUE key (sku_id, country, channel, price_type).
        async with conn.execute(
            """
            SELECT current_price_eur
            FROM sku_mdgm_master
            WHERE sku_id = ? AND country = ? AND channel = ? AND price_type = ?
            LIMIT 1
            """,
            (sku_id, country, channel, price_type),
        ) as cur:
            row2 = await cur.fetchone()
        return float(row2[0]) if row2 and row2[0] is not None else None
    finally:
        await conn.close()


async def run_submit_approval_flow(pcr_id_display: str, submitted_by: int) -> dict:
    """Require current price per SKU; set status to local_approved (Local approved, sent to Regional). No auto-approval, no floor checks."""
    conn = await database.get_connection()
    try:
        async with conn.execute(
            """SELECT proposed_price, product_skus, country, therapeutic_area, channel, price_type, product_name
               FROM pcrs WHERE pcr_id_display = ?""",
            (pcr_id_display,),
        ) as cur:
            row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="PCR not found")
        proposed_price, product_skus_str, country, therapeutic_area, channel, price_type, product_name = (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6] if len(row) > 6 else None,
        )
        channel = (channel or "Retail").strip() if channel else "Retail"
        proposed_eur = _parse_price(proposed_price)

        # Determine classification across all SKUs in this PCR
        sku_list: list[str] = []
        if product_skus_str:
            sku_list = [s.strip() for s in (product_skus_str or "").split(",") if s.strip()]

        # If we can't parse price or have no SKUs/context, treat as a validation error
        if not sku_list:
            raise HTTPException(status_code=400, detail="At least one SKU is required on the PCR for price checks.")
        if proposed_eur is None:
            raise HTTPException(status_code=400, detail="proposed_price is invalid or missing; cannot run price checks.")
        if not (country and therapeutic_area and channel and price_type):
            raise HTTPException(status_code=400, detail="country, therapeutic_area, channel, and price_type are required for price checks.")

        # Require current price for every SKU at submit (no floor required; no auto-approval)
        for sku_id in sku_list:
            current_eur = await get_current_price_eur(
                sku_id, country, therapeutic_area, channel, price_type=price_type
            )
            if current_eur is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"SKU '{sku_id}' has no current price (country={country}, channel={channel}, price_type={price_type}). Add MDGM or history before submitting.",
                )

        # Always: Local approved, goes to Regional (no auto-approval, no floor-based logic)
        await conn.execute(
            """UPDATE pcrs
               SET local_approved_by = ?,
                   status = 'local_approved',
                   regional_approved_price_eur = NULL,
                   global_approved_price_eur = NULL,
                   escalated_by = NULL,
                   global_approved_by = NULL
             WHERE pcr_id_display = ?""",
            (submitted_by, pcr_id_display),
        )
        await conn.commit()
        await notification_rules.notify_on_local_approve(pcr_id_display)
        try:
            details = "SKUs: " + (product_skus_str or "") if product_skus_str else None
            audit_brand = await _brand_from_mdgm(sku_list[0], country, therapeutic_area) if sku_list and country and therapeutic_area else (product_name or None)
            await database.log_audit(
                user_id=submitted_by,
                action="PCR submitted (Local approved)",
                entity_type="pcr",
                entity_id=pcr_id_display,
                brand=audit_brand,
                country=country or None,
                details=details,
                sku_ids=sku_list,
            )
        except Exception:
            pass
        return {
            "message": "PCR submitted and approved by Local. Sent to Regional.",
            "pcr_id": pcr_id_display,
            "status": "local_approved",
        }
    finally:
        await conn.close()
