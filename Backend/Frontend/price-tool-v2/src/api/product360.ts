const API = '/api';

function headersWithUser(userId?: number): HeadersInit {
  if (userId == null) return {};
  return { 'X-User-Id': String(userId) };
}

export type Region = { code: string; name: string };
export type Country = { id?: number; code: string; name: string; region?: string | null };
export type TherapeuticArea = { therapeutic_area: string };
export type Brand = { brand: string; therapeutic_area: string };
export type CountryMarketed = { country: string; region: string | null };
export type PcrCountByCountry = { country: string; region: string | null; pcr_count: number };
export type PricingRow = {
  sku_id: string;
  channel: string;
  price_type: string;
  current_price_eur: number | null;
  currency: string;
  current_price_in_target?: number;
  target_currency?: string;
  target_fx_date?: string;
};

export async function fetchRegions(userId?: number): Promise<{ regions: Region[] }> {
  const res = await fetch(`${API}/product-360/regions`, { headers: headersWithUser(userId) });
  if (!res.ok) throw new Error('Failed to fetch regions');
  return res.json();
}

export async function fetchCountries(region?: string, userId?: number): Promise<{ countries: Country[] }> {
  const url = region ? `${API}/product-360/countries?region=${encodeURIComponent(region)}` : `${API}/product-360/countries`;
  const res = await fetch(url, { headers: headersWithUser(userId) });
  if (!res.ok) throw new Error('Failed to fetch countries');
  return res.json();
}

export async function fetchTherapeuticAreas(region?: string, country?: string, userId?: number): Promise<{ therapeutic_areas: TherapeuticArea[] }> {
  const params = new URLSearchParams();
  if (region) params.set('region', region);
  if (country) params.set('country', country);
  const q = params.toString();
  const res = await fetch(`${API}/product-360/therapeutic-areas${q ? `?${q}` : ''}`, { headers: headersWithUser(userId) });
  if (!res.ok) throw new Error('Failed to fetch therapeutic areas');
  return res.json();
}

export async function fetchBrands(country: string, therapeuticArea?: string, userId?: number): Promise<{ country: string; therapeutic_area?: string; brands: Brand[] }> {
  const params = new URLSearchParams({ country });
  if (therapeuticArea) params.set('therapeutic_area', therapeuticArea);
  const res = await fetch(`${API}/product-360/brands?${params}`, { headers: headersWithUser(userId) });
  if (!res.ok) throw new Error('Failed to fetch brands');
  return res.json();
}

export async function fetchOverview(
  brand: string,
  opts?: { country?: string; region?: string; therapeutic_area?: string },
  userId?: number
): Promise<{
  brand: string;
  therapeutic_area: string | null;
  countries_marketed: CountryMarketed[];
  pcr_count_by_country: PcrCountByCountry[];
  selected_country?: { country: string; region: string | null };
}> {
  const params = new URLSearchParams({ brand });
  if (opts?.country) params.set('country', opts.country);
  if (opts?.region) params.set('region', opts.region);
  if (opts?.therapeutic_area) params.set('therapeutic_area', opts.therapeutic_area);
  const res = await fetch(`${API}/product-360/overview?${params}`, { headers: headersWithUser(userId) });
  if (!res.ok) throw new Error('Failed to fetch overview');
  return res.json();
}

export async function fetchPricing(
  brand: string,
  country: string,
  opts?: { therapeutic_area?: string; currency?: string; target_fx_date?: string },
  userId?: number
): Promise<{
  brand: string;
  country: string;
  therapeutic_area: string | null;
  pricing: PricingRow[];
  target_currency?: string;
  target_fx_date?: string;
}> {
  const params = new URLSearchParams({ brand, country });
  if (opts?.therapeutic_area) params.set('therapeutic_area', opts.therapeutic_area);
  if (opts?.currency) params.set('currency', opts.currency);
  if (opts?.target_fx_date) params.set('target_fx_date', opts.target_fx_date);
  const res = await fetch(`${API}/product-360/pricing?${params}`, { headers: headersWithUser(userId) });
  if (!res.ok) throw new Error('Failed to fetch pricing');
  return res.json();
}

export async function fetchSkus(brand: string, country: string, therapeuticArea?: string, userId?: number): Promise<{ brand: string; country: string; therapeutic_area?: string; skus: string[] }> {
  const params = new URLSearchParams({ brand, country });
  if (therapeuticArea) params.set('therapeutic_area', therapeuticArea);
  const res = await fetch(`${API}/product-360/skus?${params}`, { headers: headersWithUser(userId) });
  if (!res.ok) throw new Error('Failed to fetch SKUs');
  return res.json();
}

export type EligibleSkusResponse = {
  brand: string;
  country: string;
  therapeutic_area: string;
  channel: string;
  price_type: string | null;
  price_change_type: string;
  skus_with_price: string[];
  skus_without_price: string[];
};

export async function fetchEligibleSkus(
  brand: string,
  country: string,
  therapeuticArea: string,
  channel: string,
  priceType: string | null,
  priceChangeType: string,
  userId?: number
): Promise<EligibleSkusResponse> {
  const params = new URLSearchParams({
    brand,
    country,
    therapeutic_area: therapeuticArea,
    channel,
    price_change_type: priceChangeType,
  });
  if (priceType) params.set('price_type', priceType);
  const res = await fetch(`${API}/product-360/eligible-skus?${params}`, {
    headers: headersWithUser(userId),
  });
  if (!res.ok) throw new Error('Failed to fetch eligible SKUs');
  return res.json();
}

export type MdgmDetailRow = {
  id: number;
  sku_id: string;
  country: string;
  region: string | null;
  therapeutic_area: string;
  brand: string;
  channel: string;
  price_type: string | null;
  /** Current price: from history (post-PCR effective date) then MDGM fallback */
  current_price_eur: number | null;
  currency: string | null;
  marketed_status: string | null;
  last_pricing_update: string | null;
  /** Reimbursement (admin-editable per SKU combination) */
  reimbursement_price_local: number | null;
  reimbursement_price_eur: number | null;
  reimbursement_status: string | null;
  reimbursement_type: string | null;
  reimbursement_rate: number | null;
  vat_rate: number | null;
};

export type ReimbVatPayload = {
  reimbursement_price_local?: number | null;
  reimbursement_price_eur?: number | null;
  reimbursement_status?: string | null;
  reimbursement_type?: string | null;
  reimbursement_rate?: number | null;
  vat_rate?: number | null;
};

export async function fetchMdgmDetails(
  brand: string,
  country: string,
  therapeuticArea?: string,
  userId?: number
): Promise<{
  brand: string;
  country: string;
  therapeutic_area?: string | null;
  rows: MdgmDetailRow[];
  reimb_vat_editable_by_user?: boolean;
}> {
  const params = new URLSearchParams({ brand, country });
  if (therapeuticArea) params.set('therapeutic_area', therapeuticArea);
  const res = await fetch(`${API}/product-360/mdgm-details?${params}`, { headers: headersWithUser(userId) });
  if (!res.ok) throw new Error('Failed to fetch MDGM details');
  return res.json();
}

export async function updateMdgmReimbVat(
  rowId: number,
  payload: ReimbVatPayload,
  userId: number
): Promise<{ message: string; id: number; row: MdgmDetailRow }> {
  const body: Record<string, unknown> = {};
  if (payload.reimbursement_price_local !== undefined) body.reimbursement_price_local = payload.reimbursement_price_local;
  if (payload.reimbursement_price_eur !== undefined) body.reimbursement_price_eur = payload.reimbursement_price_eur;
  if (payload.reimbursement_status !== undefined) body.reimbursement_status = payload.reimbursement_status;
  if (payload.reimbursement_type !== undefined) body.reimbursement_type = payload.reimbursement_type;
  if (payload.reimbursement_rate !== undefined) body.reimbursement_rate = payload.reimbursement_rate;
  if (payload.vat_rate !== undefined) body.vat_rate = payload.vat_rate;
  const res = await fetch(`${API}/product-360/mdgm-row/${rowId}/reimb-vat`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'X-User-Id': String(userId) },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Failed to update reimbursement/VAT');
  }
  return res.json();
}

export type AuditEntry = {
  id: number;
  created_at: string;
  user_id: number | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  brand: string | null;
  country: string | null;
  details: string | null;
  user_name: string | null;
  user_email: string | null;
};

export async function fetchAuditTrail(
  userId: number,
  opts?: { brand?: string; country?: string; limit?: number }
): Promise<{ audit_entries: AuditEntry[] }> {
  const params = new URLSearchParams();
  if (opts?.brand) params.set('brand', opts.brand);
  if (opts?.country) params.set('country', opts.country);
  if (opts?.limit != null) params.set('limit', String(opts.limit));
  const q = params.toString();
  const res = await fetch(`${API}/product-360/audit-trail${q ? `?${q}` : ''}`, {
    headers: { 'X-User-Id': String(userId) },
  });
  if (res.status === 403) throw new Error('FORBIDDEN');
  if (!res.ok) throw new Error('Failed to fetch audit trail');
  return res.json();
}
