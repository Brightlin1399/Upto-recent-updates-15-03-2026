# MDGM: Multiple rows per combination + Marketed status (Planned / Actively Marketed / Not Marketed)

## Business rules (from product)

- **Same combination** (sku_id, country, channel, price_type) can appear in **multiple rows** in **one table** (`sku_mdgm_master`), each row with a different **effective_from** (e.g. one row 2024-01-01, one 2026-06-01). So admin sees "old" and "new" (and planned) data.
- **Marketed status** (on each row):
  - **Actively Marketed**: this row is the **live** price (effective date has started). **At most one row per (sku_id, country, channel, price_type) can be Actively Marketed at any time.**
  - **Not Marketed**: superseded by a newer row (old price, no longer live).
  - **Planned**: PCR approved but effective date has not started yet.
- So: multiple rows per combination = **allowed**. Multiple Actively Marketed per combination = **not allowed** — only one "live" row at a time.
- **When a PCR is approved (finalised)** with a future effective date → add a row in MDGM with `effective_from` = PCR date and `marketed_status = 'Planned'`.
- **When effective date is reached** → that Planned row becomes **Actively Marketed**, and the **previous** Actively Marketed row for that combination becomes **Not Marketed**.

No separate "planned" table: everything stays in `sku_mdgm_master` with multiple rows per combination keyed by `effective_from`.

## Current state

- `sku_mdgm_master`: UNIQUE(sku_id, country, channel, price_type) — one row per combination; has `marketed_status`, `last_pricing_update`, `current_price_eur`. No `effective_from`.
- `sku_price_history`: append-only; on finalise we INSERT with `effective_from` = PCR effective_date.
- `get_current_price_eur`: reads from history (latest effective_from <= date), then fallback to MDGM.

## Target state (single table only)

1. **Schema**
   - Add `effective_from` (DATE, nullable for legacy) to `sku_mdgm_master`.
   - Change unique key to (sku_id, country, channel, price_type, effective_from) so multiple rows per combination are allowed (e.g. one row effective_from = 2024-01-01, one effective_from = 2026-06-01).
   - Standardise `marketed_status`: `'Actively Marketed'` | `'Not Marketed'` | `'Planned'`.

2. **On PCR finalise**
   - Insert into `sku_price_history` (unchanged).
   - Upsert **sku_mdgm_master**: ensure a row exists for (sku_id, country, channel, price_type, effective_from = PCR.effective_date) with `current_price_eur` = approved price and `marketed_status` = `'Planned'` if effective_date > today, else `'Actively Marketed'`.
   - If setting `'Actively Marketed'`, set any other row for the same (sku_id, country, channel, price_type) that was `'Actively Marketed'` to `'Not Marketed'`.

3. **Activation (when effective date is reached)**
   - Run periodically (or on-demand): for each MDGM row where `effective_from <= today` and `marketed_status = 'Planned'`, set `marketed_status = 'Actively Marketed'` and set the previous Actively Marketed row for that combination to `'Not Marketed'`.

4. **get_current_price_eur**
   - Keep using `sku_price_history` as primary. Optionally: when falling back to MDGM, use the row with `marketed_status = 'Actively Marketed'` and latest `effective_from <= date`.

5. **Admin**
   - List/filter MDGM by marketed_status and effective_from so admin sees old/new/planned rows in one place.
