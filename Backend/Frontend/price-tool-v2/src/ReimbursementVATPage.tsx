import { useOutletContext } from "react-router-dom";
import { useState, useEffect } from "react";

const REIMBURSEMENT_TYPES = ["Product level", "SKU level", "Pack level"];
const REIMBURSEMENT_STATUSES = [
  "Not reimbursed",
  "Partially reimbursed",
  "Reimbursed",
];

const COUNTRY_OPTIONS = [
  { code: "IN", name: "India" },
  { code: "JP", name: "Japan" },
  { code: "AL", name: "Albania" },
  { code: "BA", name: "Bosnia and Herzegovina" },
];

export type ReimbursementRow = {
  rimbId: string;
  reimbursementType: string;
  country: string;
  productName: string;
  reimbursementStatus: string;
  date: string;
  therapeuticArea: string;
  reimbursementAmount: string;
};

function nextRimbId(existingRows: ReimbursementRow[]): string {
  const maxNum = existingRows.reduce((acc, r) => {
    const match = r.rimbId.match(/RIMB-(\d+)/);
    const n = match ? parseInt(match[1], 10) : 0;
    return Math.max(acc, n);
  }, 0);
  return `RIMB-${String(maxNum + 1).padStart(6, "0")}`;
}

const defaultReimbursementRow = (): ReimbursementRow => ({
  rimbId: "RIMB-000001",
  reimbursementType: REIMBURSEMENT_TYPES[0],
  country: "",
  productName: "",
  reimbursementStatus: REIMBURSEMENT_STATUSES[0],
  date: "",
  therapeuticArea: "",
  reimbursementAmount: "",
});

const ReimbursementVATPage = () => {
  const { row, formData, setFormData, isEditable } = useOutletContext<{
    row: { country?: string; productFamily?: string };
    formData: {
      reimbursementRows?: ReimbursementRow[];
      vatPercentage?: number | string;
    };
    setFormData: React.Dispatch<React.SetStateAction<any>>;
    isEditable: boolean;
  }>() || {};

  const rows: ReimbursementRow[] = Array.isArray(formData?.reimbursementRows)
    ? formData.reimbursementRows
    : [defaultReimbursementRow()];

  const vatInput = formData?.vatPercentage;
  const vatValue =
    vatInput === "" || vatInput === undefined || vatInput === null
      ? ""
      : Number(vatInput);
  const [vatError, setVatError] = useState<string | null>(null);

  useEffect(() => {
    if (!formData?.reimbursementRows?.length) {
      setFormData((prev: any) => ({
        ...prev,
        reimbursementRows: [defaultReimbursementRow()],
      }));
    }
  }, []);

  const updateRow = (index: number, field: keyof ReimbursementRow, value: string) => {
    setFormData((prev: any) => {
      const next = [...(prev?.reimbursementRows || rows)];
      next[index] = { ...next[index], [field]: value };
      return { ...prev, reimbursementRows: next };
    });
  };

  const addRow = () => {
    const nextId = nextRimbId(formData?.reimbursementRows || rows);
    setFormData((prev: any) => ({
      ...prev,
      reimbursementRows: [
        ...(prev?.reimbursementRows || []),
        {
          ...defaultReimbursementRow(),
          rimbId: nextId,
        },
      ],
    }));
  };

  const removeRow = (index: number) => {
    const next = (formData?.reimbursementRows || rows).filter((_, i) => i !== index);
    setFormData((prev: any) => ({
      ...prev,
      reimbursementRows: next.length > 0 ? next : [defaultReimbursementRow()],
    }));
  };

  const handleVatChange = (value: string) => {
    setVatError(null);
    const num = value === "" ? "" : parseFloat(value);
    if (value !== "" && (isNaN(num) || num < 0 || num > 100)) {
      setVatError("VAT percentage must be between 0 and 100");
    }
    setFormData((prev: any) => ({ ...prev, vatPercentage: value === "" ? undefined : num }));
  };

  const productOptions = row?.productFamily
    ? [row.productFamily, `${row.productFamily} (alt)`]
    : ["Select product"];

  return (
    <div className="bg-white min-h-screen p-4">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Reimbursements / VAT</h2>

      {/* Reimbursement Table */}
      <section className="mb-8">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Reimbursement</h3>
        <div className="overflow-x-auto border border-gray-200 rounded-lg">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-3 py-2 text-left font-medium text-gray-600">ID</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Reimbursement type</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Country</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Product name</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Reimbursement status</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Date</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Therapeutic area</th>
                <th className="px-3 py-2 text-right font-medium text-gray-600">Reimbursement amount</th>
                {isEditable && <th className="px-3 py-2 w-16"></th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, index) => (
                <tr key={r.rimbId} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-900 font-mono">{r.rimbId}</td>
                  <td className="px-3 py-2">
                    <select
                      value={r.reimbursementType}
                      onChange={(e) => updateRow(index, "reimbursementType", e.target.value)}
                      disabled={!isEditable}
                      className="w-full max-w-[140px] border border-gray-300 rounded px-2 py-1.5 text-sm bg-white disabled:bg-gray-50"
                    >
                      {REIMBURSEMENT_TYPES.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <select
                      value={r.country}
                      onChange={(e) => updateRow(index, "country", e.target.value)}
                      disabled={!isEditable}
                      className="w-full max-w-[160px] border border-gray-300 rounded px-2 py-1.5 text-sm bg-white disabled:bg-gray-50"
                    >
                      <option value="">Select country</option>
                      {COUNTRY_OPTIONS.map((c) => (
                        <option key={c.code} value={c.code}>{c.name}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <select
                      value={r.productName}
                      onChange={(e) => updateRow(index, "productName", e.target.value)}
                      disabled={!isEditable}
                      className="w-full max-w-[180px] border border-gray-300 rounded px-2 py-1.5 text-sm bg-white disabled:bg-gray-50"
                    >
                      <option value="">Select product</option>
                      {productOptions.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <select
                      value={r.reimbursementStatus}
                      onChange={(e) => updateRow(index, "reimbursementStatus", e.target.value)}
                      disabled={!isEditable}
                      className="w-full max-w-[180px] border border-gray-300 rounded px-2 py-1.5 text-sm bg-white disabled:bg-gray-50"
                    >
                      {REIMBURSEMENT_STATUSES.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <input
                      type="date"
                      value={r.date}
                      onChange={(e) => updateRow(index, "date", e.target.value)}
                      disabled={!isEditable}
                      className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full max-w-[140px] disabled:bg-gray-50"
                    />
                  </td>
                  <td className="px-3 py-2">
                    <input
                      type="text"
                      value={r.therapeuticArea}
                      onChange={(e) => updateRow(index, "therapeuticArea", e.target.value)}
                      disabled={!isEditable}
                      placeholder="Therapeutic area"
                      className="border border-gray-300 rounded px-2 py-1.5 text-sm w-full max-w-[140px] disabled:bg-gray-50"
                    />
                  </td>
                  <td className="px-3 py-2 text-right">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={r.reimbursementAmount}
                      onChange={(e) => updateRow(index, "reimbursementAmount", e.target.value)}
                      disabled={!isEditable}
                      placeholder="0.00"
                      className="border border-gray-300 rounded px-2 py-1.5 text-sm w-24 text-right disabled:bg-gray-50"
                    />
                  </td>
                  {isEditable && (
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        onClick={() => removeRow(index)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {isEditable && (
          <button
            type="button"
            onClick={addRow}
            className="mt-3 px-3 py-1.5 text-sm border border-gray-300 rounded bg-white hover:bg-gray-50"
          >
            + Add row
          </button>
        )}
      </section>

      {/* VAT Percentage */}
      <section>
        <h3 className="text-sm font-medium text-gray-700 mb-2">VAT Percentage</h3>
        <div className="flex items-center gap-3">
          <input
            type="number"
            min={0}
            max={100}
            step="0.01"
            value={vatValue === "" ? "" : vatValue}
            onChange={(e) => handleVatChange(e.target.value)}
            disabled={!isEditable}
            placeholder="0–100"
            className={`w-32 border rounded px-3 py-2 text-sm disabled:bg-gray-50 ${
              vatError ? "border-red-500" : "border-gray-300"
            }`}
          />
          <span className="text-sm text-gray-500">%</span>
        </div>
        {vatError && <p className="mt-1 text-sm text-red-600">{vatError}</p>}
        <p className="mt-1 text-xs text-gray-500">Must be between 0 and 100.</p>
      </section>
    </div>
  );
};

export default ReimbursementVATPage;
