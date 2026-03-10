import { useOutletContext } from "react-router-dom";
import { useState, useRef } from "react";


const AttachmentsAccordion = () => {
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = event.target.files;
    if (selectedFiles) {
      setFiles(prev => [...prev, ...Array.from(selectedFiles)]);
      
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
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
            onChange={handleFileSelect}
            className="hidden"
          />
          
          <button 
            onClick={handleUploadClick}
            className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded text-xs hover:bg-gray-50 flex items-center gap-1.5"
          >
            Upload
            <span className="text-xs">⬆</span>
          </button>

          {files.length > 0 && (
            <div className="space-y-2">
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                  <span className="truncate">{file.name}</span>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-red-500 hover:text-red-700 ml-2"
                  >
                    ✕
                  </button>
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
              value={formData.priceChangeType}
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
              <option value={formData.priceChangeType}>
                {formData.priceChangeType}
              </option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1">
              <span className="text-red-500">*</span> Price Change Reason
            </label>
            <input
              type="text"
              value={formData.priceChangeReason}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  priceChangeReason: e.target.value,
                })
              }
              disabled={!isEditable}
              className={`w-full p-2 border rounded ${
                !isEditable 
                  ? 'bg-gray-100 cursor-not-allowed text-gray-600' 
                  : ''
              }`}
            />
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