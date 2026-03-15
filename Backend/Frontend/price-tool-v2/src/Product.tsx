import { useState, useEffect, useCallback } from "react";
import {
  fetchRegions,
  fetchCountries,
  fetchTherapeuticAreas,
  fetchBrands,
  fetchOverview,
  fetchPricing,
  fetchMdgmDetails,
  fetchAuditTrail,
  type Region,
  type Country,
  type Brand,
  type CountryMarketed,
  type PcrCountByCountry,
  type PricingRow,
  type MdgmDetailRow,
  type AuditEntry,
} from "./api/product360";

type TabId = "overview" | "pricing" | "ibp" | "discounts" | "sku-mdgm" | "audit";

type LoggedInUser = { id?: number; role?: string; email?: string; name?: string } | null;

const TABS: { id: TabId; label: string }[] = [
  { id: "overview", label: "OVERVIEW" },
  { id: "pricing", label: "PRICING" },
  { id: "ibp", label: "IBP INFORMATION" },
  { id: "discounts", label: "DISCOUNTS INFORMATION" },
  { id: "sku-mdgm", label: "SKU-MDGM DETAILS" },
  { id: "audit", label: "AUDIT TRAIL" },
];

type ProductProps = { loggedInUser?: LoggedInUser };

export default function Product({ loggedInUser }: ProductProps) {
  const [region, setRegion] = useState<string>("");
  const [country, setCountry] = useState<string>("");
  const [therapeuticArea, setTherapeuticArea] = useState<string>("");
  const [selectedBrand, setSelectedBrand] = useState<string>("");
  const [fxCurrency, setFxCurrency] = useState<string>("");
  const [fxDate, setFxDate] = useState<string>("");

  const [regions, setRegions] = useState<Region[]>([]);
  const [countries, setCountries] = useState<Country[]>([]);
  const [therapeuticAreas, setTherapeuticAreas] = useState<string[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);

  const [overview, setOverview] = useState<{
    countries_marketed: CountryMarketed[];
    pcr_count_by_country: PcrCountByCountry[];
    selected_country?: { country: string; region: string | null };
  } | null>(null);
  const [pricing, setPricing] = useState<{
    therapeutic_area: string | null;
    pricing: PricingRow[];
    target_currency?: string;
    target_fx_date?: string;
  } | null>(null);

  const [loadingRegions, setLoadingRegions] = useState(true);
  const [loadingCountries, setLoadingCountries] = useState(false);
  const [loadingTAs, setLoadingTAs] = useState(false);
  const [loadingBrands, setLoadingBrands] = useState(false);
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [loadingPricing, setLoadingPricing] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [apiError, setApiError] = useState<string | null>(null);

  const [mdgmDetails, setMdgmDetails] = useState<{ rows: MdgmDetailRow[] } | null>(null);
  const [loadingMdgm, setLoadingMdgm] = useState(false);
  const [mdgmError, setMdgmError] = useState<string | null>(null);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [auditForbidden, setAuditForbidden] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);

  const loadRegions = useCallback(async () => {
    setLoadingRegions(true);
    setApiError(null);
    try {
      const data = await fetchRegions(loggedInUser?.id);
      setRegions(data.regions || []);
    } catch (e) {
      console.error(e);
      setRegions([]);
      setApiError("Could not load regions. Is the backend running? (Start from Backend folder: python app.py or uvicorn app:app --port 5000)");
    } finally {
      setLoadingRegions(false);
    }
  }, [loggedInUser?.id]);

  useEffect(() => {
    loadRegions();
  }, [loadRegions]);

  useEffect(() => {
    setLoadingCountries(true);
    fetchCountries(region || undefined, loggedInUser?.id)
      .then((data) => {
        setCountries(data.countries || []);
        if (!region) setCountry("");
      })
      .catch(() => setCountries([]))
      .finally(() => setLoadingCountries(false));
  }, [region, loggedInUser?.id]);

  useEffect(() => {
    if (!country && !region) {
      setTherapeuticAreas([]);
      setTherapeuticArea("");
      return;
    }
    setLoadingTAs(true);
    fetchTherapeuticAreas(region || undefined, country || undefined, loggedInUser?.id)
      .then((data) => {
        const list = (data.therapeutic_areas || []).map((t) => (typeof t === "string" ? t : t.therapeutic_area));
        setTherapeuticAreas(list);
        setTherapeuticArea("");
      })
      .catch(() => setTherapeuticAreas([]))
      .finally(() => setLoadingTAs(false));
  }, [country, region, loggedInUser?.id]);

  useEffect(() => {
    if (!country) {
      setBrands([]);
      setSelectedBrand("");
      return;
    }
    setLoadingBrands(true);
    fetchBrands(country, therapeuticArea || undefined, loggedInUser?.id)
      .then((data) => {
        setBrands(data.brands || []);
        setSelectedBrand("");
      })
      .catch(() => setBrands([]))
      .finally(() => setLoadingBrands(false));
  }, [country, therapeuticArea, loggedInUser?.id]);

  useEffect(() => {
    if (!selectedBrand) {
      setOverview(null);
      return;
    }
    setLoadingOverview(true);
    fetchOverview(selectedBrand, {
      country: country || undefined,
      region: region && !country ? region : undefined,
      therapeutic_area: therapeuticArea || undefined,
    }, loggedInUser?.id)
      .then((data) => {
        setOverview({
          countries_marketed: data.countries_marketed || [],
          pcr_count_by_country: data.pcr_count_by_country || [],
          selected_country: data.selected_country,
        });
      })
      .catch(() => setOverview(null))
      .finally(() => setLoadingOverview(false));
  }, [selectedBrand, country, region, therapeuticArea, loggedInUser?.id]);

  useEffect(() => {
    if (!selectedBrand || !country) {
      setPricing(null);
      return;
    }
    setLoadingPricing(true);
    const opts: { therapeutic_area?: string; currency?: string; target_fx_date?: string } = {
      therapeutic_area: therapeuticArea || undefined,
    };
    if (fxCurrency.trim()) opts.currency = fxCurrency.trim();
    if (fxDate.trim()) opts.target_fx_date = fxDate.trim();
    fetchPricing(selectedBrand, country, opts, loggedInUser?.id)
      .then((data) => {
        setPricing({
          therapeutic_area: data.therapeutic_area,
          pricing: data.pricing || [],
          target_currency: data.target_currency,
          target_fx_date: data.target_fx_date,
        });
      })
      .catch(() => setPricing(null))
      .finally(() => setLoadingPricing(false));
  }, [selectedBrand, country, therapeuticArea, fxCurrency, fxDate, loggedInUser?.id]);

  useEffect(() => {
    if (activeTab !== "sku-mdgm" || !selectedBrand || !country) {
      setMdgmDetails(null);
      setMdgmError(null);
      return;
    }
    setLoadingMdgm(true);
    setMdgmError(null);
    fetchMdgmDetails(selectedBrand, country, therapeuticArea || undefined, loggedInUser?.id)
      .then((data) => setMdgmDetails({ rows: data.rows || [] }))
      .catch((e) => {
        setMdgmDetails(null);
        setMdgmError("Failed to load MDGM details. Start the backend from the Backend folder: python app.py (port 5000). If it is running, check the browser console (F12) for details.");
      })
      .finally(() => setLoadingMdgm(false));
  }, [activeTab, selectedBrand, country, therapeuticArea, loggedInUser?.id]);

  const isAdmin = loggedInUser?.role?.toUpperCase().includes("ADMIN") ?? false;
  useEffect(() => {
    if (activeTab !== "audit") {
      setAuditEntries([]);
      setAuditForbidden(false);
      setAuditError(null);
      return;
    }
    if (!loggedInUser?.id) {
      setAuditForbidden(true);
      setAuditError(null);
      return;
    }
    setLoadingAudit(true);
    setAuditForbidden(false);
    setAuditError(null);
    fetchAuditTrail(loggedInUser.id, { brand: selectedBrand || undefined, country: country || undefined })
      .then((data) => setAuditEntries(data.audit_entries || []))
      .catch((e) => {
        if ((e as Error).message === "FORBIDDEN") setAuditForbidden(true);
        else {
          setAuditEntries([]);
          setAuditError("Failed to load audit trail. Ensure the backend is running (Backend folder: python app.py on port 5000).");
        }
      })
      .finally(() => setLoadingAudit(false));
  }, [activeTab, loggedInUser?.id, selectedBrand, country]);

  const selectedCountryPcrCount =
    overview?.pcr_count_by_country?.find((r) => r.country === country)?.pcr_count ?? overview?.selected_country
      ? (overview.pcr_count_by_country?.find((r) => r.country === country)?.pcr_count ?? 0)
      : null;

  const selectedBrandTa = brands.find((b) => b.brand === selectedBrand)?.therapeutic_area;

  return (
    <div className="flex min-h-[calc(100vh-64px)] bg-gray-50">
      {/* Left sidebar - Filters */}
      <aside className="w-72 shrink-0 border-r border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">Filters</h2>
        {apiError && (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            {apiError}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">Region</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
              disabled={loadingRegions}
            >
              <option value="">Select region</option>
              {regions.map((r) => (
                <option key={r.code} value={r.code}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">Country</label>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
              disabled={loadingCountries}
            >
              <option value="">Select country</option>
              {countries.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-gray-600">Therapeutic area</label>
            <select
              value={therapeuticArea}
              onChange={(e) => setTherapeuticArea(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
              disabled={loadingTAs}
            >
              <option value="">All</option>
              {therapeuticAreas.map((ta) => (
                <option key={ta} value={ta}>
                  {ta}
                </option>
              ))}
            </select>
          </div>

          <div>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Governed brands</h3>
            <div className="max-h-64 space-y-1 overflow-y-auto rounded border border-gray-200 bg-gray-50 p-2">
              {loadingBrands && <p className="text-xs text-gray-500">Loading…</p>}
              {!loadingBrands && !country && <p className="text-xs text-gray-500">Select a country first</p>}
              {!loadingBrands && brands.length === 0 && country && <p className="text-xs text-gray-500">No brands</p>}
              {!loadingBrands &&
                brands.map((b) => (
                  <label key={b.brand} className="flex cursor-pointer items-center gap-2 py-1 text-sm">
                    <input
                      type="radio"
                      name="brand"
                      checked={selectedBrand === b.brand}
                      onChange={() => setSelectedBrand(b.brand)}
                      className="h-4 w-4 text-purple-600"
                    />
                    <span className={selectedBrand === b.brand ? "font-medium text-purple-700" : "text-gray-700"}>
                      {b.brand}
                    </span>
                  </label>
                ))}
            </div>
          </div>
        </div>
      </aside>

      {/* Center - Tabs and content */}
      <main className="flex-1 overflow-auto p-6">
        <div className="mb-4 flex items-center gap-2 border-b border-gray-200">
          {selectedBrand && (
            <h1 className="mr-6 text-xl font-semibold text-gray-800">
              {selectedBrand}
              {country && (
                <span className="ml-2 text-base font-normal text-gray-500">
                  in {countries.find((c) => c.code === country)?.name ?? country}
                </span>
              )}
            </h1>
          )}
          {!selectedBrand && <h1 className="mr-6 text-xl font-semibold text-gray-500">Product 360</h1>}
          <nav className="flex min-w-0 flex-1 overflow-x-auto overflow-y-hidden">
            <div className="flex shrink-0 gap-1">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`shrink-0 rounded-t px-4 py-2 text-sm font-medium ${
                    activeTab === tab.id
                      ? "border-b-2 border-amber-500 bg-amber-50 text-amber-800"
                      : "text-gray-600 hover:bg-gray-100"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </nav>
        </div>

        {activeTab === "overview" && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-sm font-semibold text-gray-700">Marketed for this product</h3>
            {!selectedBrand && (
              <div className="text-sm text-gray-600">
                <p className="mb-2">Use the left filters, then pick a brand to see data:</p>
                <ol className="list-inside list-decimal space-y-1 text-gray-500">
                  <li>Select Region (e.g. APAC)</li>
                  <li>Select Country (e.g. India)</li>
                  <li>Select a brand under Governed brands</li>
                </ol>
              </div>
            )}
            {selectedBrand && loadingOverview && <p className="text-sm text-gray-500">Loading…</p>}
            {selectedBrand && !loadingOverview && overview && (
              <>
                <div className="mb-4 flex flex-wrap gap-2">
                  {(overview.countries_marketed || []).length === 0 && (
                    <p className="text-sm text-gray-500">No marketed countries for this brand.</p>
                  )}
                  {(overview.countries_marketed || []).map((c) => (
                    <span
                      key={c.country}
                      className="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-800"
                    >
                      {c.country} {c.region && `(${c.region})`}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-gray-400">
                  Map placeholder: use the list above or integrate a map library to show pins for these countries.
                </p>
              </>
            )}
          </div>
        )}

        {activeTab === "pricing" && (
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
            <h3 className="border-b border-gray-200 px-6 py-3 text-sm font-semibold text-gray-700">Pricing</h3>
            {(!selectedBrand || !country) && (
              <p className="p-6 text-sm text-gray-500">Select a brand and country to see pricing.</p>
            )}
            {selectedBrand && country && (
              <>
                <div className="flex flex-wrap items-end gap-4 border-b border-gray-100 px-6 py-3">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-gray-600">Bracket currency</label>
                    <input
                      type="text"
                      placeholder="e.g. USD, BAM (value in brackets)"
                      value={fxCurrency}
                      onChange={(e) => setFxCurrency(e.target.value)}
                      className="w-40 rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-gray-600">FX rate date</label>
                    <input
                      type="date"
                      value={fxDate}
                      onChange={(e) => setFxDate(e.target.value)}
                      className="rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                  </div>
                  <p className="text-xs text-gray-500">Price is always EUR; fill both to show bracket value in selected currency (e.g. 25.00 (1.50)).</p>
                </div>
                {loadingPricing && <p className="p-6 text-sm text-gray-500">Loading…</p>}
                {!loadingPricing && pricing && (
                  <div className="overflow-x-auto">
                    {pricing.therapeutic_area && (
                      <p className="px-6 pt-2 text-xs text-gray-500">Therapeutic area: {pricing.therapeutic_area}</p>
                    )}
                    {pricing.target_currency && pricing.target_fx_date && (
                      <p className="px-6 pt-1 text-xs text-gray-500">
                        Bracket value in {pricing.target_currency} (rate date: {pricing.target_fx_date})
                      </p>
                    )}
                    {pricing.pricing.length === 0 ? (
                      <p className="p-6 text-sm text-gray-500">No pricing rows.</p>
                    ) : (
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead>
                          <tr className="bg-gray-50">
                            <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-600">SKU</th>
                            <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-600">Channel</th>
                            <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-600">Price type</th>
                            <th className="px-4 py-2 text-right text-xs font-medium uppercase text-gray-600">Price (EUR)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {pricing.pricing.map((row, i) => {
                            const eurStr = row.current_price_eur != null ? row.current_price_eur.toFixed(2) : "—";
                            const bracketStr = pricing.target_currency && row.current_price_in_target != null ? ` (${row.current_price_in_target.toFixed(2)})` : "";
                            return (
                              <tr key={i} className="hover:bg-gray-50">
                                <td className="px-4 py-2 text-sm text-gray-900">{row.sku_id}</td>
                                <td className="px-4 py-2 text-sm text-gray-700">{row.channel}</td>
                                <td className="px-4 py-2 text-sm text-gray-700">{row.price_type}</td>
                                <td className="px-4 py-2 text-right text-sm text-gray-900">
                                  {eurStr}{bracketStr}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === "sku-mdgm" && (
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
            <h3 className="border-b border-gray-200 px-6 py-3 text-sm font-semibold text-gray-700">SKU-MDGM Details</h3>
            {(!selectedBrand || !country) && <p className="p-6 text-sm text-gray-500">Select a brand and country to see MDGM details.</p>}
            {selectedBrand && country && loadingMdgm && <p className="p-6 text-sm text-gray-500">Loading…</p>}
            {selectedBrand && country && mdgmError && <p className="p-6 text-sm text-amber-700">{mdgmError}</p>}
            {selectedBrand && country && !loadingMdgm && !mdgmError && mdgmDetails && (
              <div className="overflow-x-auto">
                {mdgmDetails.rows.length === 0 ? <p className="p-6 text-sm text-gray-500">No MDGM rows.</p> : (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead><tr className="bg-gray-50">
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">SKU</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Channel</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Price type</th>
                      <th className="px-3 py-2 text-right text-xs font-medium uppercase text-gray-600">Current (EUR)</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Currency</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Marketed</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Region</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Last pricing update</th>
                    </tr></thead>
                    <tbody>
                      {mdgmDetails.rows.map((row) => (
                        <tr key={row.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 text-sm text-gray-900">{row.sku_id}</td>
                          <td className="px-3 py-2 text-sm text-gray-700">{row.channel}</td>
                          <td className="px-3 py-2 text-sm text-gray-700">{row.price_type ?? "—"}</td>
                          <td className="px-3 py-2 text-right text-sm text-gray-900">{row.current_price_eur != null ? row.current_price_eur.toFixed(2) : "—"}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{row.currency ?? "—"}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{row.marketed_status ?? "—"}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{row.region ?? "—"}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{row.last_pricing_update ? new Date(row.last_pricing_update).toLocaleString() : "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === "audit" && (
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
            <h3 className="border-b border-gray-200 px-6 py-3 text-sm font-semibold text-gray-700">Audit Trail</h3>
            {auditForbidden && <p className="p-6 text-sm text-amber-700">You do not have access to the audit trail for this scope (country/brand).</p>}
            {!auditForbidden && auditError && <p className="p-6 text-sm text-amber-700">{auditError}</p>}
            {!auditForbidden && !auditError && loadingAudit && <p className="p-6 text-sm text-gray-500">Loading…</p>}
            {!auditForbidden && !auditError && !loadingAudit && (
              <div className="overflow-x-auto">
                {auditEntries.length === 0 ? <p className="p-6 text-sm text-gray-500">No audit entries yet.</p> : (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead><tr className="bg-gray-50">
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Date</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">User</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Action</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Entity</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Brand</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Country</th>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-600">Details</th>
                    </tr></thead>
                    <tbody>
                      {auditEntries.map((entry) => (
                        <tr key={entry.id} className="hover:bg-gray-50">
                          <td className="px-3 py-2 text-sm text-gray-700">{entry.created_at ? new Date(entry.created_at).toLocaleString() : "—"}</td>
                          <td className="px-3 py-2 text-sm text-gray-700">{(entry.user_name || entry.user_email) ?? String(entry.user_id ?? "—")}</td>
                          <td className="px-3 py-2 text-sm text-gray-900">{entry.action}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{entry.entity_type} {entry.entity_id ?? ""}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{entry.brand ?? "—"}</td>
                          <td className="px-3 py-2 text-sm text-gray-600">{entry.country ?? "—"}</td>
                          <td className="px-3 py-2 text-sm text-gray-500 max-w-xs truncate">{entry.details ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        )}

        {(activeTab === "ibp" || activeTab === "discounts") && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-500">Tab “{TABS.find((t) => t.id === activeTab)?.label}” – future content (IBP / Discounts).</p>
          </div>
        )}
      </main>

      {/* Right sidebar - Product hierarchy & Price Request # */}
      <aside className="w-64 shrink-0 border-l border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">Product hierarchy</h2>
        {selectedBrand && (
          <div className="space-y-1 text-sm">
            {selectedBrandTa && (
              <div className="rounded bg-gray-100 px-3 py-2 text-gray-700">{selectedBrandTa}</div>
            )}
            <div className="rounded bg-purple-50 px-3 py-2 font-medium text-purple-800">{selectedBrand}</div>
          </div>
        )}
        {!selectedBrand && <p className="text-xs text-gray-500">Select a brand to see hierarchy.</p>}

        <h2 className="mt-6 mb-2 text-sm font-semibold uppercase tracking-wide text-gray-500">Price request #</h2>
        <div className="flex h-16 items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 text-2xl font-light text-gray-400">
          {selectedBrand && country && selectedCountryPcrCount != null ? selectedCountryPcrCount : "0"}
        </div>
        {selectedBrand && country && (
          <p className="mt-1 text-xs text-gray-500">for {countries.find((c) => c.code === country)?.name ?? country}</p>
        )}
      </aside>
    </div>
  );
}
