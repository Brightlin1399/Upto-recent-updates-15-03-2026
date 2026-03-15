import { useOutletContext } from "react-router-dom";
import { useState, useRef } from "react";


const PRESIGN_API = "/api/presign-upload";

const AttachmentsAccordion = () => {
  const { formData, setFormData, isEditable } = useOutletContext<{
    formData: { attachments?: string[] };
    setFormData: React.Dispatch<React.SetStateAction<any>>;
    isEditable: boolean;
  }>();
  const [open, setOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const attachments: string[] = Array.isArray(formData?.attachments) ? formData.attachments : [];

  const uploadFile = async (file: File): Promise<string> => {
    const res = await fetch(PRESIGN_API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: file.name,
        content_type: file.type || "application/octet-stream",
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Presign failed: ${res.status}`);
    }
    const { uploadUrl, fileUrl } = await res.json();
    const putRes = await fetch(uploadUrl, {
      method: "PUT",
      body: file,
      headers: { "Content-Type": file.type || "application/octet-stream" },
    });
    if (!putRes.ok) throw new Error("Upload to storage failed");
    return fileUrl;
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = event.target.files;
    if (!selectedFiles?.length || !isEditable) return;
    setUploadError(null);
    setUploading(true);
    try {
      const urls: string[] = [];
      for (let i = 0; i < selectedFiles.length; i++) {
        const url = await uploadFile(selectedFiles[i]);
        urls.push(url);
      }
      setFormData((prev: any) => ({
        ...prev,
        attachments: [...(prev?.attachments || []), ...urls],
      }));
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const removeAttachment = (index: number) => {
    setFormData((prev: any) => ({
      ...prev,
      attachments: (prev?.attachments || []).filter((_, i) => i !== index),
    }));
  };

  return (
    <div className="shadow-lg mt-2 ml-5 mr-5">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center p-3 bg-gray-100 text-left text-sm sm:text-base font-semibold hover:cursor-pointer"
      >
        <span>Attachments</span>
        <span className="text-sm sm:text-base">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="p-4 space-y-3">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,.pdf,.doc,.docx"
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            type="button"
            onClick={handleUploadClick}
            disabled={!isEditable || uploading}
            className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded text-xs hover:bg-gray-50 flex items-center gap-1.5 disabled:opacity-50"
          >
            {uploading ? "Uploading…" : "Upload"}
            <span className="text-xs">⬆</span>
          </button>
          {uploadError && <p className="text-sm text-red-600">{uploadError}</p>}
          {attachments.length > 0 && (
            <div className="space-y-2">
              {attachments.map((url, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                  <span className="truncate text-gray-700">{url.split("/").pop() || url}</span>
                  {isEditable && (
                    <button
                      type="button"
                      onClick={() => removeAttachment(index)}
                      className="text-red-500 hover:text-red-700 ml-2"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};


type OutletContextType = {
  formData: any;
  setFormData: React.Dispatch<React.SetStateAction<any>>;
  isEditable: boolean;
};

const PRICE_CHANGE_TYPES = [
  "Price Increase",
  "Price Decrease",
  "New Product Launch",
  "Re-pricing",
  "De-listing",
  "Voluntary Price Change",
  "Mandated",
];

const PRICE_CHANGE_REASONS = [
  "New Product Launch",
  "Competitor",
  "Raw material / Cost",
  "Market alignment",
  "Other",
];

const SummaryPage = () => {
  const { formData, setFormData, isEditable } = useOutletContext<OutletContextType>();

  return (
    <>
    <div className="p-6">
      <div className="grid grid-cols-2 gap-6">

        {/* Left Column */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1">
              <span className="text-red-500">*</span> Price Change Type
            </label>
            <select
              value={formData.priceChangeType ?? ""}
              onChange={(e) =>
                setFormData({ ...formData, priceChangeType: e.target.value })
              }
              disabled={!isEditable}
              className={`w-full p-2 border rounded text-sm ${
                !isEditable 
                  ? 'bg-gray-100 cursor-not-allowed text-gray-600' 
                  : 'bg-white'
              }`}
            >
              <option value="">Select type...</option>
              {PRICE_CHANGE_TYPES.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
            {formData.priceChangeType === 'Price Increase' && (
              <p className="mt-1 text-xs text-amber-700">Proposed price must be greater than current price.</p>
            )}
            {formData.priceChangeType === 'Price Decrease' && (
              <p className="mt-1 text-xs text-amber-700">Proposed price must be lower than current price.</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1">
              <span className="text-red-500">*</span> Price Change Reason
            </label>
            <select
              value={formData.priceChangeReason ?? ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  priceChangeReason: e.target.value,
                })
              }
              disabled={!isEditable}
              className={`w-full p-2 border rounded text-sm ${
                !isEditable 
                  ? 'bg-gray-100 cursor-not-allowed text-gray-600' 
                  : 'bg-white'
              }`}
            >
              <option value="">Select reason...</option>
              {PRICE_CHANGE_REASONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1">Products</label>
            <div className="p-2 border rounded bg-gray-50 text-sm text-blue-600">
              {formData.productFamily}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1">
              <span className="text-red-500">*</span> Expected Response Date
            </label>
            <input
              type="date"
              value={formData.expectedResponseDate}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  expectedResponseDate: e.target.value,
                })
              }
              disabled={!isEditable}
              className={`w-full p-2 border rounded text-sm ${
                !isEditable 
                  ? 'bg-gray-100 cursor-not-allowed text-gray-600' 
                  : ''
              }`}
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1">
              Price Change Reason Comments
            </label>
            <textarea
              value={formData.comments}
              onChange={(e) =>
                setFormData({ ...formData, comments: e.target.value })
              }
              disabled={!isEditable}
              className={`w-full p-2 border rounded text-sm h-24 resize-none ${
                !isEditable 
                  ? 'bg-gray-100 cursor-not-allowed text-gray-600' 
                  : ''
              }`}
            />
          </div>

         
          <div>
            <label className="block text-sm font-semibold mb-1">
              Product SKUs
            </label>
            <div className="p-2 border rounded bg-gray-50 text-sm text-blue-600">
              {formData.sku}
            </div>
          </div>
        </div>
      </div>
      
    </div>
    <AttachmentsAccordion/>
    </>
  );
};

export default SummaryPage;