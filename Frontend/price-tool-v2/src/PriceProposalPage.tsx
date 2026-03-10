import { useState, useEffect, useRef } from "react";
import { useOutletContext } from 'react-router-dom';

const PriceProposalTable = ({ productFamily, priceData, onPriceDataChange, isEditable }) => {
  const handleProposedPriceChange = (id, value) => {
    const updatedData = priceData.map(row =>
      row.id === id ? { ...row, proposedPrice: value } : row
    );
    onPriceDataChange(productFamily, updatedData);
  };

  const handleProposedPercentChange = (id, value) => {
    const updatedData = priceData.map(row =>
      row.id === id ? { ...row, proposedPercent: value } : row
    );
    onPriceDataChange(productFamily, updatedData);
  };

  const handleDiscontinueChange = (id, checked) => {
    const updatedData = priceData.map(row =>
      row.id === id ? { ...row, isDiscontinue: checked } : row
    );
    onPriceDataChange(productFamily, updatedData);
  };

  const handleEffectiveDateChange = (id, value) => {
    const updatedData = priceData.map(row =>
      row.id === id ? { ...row, effectiveDate: value } : row
    );
    onPriceDataChange(productFamily, updatedData);
  };

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full border-collapse bg-white">
        <thead>
          <tr className="bg-purple-50">
            <th className="px-4 py-3 text-left text-purple-700 font-semibold border-b-2 border-gray-200">
              Price Type Name
            </th>
            <th className="px-4 py-3 text-left text-purple-700 font-semibold border-b-2 border-gray-200">
              Current Price
            </th>
            <th className="px-4 py-3 text-left text-purple-700 font-semibold border-b-2 border-gray-200">
              Floor Price
            </th>
            <th className="px-4 py-3 text-left text-purple-700 font-semibold border-b-2 border-gray-200">
              Proposed Price
            </th>
            <th className="px-4 py-3 text-left text-purple-700 font-semibold border-b-2 border-gray-200">
              Proposed<br />Percent
            </th>
            <th className="px-4 py-3 text-left text-purple-700 font-semibold border-b-2 border-gray-200">
              Is Discontinue<br />Price?
            </th>
            <th className="px-4 py-3 text-left text-purple-700 font-semibold border-b-2 border-gray-200">
              Effective Date
            </th>
            <th className="px-4 py-3 text-left text-purple-700 font-semibold border-b-2 border-gray-200">
              Published
            </th>
          </tr>
        </thead>
        <tbody>
          {priceData.map((row) => (
            <tr key={row.id} className="border-b border-gray-200">
              {/* Price Type Name - Non-editable */}
              <td className="px-4 py-4 text-gray-800">
                {row.priceTypeName}
              </td>

              {/* Current Price - Non-editable */}
              <td className="px-4 py-4 text-gray-800">
                {row.currentPrice}
              </td>

              {/* Floor Price - Non-editable */}
              <td className="px-4 py-4 text-gray-800">
                {row.floorPrice ?? '–'}
              </td>

              {/* Proposed Price - Editable */}
              <td className="px-4 py-4">
                <div className="flex items-center gap-2">
                  <div>
                    <input
                      type="text"
                      value={row.proposedPrice}
                      onChange={(e) => handleProposedPriceChange(row.id, e.target.value)}
                      disabled={!isEditable}
                      className={`w-full border border-gray-300 rounded px-2 py-1 text-gray-800 focus:outline-none focus:border-purple-500 ${
                        !isEditable ? 'bg-gray-100 cursor-not-allowed' : ''
                      }`}
                    />
                  </div>
                </div>
              </td>

              {/* Proposed Percent - Editable */}
              <td className="px-4 py-4">
                <input
                  type="text"
                  value={row.proposedPercent}
                  onChange={(e) => handleProposedPercentChange(row.id, e.target.value)}
                  disabled={!isEditable}
                  className={`w-24 border border-gray-300 rounded px-2 py-1 text-gray-800 focus:outline-none focus:border-purple-500 ${
                    !isEditable ? 'bg-gray-100 cursor-not-allowed' : ''
                  }`}
                />
              </td>

              {/* Is Discontinue Price - Editable */}
              <td className="px-4 py-4 text-center">
                <input
                  type="checkbox"
                  checked={row.isDiscontinue}
                  onChange={(e) => handleDiscontinueChange(row.id, e.target.checked)}
                  disabled={!isEditable}
                  className={`w-4 h-4 accent-purple-600 ${
                    !isEditable ? 'cursor-not-allowed' : 'cursor-pointer'
                  }`}
                />
              </td>

              {/* Effective Date - Editable */}
              <td className="px-4 py-4">
                <input
                  type="text"
                  value={row.effectiveDate}
                  onChange={(e) => handleEffectiveDateChange(row.id, e.target.value)}
                  disabled={!isEditable}
                  className={`w-32 border border-gray-300 rounded px-2 py-1 text-gray-800 focus:outline-none focus:border-purple-500 ${
                    !isEditable ? 'bg-gray-100 cursor-not-allowed' : ''
                  }`}
                />
              </td>

              {/* Published - Non-editable */}
              <td className="px-4 py-4 text-gray-800">
                {row.published}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const Accordion = ({ row, priceProposalData, onPriceDataChange, isEditable }) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="shadow-lg mt-4">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center p-3 bg-gray-100 text-left text-sm sm:text-base font-semibold hover:cursor-pointer"
      >
        <span>{row.productFamily}</span>
        <span className="text-sm sm:text-base">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div>
          <PriceProposalTable
            productFamily={row.productFamily}
            priceData={priceProposalData}
            onPriceDataChange={onPriceDataChange}
            isEditable={isEditable}
          />
        </div>
      )}
    </div>
  );
};

// Build multiple rows from backend skus_pricing (one per SKU) or use sample rows for testing
const buildPriceRowsFromPcrDetail = (pcrDetail, priceTypeName) => {
  if (!pcrDetail?.skus_pricing?.length) return null;
  return pcrDetail.skus_pricing.map((sp, idx) => ({
    id: `sku-${sp.sku_id}-${idx}`,
    priceTypeName: priceTypeName || 'NSP Minimum',
    currentPrice: sp.current_price_eur != null ? `EUR ${sp.current_price_eur.toFixed(2)}` : '–',
    floorPrice: sp.floor_price_eur != null ? `EUR ${sp.floor_price_eur.toFixed(2)}` : '–',
    proposedPrice: sp.proposed_price_eur != null ? `EUR ${sp.proposed_price_eur.toFixed(2)}` : '',
    proposedPercent: '',
    isDiscontinue: false,
    effectiveDate: '',
    published: 'No',
  }));
};

const SAMPLE_PRICE_ROWS = [
  { id: 1, priceTypeName: 'NSP Minimum', currentPrice: 'EUR 100.00', floorPrice: 'EUR 90.00', proposedPrice: 'EUR 110.00', proposedPercent: '10.0 %', isDiscontinue: false, effectiveDate: '', published: 'No' },
  { id: 2, priceTypeName: 'List Price', currentPrice: 'EUR 2.11', floorPrice: 'EUR 2.00', proposedPrice: 'EUR 2.15', proposedPercent: '1.9 %', isDiscontinue: false, effectiveDate: '03 Feb 2026', published: 'No' },
  { id: 3, priceTypeName: 'List Floor', currentPrice: 'EUR 2.00', floorPrice: 'EUR 1.90', proposedPrice: 'EUR 2.10', proposedPercent: '5.0 %', isDiscontinue: false, effectiveDate: '', published: 'No' },
];

const PriceProposalPage = () => {
  const { row, formData, setFormData, isEditable, pcrDetail } = useOutletContext() || {};
  const fileInputRef = useRef(null);
  
  
  const [files, setFiles] = useState([]);
  
 
  const handleFileSelect = (event) => {
    const selectedFiles = event.target.files;
    if (selectedFiles) {
      const newFiles = Array.from(selectedFiles);
      setFiles(prev => [...prev, ...newFiles]);
      
      
      setFormData(prev => ({
        ...prev,
        uploadedFiles: [...(prev.uploadedFiles || []), ...newFiles.map(f => f.name)]
      }));
    }
  };
  
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };
  

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    
    
    setFormData(prev => ({
      ...prev,
      uploadedFiles: (prev.uploadedFiles || []).filter((_, i) => i !== index)
    }));
  };

  // When pcrDetail loads, init price proposal from backend; otherwise use sample rows for testing
  const backendRows = buildPriceRowsFromPcrDetail(pcrDetail, row?.price_type || pcrDetail?.price_type || 'NSP Minimum');
  const defaultRows = backendRows && backendRows.length > 0 ? backendRows : SAMPLE_PRICE_ROWS;

  useEffect(() => {
    const family = row?.productFamily;
    if (!family || formData?.priceProposalData?.[family]?.length) return;
    setFormData(prev => ({
      ...prev,
      priceProposalData: {
        ...prev?.priceProposalData,
        [family]: buildPriceRowsFromPcrDetail(pcrDetail, row?.price_type || pcrDetail?.price_type)?.length
          ? buildPriceRowsFromPcrDetail(pcrDetail, row?.price_type || pcrDetail?.price_type || 'NSP Minimum')
          : SAMPLE_PRICE_ROWS
      }
    }));
  }, [pcrDetail?.skus_pricing, row?.productFamily, row?.price_type]);

  const handlePriceDataChange = (productFamily, updatedData) => {
    setFormData(prev => ({
      ...prev,
      priceProposalData: {
        ...prev.priceProposalData,
        [productFamily]: updatedData
      }
    }));
  };

  const currentPriceData = formData.priceProposalData?.[row?.productFamily] || defaultRows || SAMPLE_PRICE_ROWS;

  return (
    <div className="bg-white min-h-screen p-4">
      {/* Main Content - All in one row */}
      <div className="flex items-start gap-6">
        {/* Right Side - Filter Section in a grid */}
        <div className="flex-1">
          <div className="grid grid-cols-3 gap-4">
          
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-600">SKU Filter</label>
              <select
                className="bg-white border border-gray-300 text-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                disabled={!isEditable}
              >
                <option value=""></option>
              </select>
            </div>

           
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-600">Marketing Status Filter</label>
              <select
                className="bg-white border border-gray-300 text-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                disabled={!isEditable}
              >
                <option value=""></option>
              </select>
            </div>

         
            <div className="flex gap-2 items-end">
              <button className="bg-white border border-gray-300 text-gray-700 px-3 py-1.5 rounded text-xs hover:bg-gray-50 flex items-center gap-1.5">
                Download
                <span className="text-xs">⬇</span>
              </button>
              
             
              <div className="space-y-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={!isEditable}
                />
                
                <button 
                  onClick={handleUploadClick}
                  disabled={!isEditable}
                  className={`bg-white border border-gray-300 text-gray-700 px-3 py-1.5 rounded text-xs hover:bg-gray-50 flex items-center gap-1.5 ${
                    !isEditable ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  Upload
                  <span className="text-xs">⬆</span>
                </button>
              </div>
            </div>
          </div>

         
          {files.length > 0 && (
            <div className="mt-3 space-y-2">
              <label className="text-xs font-medium text-gray-600">Uploaded Files:</label>
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                  <span className="truncate">{file.name}</span>
                  <button
                    onClick={() => removeFile(index)}
                    disabled={!isEditable}
                    className={`text-red-500 hover:text-red-700 ml-2 ${
                      !isEditable ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          
          <div className="flex flex-col gap-1 mt-3" style={{ maxWidth: "180px" }}>
            <label className="text-xs font-medium text-gray-600">Current Year</label>
            <select
              className="bg-white border border-gray-300 text-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={!isEditable}
            >
              <option value="2025">2025</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
            </select>
          </div>
        </div>
      </div>
      
      <Accordion 
        row={row} 
        priceProposalData={currentPriceData}
        onPriceDataChange={handlePriceDataChange}
        isEditable={isEditable}
      />
    </div>
  );
};

export default PriceProposalPage;