import React, { useState, useEffect } from 'react';
import { Link, Outlet } from 'react-router-dom';
import { NavLink } from "react-router-dom";
import { fetchRegions, fetchCountries, fetchBrands, fetchSkus } from './api/product360';

type HomeProps = {
  loggedInUser: {
    id?: number;
    email: string;
    role: "LOCAL USER" | "REGIONAL USER" | "GLOBAL USER" | "ADMIN USER";
  } | null;
};

const PRICE_CHANGE_TYPES = [
  "Price Increase", "Price Decrease", "New Product Launch", "Re-pricing", "De-listing",
  "Voluntary Price Change", "Mandated",
];
const PRICE_CHANGE_REASONS = [
  "New Product Launch", "Competitor", "Raw material / Cost", "Market alignment", "Other",
];

export default function Home({ loggedInUser }:HomeProps) {
  
  const [showFilters, setShowFilters] = useState(false);
  
 
  const [showDetailPage, setShowDetailPage] = useState(false);
  const [selectedRow, setSelectedRow] = useState(null);
  
 
  const [showNewModal, setShowNewModal] = useState(false);
  
  
  const [newEntry, setNewEntry] = useState({
    countries: [] as string[],
    brand: '',
    sku: [] as string[]
  });
  // Current + floor price per SKU when creating PCR (from backend)
  const [createModalSkuPrices, setCreateModalSkuPrices] = useState<Record<string, { current_price_eur: number | null; floor_price_eur: number | null }>>({});
  const [createModalPricesLoading, setCreateModalPricesLoading] = useState(false);

  const initialFilters = {
  priceRequestId: "",
  approvalStatus: "",
  country: "",
  productFamily: "",
  priceChangeType: "",
  submitter: "",
  approvalDays: "",
  priceChangeReason: "",
  submittedFromDate: "",
  submittedToDate: "",
  autoApproved: false,
};

  const [filters, setFilters] = useState(initialFilters);
  



  // PCR list: only from database (loaded via API when user is logged in)
const [allTableData, setAllTableData] = useState([]);
const [tableData, setTableData] = useState([]);
const [pcrsLoading, setPcrsLoading] = useState(false);
// Create New PCR modal: all from backend (product-360 API)
const [createModalRegions, setCreateModalRegions] = useState<Array<{ code: string; name: string }>>([]);
const [createModalRegionsLoading, setCreateModalRegionsLoading] = useState(false);
const [createModalSelectedRegion, setCreateModalSelectedRegion] = useState<string>('');
const [createModalCountries, setCreateModalCountries] = useState<Array<{ code: string; name: string; region?: string | null }>>([]);
const [createModalCountriesLoading, setCreateModalCountriesLoading] = useState(false);
const [createModalBrands, setCreateModalBrands] = useState<Array<{ brand: string; therapeutic_area: string }>>([]);
const [createModalBrandsLoading, setCreateModalBrandsLoading] = useState(false);
const [createModalSkus, setCreateModalSkus] = useState<string[]>([]);
const [createModalSkusLoading, setCreateModalSkusLoading] = useState(false);

const [currentPage, setCurrentPage] = useState(1);
const rowsPerPage = 10;

// Load PCR list from backend (only source of truth; no dummy data)
const backendStatusToApprovalStatus = {
  draft: 'Draft',
  local_approved: 'Pending',
  auto_approved: 'Approved',
  regional_approved: 'Approved',
  regional_rejected: 'Regional Rejected',
  escalated_to_global: 'Escalated to Global',
  global_approved: 'Approved',
  global_rejected: 'Global Rejected',
  finalised: 'Finalized',
};
async function loadPcrsFromApi(userId, loggedInUserEmail = '') {
  if (!userId) return;
  setPcrsLoading(true);
  try {
    const res = await fetch('/api/pcrs', { headers: { 'X-User-Id': String(userId) } });
    if (!res.ok) {
      setAllTableData([]);
      return;
    }
    const data = await res.json();
    if (!Array.isArray(data.pcrs)) return;
    const rows = data.pcrs.map((p) => ({
      id: p.pcr_id_display,
      backendId: p.pcr_id_display,
      country: p.country || '',
      productFamily: p.product_name || '',
      name: p.submitter_name || '',
      createdBy: p.submitter_email || '',
      approvalStatus: backendStatusToApprovalStatus[p.status] ?? p.status,
      priceChangeType: p.price_change_type || '',
      priceChangeReason: p.price_change_reason || '',
      submittedDate: p.created_at ? new Date(p.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).replace(/ /g, ' ') : '',
      current_price: p.current_price,
      floor_price: p.floor_price,
      proposed_price: p.proposed_price,
      autoApproved: p.status === 'auto_approved',
      attachments: Array.isArray(p.submission_attachments) ? p.submission_attachments : [],
    }));
    setAllTableData((prev) => {
      const apiIds = new Set(rows.map((r) => r.id));
      const localDrafts = (prev || []).filter(
        (row) => row.approvalStatus === 'Draft' && !row.backendId && row.createdBy === loggedInUserEmail && !apiIds.has(row.id)
      );
      return [...localDrafts, ...rows];
    });
  } catch (e) {
    console.error('Failed to load PCRs', e);
    setAllTableData([]);
  } finally {
    setPcrsLoading(false);
  }
}
useEffect(() => {
  if (!loggedInUser?.id) {
    setAllTableData([]);
    setPcrsLoading(false);
    setCreateModalCountries([]);
    return;
  }
  loadPcrsFromApi(loggedInUser.id, loggedInUser?.email ?? '');
  // Load regions for Create New PCR (optional filter)
  setCreateModalRegionsLoading(true);
  fetchRegions(loggedInUser.id)
    .then((data) => setCreateModalRegions(data.regions || []))
    .catch(() => setCreateModalRegions([]))
    .finally(() => setCreateModalRegionsLoading(false));
}, [loggedInUser?.id, loggedInUser?.email]);

// Load countries when region changes (or on mount); used for Create New PCR and table labels
useEffect(() => {
  if (!loggedInUser?.id) return;
  setCreateModalCountriesLoading(true);
  const region = createModalSelectedRegion || undefined;
  fetchCountries(region, loggedInUser.id)
    .then((data) => setCreateModalCountries(data.countries || []))
    .catch(() => setCreateModalCountries([]))
    .finally(() => setCreateModalCountriesLoading(false));
}, [loggedInUser?.id, createModalSelectedRegion]);

// Load brands when user selects country/countries in Create New PCR
useEffect(() => {
  if (!loggedInUser?.id || newEntry.countries.length === 0) {
    setCreateModalBrands([]);
    return;
  }
  setCreateModalBrandsLoading(true);
  Promise.all(
    newEntry.countries.map((code) => fetchBrands(code, undefined, loggedInUser.id))
  )
    .then((responses) => {
      const byBrand = new Map<string, string>();
      responses.forEach((r) => {
        (r.brands || []).forEach((b) => {
          if (!byBrand.has(b.brand)) byBrand.set(b.brand, b.therapeutic_area || '');
        });
      });
      setCreateModalBrands(Array.from(byBrand.entries()).map(([brand, therapeutic_area]) => ({ brand, therapeutic_area })));
    })
    .catch(() => setCreateModalBrands([]))
    .finally(() => setCreateModalBrandsLoading(false));
}, [loggedInUser?.id, newEntry.countries.join(',')]);

// Load SKUs when user selects brand and country in Create New PCR
useEffect(() => {
  if (!loggedInUser?.id || !newEntry.brand || newEntry.countries.length === 0) {
    setCreateModalSkus([]);
    return;
  }
  const ta = createModalBrands.find((b) => b.brand === newEntry.brand)?.therapeutic_area;
  setCreateModalSkusLoading(true);
  fetchSkus(newEntry.brand, newEntry.countries[0], ta, loggedInUser.id)
    .then((data) => setCreateModalSkus(data.skus || []))
    .catch(() => setCreateModalSkus([]))
    .finally(() => setCreateModalSkusLoading(false));
}, [loggedInUser?.id, newEntry.brand, newEntry.countries[0], createModalBrands]);

// Filter data based on logged-in user and draft status
useEffect(() => {
  if (!loggedInUser) return;
  
  const filteredData = allTableData.filter(row => {
    
    if (row.approvalStatus === 'Draft') {
      return row.createdBy === loggedInUser.email;
    }
    
    return true;
  });
  
  setTableData(filteredData);
  setCurrentPage(1); 
}, [allTableData, loggedInUser]);


const indexOfLastRow = currentPage * rowsPerPage;
const indexOfFirstRow = indexOfLastRow - rowsPerPage;
const currentRows = tableData.slice(indexOfFirstRow, indexOfLastRow);
const totalPages = Math.ceil(tableData.length / rowsPerPage);


const goToNextPage = () => {
  if (currentPage < totalPages) {
    setCurrentPage(currentPage + 1);
  }
};

const goToPreviousPage = () => {
  if (currentPage > 1) {
    setCurrentPage(currentPage - 1);
  }
};

const goToPage = (pageNumber) => {
  setCurrentPage(pageNumber);
};





  
  // Country label for table/modal: from backend-loaded createModalCountries
  const countryLabel = (code: string | undefined) => createModalCountries.find((c) => c.code === code)?.name ?? code ?? '';

  function generatePCRId() {
    return 'PCR-' + Math.floor(100000 + Math.random() * 900000);
  }
  
 
  function getCurrentDate() {
    const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEPT', 'OCT', 'NOV', 'DEC'];
    const date = new Date();
    return `${date.getDate()}. ${months[date.getMonth()]}. ${date.getFullYear()}`;
  }


  function handleCountryToggle(countryCode: string) {
  setNewEntry(prev => {
    const has = prev.countries.includes(countryCode);
    const next = has
      ? prev.countries.filter(c => c !== countryCode)
      : [...prev.countries, countryCode];
    return { ...prev, countries: next, brand: '', sku: [] };
  });
}


function handleBrandChange(e) {
  setNewEntry({
    ...newEntry,
    brand: e.target.value,
    sku: []
  });
}



function handleSkuChange(skuValue) {
  setNewEntry(prev => {
    const isSelected = prev.sku.includes(skuValue);
    
    if (isSelected) {
      // Remove SKU if already selected
      return {
        ...prev,
        sku: prev.sku.filter(s => s !== skuValue)
      };
    } else {
      // Add SKU if not selected
      return {
        ...prev,
        sku: [...prev.sku, skuValue]
      };
    }
  });
}

  // When creating PCR: fetch current + floor price for each selected SKU (show in modal; uses first selected country)
  const firstCountry = newEntry.countries[0];
  useEffect(() => {
    const country = firstCountry;
    const brand = newEntry.brand;
    const skuIds = newEntry.sku;
    const ta = brand ? (createModalBrands.find((b) => b.brand === brand)?.therapeutic_area ?? '') : '';
    if (!country || !ta || skuIds.length === 0) {
      setCreateModalSkuPrices({});
      return;
    }
    let cancelled = false;
    setCreateModalPricesLoading(true);
    const priceType = 'NSP Minimum';
    Promise.all(
      skuIds.map(async (skuId) => {
        try {
          const res = await fetch(
            `/api/countries/${encodeURIComponent(country)}/skus/${encodeURIComponent(skuId)}/prices?therapeutic_area=${encodeURIComponent(ta)}&price_type=${encodeURIComponent(priceType)}`
          );
          if (!res.ok || cancelled) return { skuId, current: null, floor: null };
          const data = await res.json();
          const first = data.prices && data.prices[0];
          return {
            skuId,
            current: first?.current_price_eur ?? null,
            floor: first?.floor_price_eur ?? null,
          };
        } catch {
          return { skuId, current: null, floor: null };
        }
      })
    ).then((results) => {
      if (cancelled) return;
      const next = {};
      results.forEach((r) => {
        next[r.skuId] = { current_price_eur: r.current, floor_price_eur: r.floor };
      });
      setCreateModalSkuPrices(next);
      setCreateModalPricesLoading(false);
    });
    return () => { cancelled = true; };
  }, [firstCountry, newEntry.brand, newEntry.sku.join(',')]);

 function handleAddEntry() {
  if (newEntry.countries.length === 0 || !newEntry.brand || newEntry.sku.length === 0) {
    alert('Please select at least one country, a brand, and at least one SKU');
    return;
  }
  const newPCRs = newEntry.countries.map((country) => ({
    id: generatePCRId(),
    country,
    productFamily: newEntry.brand,
    sku: newEntry.sku.join(', '),
    name: loggedInUser?.email || 'Current User',
    priceChangeType: 'Voluntary Price Change',
    priceChangeReason: 'Other',
    approvalStatus: 'Draft',
    submittedDate: getCurrentDate(),
    createdBy: loggedInUser?.email || 'Current User',
    channel: 'Retail',
    price_type: 'NSP Minimum',
  }));
  const updatedData = [...newPCRs, ...allTableData];
  setAllTableData(updatedData);
  setSelectedRow(newPCRs[0]);
  setShowDetailPage(true);
  setShowNewModal(false);
  setNewEntry({ countries: [], brand: '', sku: [] });
}
  

  function handleRowClick(row) {
    setSelectedRow(row);
    setShowDetailPage(true);
  }
  
  
  function goBackToTable() {
    setShowDetailPage(false);
    setSelectedRow(null);
  }
  

  async function handleSummitPCR(pcrId, formDataFromDetail = null) {
    const pcr = allTableData.find(row => row.id === pcrId);
    if (!pcr || pcr.approvalStatus !== 'Draft') return;

    let current_price = pcr.current_price;
    let proposed_price = pcr.proposed_price;
    const firstPriceRow = formDataFromDetail?.priceProposalData?.[pcr.productFamily]?.[0];
    if (firstPriceRow) {
      if (current_price == null || current_price === '') current_price = firstPriceRow.currentPrice;
      if (proposed_price == null || proposed_price === '') proposed_price = firstPriceRow.proposedPrice;
    }

    const productSkus = pcr.sku ? String(pcr.sku).split(',').map((s) => s.trim()).filter(Boolean) : (pcr.product_skus ? [pcr.product_skus] : []);

    const priceChangeType = formDataFromDetail?.priceChangeType ?? pcr.priceChangeType ?? '';
    const currentNum = parseFloat(String(current_price));
    const proposedNum = parseFloat(String(proposed_price));
    const validNumbers = !Number.isNaN(currentNum) && !Number.isNaN(proposedNum);
    if (validNumbers && priceChangeType === 'Price Increase' && proposedNum <= currentNum) {
      alert(`Price Change Type is "Price Increase". Proposed price (${proposed_price}) must be greater than current price (${current_price}).`);
      return;
    }
    if (validNumbers && priceChangeType === 'Price Decrease' && proposedNum >= currentNum) {
      alert(`Price Change Type is "Price Decrease". Proposed price (${proposed_price}) must be lower than current price (${current_price}).`);
      return;
    }

    let backendId = null;
    let newStatus = 'Submitted for Local Approval';
    let autoApproved = false;

    if (loggedInUser?.id) {
      try {
        const body: Record<string, unknown> = {
          submitted_by: loggedInUser.id,
          pcr_id: pcr.id,
          country: pcr.country || '',
          brand: pcr.productFamily || '',
          product_skus: productSkus.length ? productSkus : [pcr.id],
          product_name: pcr.productFamily,
          channel: pcr.channel || 'Retail',
          price_type: pcr.price_type || 'NSP Minimum',
        };
        if (current_price != null && current_price !== '') body.current_price = current_price;
        if (proposed_price != null && proposed_price !== '') body.proposed_price = proposed_price;
        if (priceChangeType) body.price_change_type = priceChangeType;
        const reason = formDataFromDetail?.priceChangeReason ?? pcr.priceChangeReason;
        if (reason) body.price_change_reason = reason;
        const expectedDate = formDataFromDetail?.expectedResponseDate ?? pcr.expectedResponseDate;
        if (expectedDate) body.expected_response_date = expectedDate;
        const comments = formDataFromDetail?.comments ?? pcr.comments;
        if (comments) body.price_change_reason_comments = comments;
        const attachmentUrls = formDataFromDetail?.attachments;
        if (Array.isArray(attachmentUrls) && attachmentUrls.length > 0) body.attachments = attachmentUrls;

        const response = await fetch('/api/pcrs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify(body),
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
          alert(`Failed to submit: ${error.detail || error.error || 'Unknown error'}`);
          return;
        }
        const data = await response.json();
        backendId = data.pcr_id;
        if (data.status === 'local_approved') newStatus = 'Pending';
        else if (data.status === 'auto_approved' || data.auto_approved) {
          newStatus = 'Approved';
          autoApproved = true;
        }
      } catch (err) {
        console.error('Submit error:', err);
        alert('Failed to submit PCR');
        return;
      }
    }

    const updatedData = allTableData.map((row) => {
      if (row.id === pcrId && row.approvalStatus === 'Draft') {
        return {
          ...row,
          approvalStatus: newStatus,
          submittedDate: getCurrentDate(),
          backendId: backendId || row.backendId,
          autoApproved: autoApproved || row.autoApproved,
        };
      }
      return row;
    });

    setAllTableData(updatedData);
    if (selectedRow?.id === pcrId) setSelectedRow(updatedData.find((r) => r.id === pcrId));
    loadPcrsFromApi(loggedInUser.id, loggedInUser?.email ?? '');
    alert(newStatus === 'Approved' ? 'PCR submitted and auto-approved.' : 'PCR submitted. Pending Regional approval.');
  }

 
  async function handleLocalApprove(pcrId) {
    const pcr = allTableData.find(row => row.id === pcrId);
    if (!pcr || pcr.approvalStatus !== 'Submitted for Local Approval' || pcr.localDecision) return;
    
    let autoApproved = false;
    if (pcr.backendId && loggedInUser?.id) {
      try {
        const response = await fetch(`/api/pcrs/${pcr.backendId}/local-approve`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify({ approved_by: loggedInUser.id }),
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          alert(`Failed to approve: ${error.error || 'Unknown error'}`);
          return;
        }
        const data = await response.json().catch(() => ({}));
        autoApproved = data.auto_approved === true;
      } catch (err) {
        console.error('Approve error:', err);
        alert('Failed to approve PCR');
        return;
      }
    }

    const updatedData = allTableData.map(row => {
      if (row.id === pcrId && row.approvalStatus === 'Submitted for Local Approval' && !row.localDecision) {
        return {
          ...row,
          approvalStatus: autoApproved ? 'Approved' : 'Pending',
          autoApproved: autoApproved || row.autoApproved,
          localApprovedBy: loggedInUser?.email,
          localApprovedDate: getCurrentDate(),
          localDecision: 'Approved'
        };
      }
      return row;
    });

    setAllTableData(updatedData);

    if (selectedRow?.id === pcrId) {
      const updatedRow = updatedData.find(row => row.id === pcrId);
      setSelectedRow(updatedRow);
    }

    alert(autoApproved ? 'PCR auto-approved (price increase). Fully approved.' : 'PCR approved at local level! Now pending regional/global approval.');
  }

  
  async function handleLocalReject(pcrId) {
    const pcr = allTableData.find(row => row.id === pcrId);
    if (!pcr || pcr.approvalStatus !== 'Submitted for Local Approval' || pcr.localDecision) return;
    
    // Call backend API if PCR has backendId and user has id
    if (pcr.backendId && loggedInUser?.id) {
      try {
        const response = await fetch(`/api/pcrs/${pcr.backendId}/local-reject`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify({ rejected_by: loggedInUser.id }),
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          alert(`Failed to reject: ${error.error || 'Unknown error'}`);
          return;
        }
      } catch (err) {
        console.error('Reject error:', err);
        alert('Failed to reject PCR');
        return;
      }
    }
    
    // Update UI (existing logic)
    const updatedData = allTableData.map(row => {
      if (row.id === pcrId && row.approvalStatus === 'Submitted for Local Approval' && !row.localDecision) {
        return {
          ...row,
          approvalStatus: 'Rejected by Local',
          localRejectedBy: loggedInUser?.email,
          localRejectedDate: getCurrentDate(),
          localDecision: 'Rejected'
        };
      }
      return row;
    });
    
    setAllTableData(updatedData);
    
    if (selectedRow?.id === pcrId) {
      const updatedRow = updatedData.find(row => row.id === pcrId);
      setSelectedRow(updatedRow);
    }
    
    alert('PCR rejected at local level.');
  }

  async function handleRegionalApprove(pcrId) {
    const pcr = allTableData.find(row => row.id === pcrId);
    if (!pcr || pcr.approvalStatus !== 'Pending' || pcr.regionalDecision) return;
    
    // Call backend API if PCR has backendId and user has id
    if (pcr.backendId && loggedInUser?.id) {
      try {
        const response = await fetch(`/api/pcrs/${pcr.backendId}/regional-approve`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify({ approved_by: loggedInUser.id }),
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          alert(`Failed to approve: ${error.error || 'Unknown error'}`);
          return;
        }
      } catch (err) {
        console.error('Approve error:', err);
        alert('Failed to approve PCR');
        return;
      }
    }
    
    // Update UI: after regional approve, keep status Pending (waiting for Global)
    const updatedData = allTableData.map(row => {
      if (row.id === pcrId && row.approvalStatus === 'Pending' && !row.regionalDecision) {
        return {
          ...row,
          approvalStatus: 'Pending',
          regionalApprovedBy: loggedInUser?.email,
          regionalApprovedDate: getCurrentDate(),
          regionalDecision: 'Approved',
          escalatedToGlobal: true
        };
      }
      return row;
    });
    
    setAllTableData(updatedData);
    
    if (selectedRow?.id === pcrId) setSelectedRow(updatedData.find(row => row.id === pcrId));
    loadPcrsFromApi(loggedInUser?.id, loggedInUser?.email ?? '');
    alert('PCR approved at regional level! Now pending Global approval.');
  }

  async function handleRegionalReject(pcrId) {
    const pcr = allTableData.find(row => row.id === pcrId);
    if (!pcr || pcr.approvalStatus !== 'Pending' || pcr.regionalDecision) return;
    
    // Call backend API if PCR has backendId and user has id
    if (pcr.backendId && loggedInUser?.id) {
      try {
        const response = await fetch(`/api/pcrs/${pcr.backendId}/regional-reject`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify({ rejected_by: loggedInUser.id }),
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          alert(`Failed to reject: ${error.error || 'Unknown error'}`);
          return;
        }
      } catch (err) {
        console.error('Reject error:', err);
        alert('Failed to reject PCR');
        return;
      }
    }
    
    // Update UI (existing logic)
    const updatedData = allTableData.map(row => {
      if (row.id === pcrId && row.approvalStatus === 'Pending' && !row.regionalDecision) {
        return {
          ...row,
          approvalStatus: 'Rejected by Regional',
          regionalRejectedBy: loggedInUser?.email,
          regionalRejectedDate: getCurrentDate(),
          regionalDecision: 'Rejected'
        };
      }
      return row;
    });
    
    setAllTableData(updatedData);
    
    if (selectedRow?.id === pcrId) setSelectedRow(updatedData.find(row => row.id === pcrId));
    loadPcrsFromApi(loggedInUser?.id, loggedInUser?.email ?? '');
    alert('PCR rejected at regional level.');
  }


  async function handleEscalateToGlobal(pcrId) {
    const pcr = allTableData.find(row => row.id === pcrId);
    if (!pcr?.backendId || !loggedInUser?.id) {
      alert('Cannot escalate: no backend PCR or user.');
      return;
    }
    try {
      const response = await fetch(`/api/pcrs/${pcr.backendId}/escalate-to-global`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
        body: JSON.stringify({ escalated_by: loggedInUser.id, attachments: ['https://example.com/placeholder.pdf'], comments: 'Escalated from UI' }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        alert(`Failed to escalate: ${err.detail || 'Unknown error'}`);
        return;
      }
      loadPcrsFromApi(loggedInUser.id, loggedInUser?.email ?? '');
      if (selectedRow?.id === pcrId) {
        const updated = await fetch(`/api/pcrs`, { headers: { 'X-User-Id': String(loggedInUser.id) } }).then(r => r.json()).catch(() => ({ pcrs: [] }));
        const row = (updated.pcrs || []).find((r) => r.pcr_id_display === pcr.backendId);
        if (row) setSelectedRow({ ...selectedRow, approvalStatus: backendStatusToApprovalStatus[row.status] ?? row.status, escalatedToGlobal: true });
      }
      alert('PCR escalated to global.');
    } catch (e) {
      console.error(e);
      alert('Failed to escalate PCR');
    }
  }

  async function handleGlobalApprove(pcrId) {
    const pcr = allTableData.find(row => row.id === pcrId);
    const isPendingGlobal = pcr?.approvalStatus === 'Escalated to Global' || (pcr?.approvalStatus === 'Pending' && pcr?.regionalDecision === 'Approved');
    if (!pcr || !isPendingGlobal || pcr.globalDecision) return;
    
    // Call backend API if PCR has backendId and user has id
    if (pcr.backendId && loggedInUser?.id) {
      try {
        const response = await fetch(`/api/pcrs/${pcr.backendId}/global-approve`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify({ approved_by: loggedInUser.id }),
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          alert(`Failed to approve: ${error.error || 'Unknown error'}`);
          return;
        }
      } catch (err) {
        console.error('Approve error:', err);
        alert('Failed to approve PCR');
        return;
      }
    }
    
    const updatedData = allTableData.map(row => {
      if (row.id === pcrId && (row.approvalStatus === 'Escalated to Global' || (row.approvalStatus === 'Pending' && row.regionalDecision === 'Approved')) && !row.globalDecision) {
        return {
          ...row,
          approvalStatus: 'Approved',
          globalApprovedBy: loggedInUser?.email,
          globalApprovedDate: getCurrentDate(),
          globalDecision: 'Approved'
        };
      }
      return row;
    });

    setAllTableData(updatedData);

    if (selectedRow?.id === pcrId) setSelectedRow(updatedData.find(row => row.id === pcrId));
    loadPcrsFromApi(loggedInUser?.id, loggedInUser?.email ?? '');
    alert('PCR approved at global level!');
  }

  async function handleGlobalReject(pcrId) {
    const pcr = allTableData.find(row => row.id === pcrId);
    const isPendingGlobal = pcr?.approvalStatus === 'Escalated to Global' || (pcr?.approvalStatus === 'Pending' && pcr?.regionalDecision === 'Approved');
    if (!pcr || !isPendingGlobal || pcr.globalDecision) return;
    
    // Call backend API if PCR has backendId and user has id
    if (pcr.backendId && loggedInUser?.id) {
      try {
        const response = await fetch(`/api/pcrs/${pcr.backendId}/global-reject`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify({ rejected_by: loggedInUser.id }),
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          alert(`Failed to reject: ${error.error || 'Unknown error'}`);
          return;
        }
      } catch (err) {
        console.error('Reject error:', err);
        alert('Failed to reject PCR');
        return;
      }
    }
    
    const updatedData = allTableData.map(row => {
      if (row.id === pcrId && (row.approvalStatus === 'Escalated to Global' || (row.approvalStatus === 'Pending' && row.regionalDecision === 'Approved')) && !row.globalDecision) {
        return {
          ...row,
          approvalStatus: 'Rejected by Global',
          globalRejectedBy: loggedInUser?.email,
          globalRejectedDate: getCurrentDate(),
          globalDecision: 'Rejected'
        };
      }
      return row;
    });

    setAllTableData(updatedData);

    if (selectedRow?.id === pcrId) setSelectedRow(updatedData.find(row => row.id === pcrId));
    loadPcrsFromApi(loggedInUser?.id, loggedInUser?.email ?? '');
    alert('PCR rejected at global level.');
  }

  async function handleResubmit(pcrId) {
    const pcr = allTableData.find(row => row.id === pcrId);
    if (!pcr) return;
    const canResubmit = pcr.approvalStatus === 'Draft' ||
                        pcr.approvalStatus === 'Regional Rejected' ||
                        pcr.approvalStatus === 'Global Rejected';
    if (!canResubmit) return;
    
    // Call backend API if PCR has backendId and user has id
    if (pcr.backendId && loggedInUser?.id) {
      try {
        const response = await fetch(`/api/pcrs/${pcr.backendId}/resubmit`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify({ re_submitted_by: loggedInUser.id }),
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({ error: 'Unknown error' }));
          alert(`Failed to resubmit: ${error.error || 'Unknown error'}`);
          return;
        }
      } catch (err) {
        console.error('Resubmit error:', err);
        alert('Failed to resubmit PCR');
        return;
      }
    }
    
    // Update UI (existing logic)
    const updatedData = allTableData.map(row => {
      if (row.id === pcrId && canResubmit) {
        return {
          ...row,
          approvalStatus: 'Draft',
          createdBy: loggedInUser?.email || row.createdBy, // Update createdBy so PCR remains visible after resubmit
          resubmittedBy: loggedInUser?.email,
          resubmittedDate: getCurrentDate(),
          // Clear previous decisions
          localDecision: undefined,
          regionalDecision: undefined,
          globalDecision: undefined,
          escalatedToGlobal: undefined
        };
      }
      return row;
    });
    
    setAllTableData(updatedData);
    
    if (selectedRow?.id === pcrId) setSelectedRow(updatedData.find(row => row.id === pcrId));
    loadPcrsFromApi(loggedInUser?.id, loggedInUser?.email ?? '');
    alert('PCR moved back to Draft status. You can now edit and save changes.');
  }

  async function handleSavePCR(updatedRow) {
    if (updatedRow.approvalStatus !== 'Draft') {
      alert('Cannot save - PCR is not in Draft status');
      return;
    }

    const rowToSave = { ...updatedRow };
    const priceRows = updatedRow.priceProposalData?.[updatedRow.productFamily];
    if (Array.isArray(priceRows) && priceRows.length > 0) {
      const first = priceRows[0];
      rowToSave.current_price = first.currentPrice ?? updatedRow.current_price;
      rowToSave.proposed_price = first.proposedPrice ?? updatedRow.proposed_price;
    }

    if (!loggedInUser?.id) {
      const updatedData = allTableData.map((row) => (row.id === rowToSave.id ? rowToSave : row));
      setAllTableData(updatedData);
      setSelectedRow(rowToSave);
      alert('Changes saved locally.');
      return;
    }

    try {
      if (rowToSave.backendId) {
        // Existing draft: update in backend
        const body = {
          edited_by: loggedInUser.id,
          product_name: rowToSave.productFamily,
          current_price: rowToSave.current_price,
          proposed_price: rowToSave.proposed_price,
          price_change_type: rowToSave.priceChangeType,
          price_change_reason: rowToSave.priceChangeReason,
        };
        const res = await fetch(`/api/pcrs/${rowToSave.backendId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          alert(`Failed to save: ${err.detail || err.error || 'Unknown error'}`);
          return;
        }
      } else {
        // New draft (no backendId): create in backend as draft via POST with save_as_draft
        const productSkus = rowToSave.sku
          ? String(rowToSave.sku).split(',').map((s) => s.trim()).filter(Boolean)
          : rowToSave.product_skus ? [rowToSave.product_skus] : [rowToSave.id];
        const body = {
          submitted_by: loggedInUser.id,
          pcr_id: rowToSave.id,
          country: rowToSave.country || '',
          brand: rowToSave.productFamily || '',
          product_skus: productSkus.length ? productSkus : [rowToSave.id],
          product_name: rowToSave.productFamily,
          channel: rowToSave.channel || 'Retail',
          price_type: rowToSave.price_type || 'NSP Minimum',
          current_price: rowToSave.current_price,
          proposed_price: rowToSave.proposed_price,
          price_change_type: rowToSave.priceChangeType,
          price_change_reason: rowToSave.priceChangeReason,
          save_as_draft: true,
        };
        const res = await fetch('/api/pcrs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          alert(`Failed to save draft: ${err.detail || err.error || 'Unknown error'}`);
          return;
        }
        const data = await res.json();
        rowToSave.backendId = data.pcr_id;
      }
    } catch (e) {
      console.error(e);
      alert('Failed to save PCR');
      return;
    }

    const updatedData = allTableData.map((row) => (row.id === rowToSave.id ? rowToSave : row));
    setAllTableData(updatedData);
    setSelectedRow(rowToSave);
    loadPcrsFromApi(loggedInUser.id, loggedInUser?.email ?? '');
    alert('Draft saved successfully.');
  }

  async function handleFinalise(pcrId) {
    const pcr = allTableData.find((r) => r.id === pcrId);
    if (!pcr?.backendId || !loggedInUser?.id) return;
    try {
      const res = await fetch(`/api/pcrs/${pcr.backendId}/finalise`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
        body: JSON.stringify({ finalised_by: loggedInUser.id }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(`Failed to finalise: ${err.detail || err.error || 'Unknown error'}`);
        return;
      }
      const updatedData = allTableData.map((row) =>
        row.id === pcrId ? { ...row, approvalStatus: 'Finalized' } : row
      );
      setAllTableData(updatedData);
      if (selectedRow?.id === pcrId) setSelectedRow(updatedData.find((r) => r.id === pcrId));
      loadPcrsFromApi(loggedInUser?.id, loggedInUser?.email ?? '');
      alert('PCR finalised.');
    } catch (e) {
      console.error(e);
      alert('Failed to finalise PCR');
    }
  }

  async function handleRegionalEdit(pcrId, formData) {
    const pcr = allTableData.find((r) => r.id === pcrId);
    if (!pcr?.backendId || !loggedInUser?.id) return;
    try {
      const body = {
        edited_by: loggedInUser.id,
        price_change_type: formData?.priceChangeType ?? pcr.priceChangeType,
        price_change_reason: formData?.priceChangeReason ?? pcr.priceChangeReason,
      };
      const res = await fetch(`/api/pcrs/${pcr.backendId}/regional-edit`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-User-Id': String(loggedInUser.id) },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(`Failed to save: ${err.detail || err.error || 'Unknown error'}`);
        return;
      }
      const updatedData = allTableData.map((row) =>
        row.id === pcrId ? { ...row, ...body, priceChangeType: body.price_change_type, priceChangeReason: body.price_change_reason } : row
      );
      setAllTableData(updatedData);
      if (selectedRow?.id === pcrId) setSelectedRow(updatedData.find((r) => r.id === pcrId));
      alert('Regional edit saved.');
    } catch (e) {
      console.error(e);
      alert('Failed to save regional edit');
    }
  }


  function applyFilters() {
    let filtered = allTableData.filter(row => {
      // First check if user has permission to see this row
      if (row.approvalStatus === 'Draft' && row.createdBy !== loggedInUser?.email) {
        return false;
      }
      
      return (
        (!filters.priceRequestId ||
          row.id.toLowerCase().includes(filters.priceRequestId.toLowerCase())) &&

        (!filters.approvalStatus ||
          row.approvalStatus === filters.approvalStatus) &&

        (!filters.country ||
          row.country.toLowerCase().includes(filters.country.toLowerCase())) &&

        (!filters.productFamily ||
          row.productFamily.toLowerCase().includes(filters.productFamily.toLowerCase())) &&

        (!filters.priceChangeType ||
          row.priceChangeType === filters.priceChangeType) &&

        (!filters.submitter ||
          row.name.toLowerCase().includes(filters.submitter.toLowerCase())) &&

        (!filters.priceChangeReason ||
          row.priceChangeReason === filters.priceChangeReason) &&

        (!filters.autoApproved || row.autoApproved === true)
      );
    });

    setTableData(filtered);
    setCurrentPage(1); 
  }

  return (
    <div className="min-h-screen bg-purple-600 p-5">
      
      {/* New Entry Modal */}
      {showNewModal && (
    
        <div className="fixed inset-0 flex items-center justify-center z-50">

          <div className="bg-white rounded-lg shadow-xl p-6 w-96 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4 text-purple-600">Create New PCR</h2>
            
            <div className="space-y-4">
              {/* Region (optional filter) from backend (product-360/regions) */}
              <div>
                <label className="block mb-2 font-medium text-gray-700">Region (optional)</label>
                <select
                  value={createModalSelectedRegion}
                  onChange={(e) => {
                    setCreateModalSelectedRegion(e.target.value);
                    setNewEntry((prev) => ({ ...prev, countries: [], brand: '', sku: [] }));
                  }}
                  className="w-full p-2 border border-gray-300 rounded bg-white"
                >
                  <option value="">All regions</option>
                  {createModalRegionsLoading ? (
                    <option disabled>Loading…</option>
                  ) : (
                    createModalRegions.map((r) => (
                      <option key={r.code} value={r.code}>{r.name} ({r.code})</option>
                    ))
                  )}
                </select>
              </div>
              {/* Countries from backend (product-360/countries); scoped by user role and optional region */}
              <div>
                <label className="block mb-2 font-medium text-gray-700">Countries (select one or more)</label>
                <div className="border border-gray-300 rounded p-3 space-y-2 bg-white">
                  {createModalCountriesLoading ? (
                    <p className="text-sm text-gray-500">Loading countries…</p>
                  ) : createModalCountries.length === 0 ? (
                    <p className="text-sm text-amber-600">No countries available. Ensure backend is running and your user has access.</p>
                  ) : (
                    createModalCountries.map((c) => (
                      <div key={c.code} className="flex items-center">
                        <input
                          type="checkbox"
                          id={`country-${c.code}`}
                          checked={newEntry.countries.includes(c.code)}
                          onChange={() => handleCountryToggle(c.code)}
                          className="mr-2 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <label htmlFor={`country-${c.code}`} className="text-sm text-gray-700 cursor-pointer">{c.name} ({c.code})</label>
                      </div>
                    ))
                  )}
                </div>
                {newEntry.countries.length > 0 && (
                  <p className="mt-2 text-sm text-purple-600">Selected: {newEntry.countries.map((code) => countryLabel(code)).join(', ')}</p>
                )}
              </div>
              
              {/* Brands from backend (product-360/brands) */}
              <div>
                <label className="block mb-2 font-medium text-gray-700">Brand</label>
                <select 
                  value={newEntry.brand}
                  onChange={handleBrandChange}
                  disabled={newEntry.countries.length === 0}
                  className={`w-full p-2 border rounded ${
                    newEntry.countries.length === 0 ? "bg-gray-100 cursor-not-allowed" : "border-gray-300"
                  }`}
                >
                  <option value="">Select Brand</option>
                  {createModalBrandsLoading ? (
                    <option disabled>Loading…</option>
                  ) : (
                    createModalBrands.map((b) => (
                      <option key={b.brand} value={b.brand}>{b.brand}</option>
                    ))
                  )}
                </select>
              </div>
              
              {/* SKUs from backend (product-360/skus) */}
              <div>
                <label className="block mb-2 font-medium text-gray-700">SKU (Select Multiple)</label>
                <div
                  className={`border rounded p-3 space-y-2 ${
                    !newEntry.brand ? "bg-gray-100 cursor-not-allowed" : "border-gray-300 bg-white"
                  }`}
                >
                  {createModalSkusLoading ? (
                    <p className="text-sm text-gray-500">Loading SKUs…</p>
                  ) : (
                    createModalSkus.map((skuId) => (
                      <div key={skuId} className="flex items-center">
                        <input
                          type="checkbox"
                          id={skuId}
                          value={skuId}
                          checked={newEntry.sku.includes(skuId)}
                          onChange={() => handleSkuChange(skuId)}
                          disabled={!newEntry.brand}
                          className="mr-2 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <label htmlFor={skuId} className={`text-sm ${!newEntry.brand ? 'text-gray-400' : 'text-gray-700 cursor-pointer'}`}>
                          {skuId}
                        </label>
                      </div>
                    ))
                  )}
                </div>
  {newEntry.sku.length > 0 && (
    <p className="mt-2 text-sm text-purple-600">
      Selected: {newEntry.sku.join(', ')}
    </p>
  )}

              {/* Current & floor price (from backend; shown for first selected country) */}
              {firstCountry && newEntry.brand && newEntry.sku.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">Current & floor price (€)</p>
                  {createModalPricesLoading ? (
                    <p className="text-sm text-gray-500">Loading…</p>
                  ) : Object.keys(createModalSkuPrices).length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="text-left text-gray-600 border-b">
                            <th className="py-1 pr-2">SKU</th>
                            <th className="py-1 pr-2">Current (€)</th>
                            <th className="py-1">Floor (€)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {newEntry.sku.map((skuId) => {
                            const p = createModalSkuPrices[skuId];
                            return (
                              <tr key={skuId} className="border-b border-gray-100">
                                <td className="py-1.5 pr-2 font-medium">{skuId}</td>
                                <td className="py-1.5 pr-2">{p?.current_price_eur != null ? p.current_price_eur.toFixed(2) : '–'}</td>
                                <td className="py-1.5">{p?.floor_price_eur != null ? p.floor_price_eur.toFixed(2) : '–'}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No prices in backend for this context. Add floor/current in Admin or seed.</p>
                  )}
                </div>
              )}
</div>
            </div>
            
            {/* Buttons */}
            <div className="flex gap-3 mt-6">
              <button 
                onClick={() => {
                  setShowNewModal(false);
                  setNewEntry({ countries: [], brand: '', sku: [] });
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button 
                onClick={handleAddEntry}
                className="flex-1 px-4 py-2 bg-purple-600 text-white font-medium rounded hover:bg-purple-700"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Show Detail Page if user clicked on a row */}
      {showDetailPage ? (
        <DetailPage 
          row={selectedRow} 
          onBack={goBackToTable} 
          loggedInUser={loggedInUser} 
          onSummit={handleSummitPCR} 
          onSave={handleSavePCR}
          onLocalApprove={handleLocalApprove}
          onLocalReject={handleLocalReject}
          onRegionalApprove={handleRegionalApprove}
          onRegionalReject={handleRegionalReject}
          onEscalateToGlobal={handleEscalateToGlobal}
          onGlobalApprove={handleGlobalApprove}
          onGlobalReject={handleGlobalReject}
          onResubmit={handleResubmit}
        />
      ) : (
        <>
          {/* Filter Section - Only shows when showFilters is true */}
           
          {showFilters && (
            <div className="bg-white p-5 mb-5 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4">Filters</h3>
              
              {/* Filter Row 1 */}
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div>
                  <label className="block mb-1 font-medium">Price Request ID</label>
                  <input
  type="text"
  placeholder="Enter ID"
  value={filters.priceRequestId}
  onChange={(e) =>
    setFilters({ ...filters, priceRequestId: e.target.value })
  }
  className="w-full p-2 border border-gray-300 rounded"
/>

                </div>
                
                <div>
                  <label className="block mb-1 font-medium">Approval Status</label>
                  <select
  value={filters.approvalStatus}
  onChange={(e) =>
    setFilters({ ...filters, approvalStatus: e.target.value })
  }
  className="w-full p-2 border border-gray-300 rounded"
>
  <option value="">Choose Status</option>
  <option value="Draft">Draft</option>
  <option value="Submitted for Local Approval">Submitted for Local Approval</option>
  <option value="Pending">Pending</option>
  <option value="Approved">Approved</option>
  <option value="Escalated to Global">Escalated to Global</option>
  <option value="Rejected by Local">Rejected by Local</option>
  <option value="Rejected by Regional">Rejected by Regional</option>
  <option value="Rejected by Global">Rejected by Global</option>
  <option value="Finalized">Finalized</option>
</select>

                </div>
                
                <div>
                  <label className="block mb-1 font-medium">Country</label>
                  <input
  type="text"
  placeholder="Search country"
  value={filters.country}
  onChange={(e) =>
    setFilters({ ...filters, country: e.target.value })
  }
  className="w-full p-2 border border-gray-300 rounded"
/>

                </div>
                
                <div>
                  <label className="block mb-1 font-medium">Product Family</label>
                   <input
      type="text"
      placeholder="Search product"
      value={filters.productFamily}
      onChange={(e) =>
        setFilters({ ...filters, productFamily: e.target.value })
      }
      className="w-full p-2 border border-gray-300 rounded"
    />
                </div>
              </div>

              {/* Filter Row 2 */}
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div>
                  <label className="block mb-1 font-medium">Price Change Type</label>
                   <select
      value={filters.priceChangeType}
      onChange={(e) =>
        setFilters({ ...filters, priceChangeType: e.target.value })
      }
      className="w-full p-2 border border-gray-300 rounded"
    >
                    <option value="">Choose Type</option>
                    {PRICE_CHANGE_TYPES.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block mb-1 font-medium">Submitter</label>
                    <input
      type="text"
      placeholder="Search submitter"
      value={filters.submitter}
      onChange={(e) =>
        setFilters({ ...filters, submitter: e.target.value })
      }
      className="w-full p-2 border border-gray-300 rounded"
    />
                </div>
                
                <div>
                  <label className="block mb-1 font-medium">Approval Days</label>
                   <input
      type="text"
      placeholder="Enter days"
      value={filters.approvalDays}
      onChange={(e) =>
        setFilters({ ...filters, approvalDays: e.target.value })
      }
      className="w-full p-2 border border-gray-300 rounded"
    />
                </div>
                
                <div>
                  <label className="block mb-1 font-medium">Price Change Reason</label>
                   <select
      value={filters.priceChangeReason}
      onChange={(e) =>
        setFilters({ ...filters, priceChangeReason: e.target.value })
      }
      className="w-full p-2 border border-gray-300 rounded"
    >
                    <option value="">Choose Reason</option>
                    {PRICE_CHANGE_REASONS.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Filter Row 3 */}
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div>
                  <label className="block mb-1 font-medium">Submitted From Date</label>
                   <input
      type="date"
      value={filters.submittedFromDate}
      onChange={(e) =>
        setFilters({ ...filters, submittedFromDate: e.target.value })
      }
      className="w-full p-2 border border-gray-300 rounded"
    />
                </div>
                
                <div>
                  <label className="block mb-1 font-medium">Auto Approved?</label>
                  <div className="mt-2">
                         <input
        type="checkbox"
        checked={filters.autoApproved}
        onChange={(e) =>
          setFilters({
            ...filters,
            autoApproved: e.target.checked,
          })
        }
        className="mr-2"
      />

                    <span>Auto Approved</span>
                  </div>
                </div>
                
                <div>
                  <label className="block mb-1 font-medium">Submitted To Date</label>
                    <input
      type="date"
      value={filters.submittedToDate}
      onChange={(e) =>
        setFilters({ ...filters, submittedToDate: e.target.value })
      }
      className="w-full p-2 border border-gray-300 rounded"
    />
                </div>
              </div>

              {/* Filter Buttons */}
              <div className="text-right mt-4">
                <button
                   onClick={() =>
      setFilters(initialFilters)
    }
                 className="px-5 py-2 bg-gray-200 text-black font-medium rounded mr-2 hover:bg-purple-600 hover:text-white hover:cursor-pointer">
                  Clear
                </button>
                <button
                onClick={applyFilters}
                className="px-5 py-2 bg-gray-200 text-black font-medium rounded mr-2 hover:bg-purple-600 hover:text-white hover:cursor-pointer">
                  Search
                </button>
              </div>
            </div>
          )}

          {/* Table Section */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
           
            
            {/* Table Header with Buttons */}
           
            <div className="bg-gray-50 p-4 border-b flex items-center gap-2">
                {loggedInUser?.role === "LOCAL USER" && (
                    <button onClick={() => setShowNewModal(true)} className="px-5 py-2 bg-gray-200 text-black font-medium
                     rounded hover:bg-purple-600 hover:text-white mr-auto hover:cursor-pointer">
                        New</button>
                )}

             <div className="ml-auto flex gap-2">  
                
              <button 
                onClick={() => setShowFilters(!showFilters)}
                className="px-5 py-2 bg-gray-200 text-black font-medium rounded mr-2 hover:bg-purple-600 hover:text-white hover:cursor-pointer">
                {showFilters ? 'Hide Filters' : 'Show Filters'}
              </button>
              <button
                onClick={() => loggedInUser?.id && loadPcrsFromApi(loggedInUser.id, loggedInUser?.email ?? '')}
                disabled={pcrsLoading}
                className="px-5 py-2 bg-gray-200 text-black font-medium rounded mr-2 hover:bg-purple-600 hover:text-white hover:cursor-pointer disabled:opacity-50"
              >
                {pcrsLoading ? 'Loading...' : 'Refresh'}
              </button>
              </div>
            </div>
            

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b-2">
                  <tr>
                    <th className="p-3 text-left">
                      <input type="checkbox" />
                    </th>
                    <th className="p-3 text-left text-purple-600 font-medium">Price Request ID</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Country</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Product Family</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Name</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Price Change Type</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Price Change Reason</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Current Price (€)</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Floor Price (€)</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Proposed Price (€)</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Approval Status</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Submitted Date</th>
                    <th className="p-3 text-left text-purple-600 font-medium">Auto Approved?</th>
                  </tr>
                </thead>
                <tbody>
                  {pcrsLoading ? (
                    <tr><td colSpan={12} className="p-6 text-center text-gray-500">Loading PCRs...</td></tr>
                  ) : tableData.length === 0 ? (
                    <tr><td colSpan={12} className="p-6 text-center text-gray-500">No PCRs found. Log in (e.g. vishal@gmail.com for India) and ensure the backend is running on port 8000.</td></tr>
                  ) : currentRows.map((row, index) => (
                    <tr 
                      key={index} 
                      onClick={() => handleRowClick(row)}
                      className="border-b hover:bg-gray-50 cursor-pointer">
                      <td className="p-3" onClick={(e) => e.stopPropagation()}>
                        <input type="checkbox" />
                      </td>
                      <td className="p-3 text-purple-600 font-medium">{row.id}</td>
                      <td className="p-3">{countryLabel(row.country) || row.country}</td>
                      <td className="p-3">{row.productFamily}</td>
                      <td className="p-3">{row.name}</td>
                      <td className="p-3">{row.priceChangeType}</td>
                      <td className="p-3">{row.priceChangeReason}</td>
                      <td className="p-3">{row.current_price ?? '–'}</td>
                      <td className="p-3">{row.floor_price ?? '–'}</td>
                      <td className="p-3">{row.proposed_price ?? '–'}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          row.approvalStatus === 'Draft' 
                            ? 'bg-gray-200 text-gray-700'
                            : row.approvalStatus === 'Submitted for Local Approval'
                            ? 'bg-orange-100 text-orange-800'
                            : row.approvalStatus === 'Pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : row.approvalStatus === 'Approved'
                            ? 'bg-blue-100 text-blue-800'
                            : row.approvalStatus === 'Escalated to Global'
                            ? 'bg-purple-100 text-purple-800'
                            : row.approvalStatus === 'Rejected by Local'
                            ? 'bg-red-100 text-red-800'
                            : row.approvalStatus === 'Rejected by Regional'
                            ? 'bg-red-100 text-red-800'
                            : row.approvalStatus === 'Rejected by Global'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {row.approvalStatus}
                        </span>
                      </td>
                      <td className="p-3">{row.submittedDate}</td>
                      <td className="p-3">{row.autoApproved ? '✓' : ''}</td>
                    </tr>
                  )) }
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="bg-gray-50 px-4 py-3 border-t flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {indexOfFirstRow + 1} to {Math.min(indexOfLastRow, tableData.length)} of {tableData.length} entries
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={goToPreviousPage}
                  disabled={currentPage === 1}
                  className={`px-3 py-1 rounded ${
                    currentPage === 1
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-200 text-black hover:bg-purple-600 hover:text-white cursor-pointer'
                  }`}
                >
                  Previous
                </button>
                
                {/* Page Numbers */}
                <div className="flex gap-1">
                  {[...Array(totalPages)].map((_, index) => {
                    const pageNumber = index + 1;
                    
                    if (
                      pageNumber === 1 ||
                      pageNumber === totalPages ||
                      (pageNumber >= currentPage - 1 && pageNumber <= currentPage + 1)
                    ) {
                      return (
                        <button
                          key={pageNumber}
                          onClick={() => goToPage(pageNumber)}
                          className={`px-3 py-1 rounded ${
                            currentPage === pageNumber
                              ? 'bg-purple-600 text-white'
                              : 'bg-gray-200 text-black hover:bg-purple-600 hover:text-white cursor-pointer'
                          }`}
                        >
                          {pageNumber}
                        </button>
                      );
                    } else if (
                      pageNumber === currentPage - 2 ||
                      pageNumber === currentPage + 2
                    ) {
                      return <span key={pageNumber} className="px-2">...</span>;
                    }
                    return null;
                  })}
                </div>
                
                <button
                  onClick={goToNextPage}
                  disabled={currentPage === totalPages}
                  className={`px-3 py-1 rounded ${
                    currentPage === totalPages
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      : 'bg-gray-200 text-black hover:bg-purple-600 hover:text-white cursor-pointer'
                  }`}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}


function ActionsDropdown({loggedInUser, row, formData, onSummit, onLocalApprove, onLocalReject, onRegionalApprove, onRegionalReject, onEscalateToGlobal, onGlobalApprove, onGlobalReject, onResubmit}) {
  const [open, setOpen] = useState(false);
  
  const isSummitDisabled = row?.approvalStatus !== "Draft";
  const isRegionalApprovalPending = row?.approvalStatus === "Pending";
  const isGlobalApprovalPending = row?.approvalStatus === "Escalated to Global" || (row?.approvalStatus === 'Pending' && row?.regionalDecision === 'Approved');
  
 
  const hasRegionalDecision = row?.regionalDecision !== undefined;
  const hasGlobalDecision = row?.globalDecision !== undefined;
  const hasEscalated = row?.escalatedToGlobal === true;
  
  
  const isRegionalApproveDisabled = !isRegionalApprovalPending || hasRegionalDecision || hasEscalated;
  const isRegionalRejectDisabled = !isRegionalApprovalPending || hasRegionalDecision || hasEscalated;
  
  
  const isEscalateDisabled = row?.approvalStatus !== 'Pending' || hasEscalated || hasRegionalDecision;
  
 
  const isGlobalApproveDisabled = !isGlobalApprovalPending || hasGlobalDecision;
  const isGlobalRejectDisabled = !isGlobalApprovalPending || hasGlobalDecision;
  
  const canResubmit = row?.approvalStatus === 'Rejected by Local' ||
                       row?.approvalStatus === 'Rejected by Regional' ||
                       row?.approvalStatus === 'Rejected by Global' ||
                       row?.approvalStatus === 'Draft';

  return (
    <div className="relative inline-block text-left">
     
      <button
        onClick={() => setOpen(!open)}
        className="bg-gray-200 text-black font-medium px-4 py-2 rounded-md text-sm flex items-center gap-2 hover:bg-purple-600 hover:text-white hover:cursor-pointer"
      >
        Actions
        <span>▼</span>
      </button>

      
      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-white border rounded-md shadow-lg z-10 max-h-96 overflow-y-auto">
          
          
          {loggedInUser?.role === "REGIONAL USER" && (
            <>
              <div
                onClick={() => {
                  if (isRegionalApproveDisabled) return;
                  onRegionalApprove(row.id);
                  setOpen(false);
                }}
                className={`flex items-center gap-2 px-4 py-2 text-sm ${
                  isRegionalApproveDisabled
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'text-white bg-green-600 hover:bg-green-700 cursor-pointer'
                }`}
              >
                ✓ Approve (Regional)
              </div>

              <div
                onClick={() => {
                  if (isRegionalRejectDisabled) return;
                  onRegionalReject(row.id);
                  setOpen(false);
                }}
                className={`flex items-center gap-2 px-4 py-2 text-sm ${
                  isRegionalRejectDisabled
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'text-white bg-red-600 hover:bg-red-700 cursor-pointer'
                }`}
              >
                ✕ Reject (Regional)
              </div>

             
              <div
                onClick={() => {
                  if (isEscalateDisabled) return;
                  onEscalateToGlobal(row.id);
                  setOpen(false);
                }}
                className={`flex items-center gap-2 px-4 py-2 text-sm rounded ${
                  isEscalateDisabled
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'bg-purple-600 text-white hover:bg-purple-700 cursor-pointer'
                }`}
              >
                ⬆ Escalate To Global
              </div>
            </>
          )}

          
          {loggedInUser?.role === "GLOBAL USER" && (
            <>
              <div
                onClick={() => {
                  if (isGlobalApproveDisabled) return;
                  onGlobalApprove(row.id);
                  setOpen(false);
                }}
                className={`flex items-center gap-2 px-4 py-2 text-sm ${
                  isGlobalApproveDisabled
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'text-white bg-green-600 hover:bg-green-700 cursor-pointer'
                }`}
              >
                ✓ Approve (Global)
              </div>

              <div
                onClick={() => {
                  if (isGlobalRejectDisabled) return;
                  onGlobalReject(row.id);
                  setOpen(false);
                }}
                className={`flex items-center gap-2 px-4 py-2 text-sm ${
                  isGlobalRejectDisabled
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'text-white bg-red-600 hover:bg-red-700 cursor-pointer'
                }`}
              >
                ✕ Reject (Global)
              </div>
            </>
          )}
          
          
          {(loggedInUser?.role === "LOCAL USER" || loggedInUser?.role === "REGIONAL USER") && (
            <div
              onClick={() => {
                if (isSummitDisabled) return;
                onSummit(row.id, formData ?? undefined);
                setOpen(false);
              }}
              className={`flex items-center gap-2 px-4 py-2 text-sm rounded cursor-pointer ${
                isSummitDisabled
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                  : "bg-blue-600 text-white hover:bg-blue-700"
              }`}
            >
              ✓ Submit
            </div>
          )}

         
          {(loggedInUser?.role === "LOCAL USER" || loggedInUser?.role === "REGIONAL USER") && canResubmit && (
            <div
              onClick={() => {
                onResubmit(row.id);
                setOpen(false);
              }}
              className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
            >
              🔁 Re-Submit
            </div>
          )}

         
          <div
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
          >
            ⬆ Export
          </div>

          
          <div
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer border-t"
          >
            ✕ Close
          </div>
        </div>
      )}
    </div>
  );
}


function ProgressBar({ status }) {
 
  const getFirstBarLabel = () => {
    if (status === 'Draft' || status === 'Submitted for Local Approval') return 'Draft';
    if (status === 'Pending') return 'Pending'; // Waiting for Regional
    if (status === 'Escalated to Global') return 'Escalated to Global'; // Waiting for Global – clear next step
    if (status === 'Approved' || status === 'Finalized') return 'Pending'; // Already past first stage
    if (status === 'Rejected by Local') return 'Rejected';
    if (status === 'Rejected by Regional') return 'Rejected';
    if (status === 'Rejected by Global') return 'Rejected';
    return 'Draft';
  };

  const getCurrentStageIndex = () => {
    if (status === 'Draft' || status === 'Submitted for Local Approval') return 0;
    if (status === 'Pending' || status === 'Escalated to Global') return 0; // Still on first stage until globally approved
    if (status === 'Approved') return 1;
    if (status === 'Finalized') return 2;
    if (status === 'Rejected by Local' || status === 'Rejected by Regional' || status === 'Rejected by Global') return 0;
    return -1;
  };

  const stages = [
    getFirstBarLabel(),
    'Approved',
    'Finalized'
  ];

  const currentStageIndex = getCurrentStageIndex();
  
  const getStageStyle = (stageIndex) => {
    if ((status === 'Rejected by Local' || status === 'Rejected by Regional') && stageIndex === 0) {
      return {
        bg: 'bg-red-500',
        text: 'text-white',
        content: 'Rejected'
      };
    }
    
    if (stageIndex <= currentStageIndex) {
      const colors = [
        'bg-purple-500',    
        'bg-purple-600',    
        'bg-purple-800'     
      ];
      return {
        bg: colors[stageIndex],
        text: 'text-white',
        content: stages[stageIndex]
      };
    } else {
      return {
        bg: 'bg-gray-300',
        text: 'text-gray-600',
        content: stages[stageIndex]
      };
    }
  };
  
  return (
    <div className="bg-white border-b">
      <div className="flex">
        {stages.map((stage, index) => {
          const style = getStageStyle(index);
          const isFirst = index === 0;
          const isLast = index === stages.length - 1;
          
          return (
            <div
              key={index}
              className={`flex-1 ${style.bg} py-4 text-center ${style.text} font-semibold text-base ${!isLast ? '-mr-5' : ''}`}
              style={{
                clipPath: isFirst
                  ? 'polygon(0 0, calc(100% - 30px) 0, 100% 50%, calc(100% - 30px) 100%, 0 100%)'
                  : isLast
                  ? 'polygon(0 0, 100% 0, 100% 100%, 0 100%, 30px 50%)'
                  : 'polygon(0 0, calc(100% - 30px) 0, 100% 50%, calc(100% - 30px) 100%, 0 100%, 30px 50%)'
              }}
            >
              {style.content}
            </div>
          );
        })}
      </div>
    </div>
  );
}


function DetailPage({ row, onBack, loggedInUser, onSummit, onSave, onLocalApprove, onLocalReject, onRegionalApprove, onRegionalReject, onEscalateToGlobal, onGlobalApprove, onGlobalReject, onResubmit }) {

  const [formData, setFormData] = useState(row);
  const [pcrDetail, setPcrDetail] = useState(null);
  const [pcrDetailLoaded, setPcrDetailLoaded] = useState(false);

  const isEditable = row.approvalStatus === 'Draft';

  useEffect(() => {
    setFormData(prev => ({
      ...row,
      attachments: Array.isArray(row.attachments) ? row.attachments : [],
      priceProposalData: prev.priceProposalData ?? row.priceProposalData
    }));
  }, [row]);

  // Load live CP/FP/PP from backend so Local/Regional/Global see current and floor from history + MDGM
  useEffect(() => {
    const id = row?.backendId || row?.id;
    if (!id || !loggedInUser?.id) return;
    setPcrDetailLoaded(false);
    let cancelled = false;
    fetch(`/api/pcrs/${id}`, { headers: { 'X-User-Id': String(loggedInUser.id) } })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!cancelled) {
          setPcrDetail(data || {});
          setPcrDetailLoaded(true);
        }
      })
      .catch(() => { if (!cancelled) setPcrDetailLoaded(true); });
    return () => { cancelled = true; };
  }, [row?.id, row?.backendId, loggedInUser?.id]);

  return (
    <div className="min-h-screen bg-gray-100">

      {/* ================= TOP HEADER ================= */}
      <div className="bg-white border-b px-6 py-3 flex items-center justify-between">
        <h1 className="text-lg font-medium text-purple-600">
            {row.id}: {row.productFamily} in {(row.country && { IN: 'India', JP: 'Japan', AL: 'Albania', BA: 'Bosnia' }[row.country]) || row.country}
        </h1>

        <div className="flex items-center gap-3">
          <button className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">
            FAQs
          </button>
          {(loggedInUser?.role === "REGIONAL USER" ||
  loggedInUser?.role === "GLOBAL USER") && (
          <button className="bg-gray-200 text-black font-medium px-4 py-2 rounded-md text-sm flex items-center gap-2 hover:bg-purple-600 hover:text-white hover:cursor-pointer">
            Run IRP
          </button>
          )}
          <button
            onClick={() => isEditable && onSave(formData)}  
            className={`font-medium px-4 py-2 rounded-md text-sm flex items-center gap-2 ${
              isEditable
                ? 'bg-gray-200 text-black hover:bg-purple-600 hover:text-white hover:cursor-pointer'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'  
            }`}
            disabled={!isEditable}>  
            Save
          </button>
          <ActionsDropdown 
            loggedInUser={loggedInUser} 
            row={row} 
            formData={formData}
            onSummit={onSummit}
            onLocalApprove={onLocalApprove}
            onLocalReject={onLocalReject}
            onRegionalApprove={onRegionalApprove}
            onRegionalReject={onRegionalReject}
            onEscalateToGlobal={onEscalateToGlobal}
            onGlobalApprove={onGlobalApprove}
            onGlobalReject={onGlobalReject}
            onResubmit={onResubmit}
          />
        </div>
      </div>
      
      
      <ProgressBar status={row.approvalStatus} />

      {/* Pricing per SKU (Current / Floor / Proposed) from backend */}
      <div className="bg-white mx-4 mt-4 p-4 rounded shadow">
        <h3 className="text-sm font-semibold text-gray-800 mb-2">Pricing per SKU (Current / Floor / Proposed)</h3>
        {!pcrDetailLoaded && (row?.backendId || row?.id) ? (
          <p className="text-sm text-gray-500">Loading pricing...</p>
        ) : pcrDetail?.skus_pricing?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-600">
                  <th className="py-2 pr-4">SKU</th>
                  <th className="py-2 pr-4">Current (€)</th>
                  <th className="py-2 pr-4">Floor (€)</th>
                  <th className="py-2">Proposed (€)</th>
                </tr>
              </thead>
              <tbody>
                {pcrDetail.skus_pricing.map((sp) => (
                  <tr key={sp.sku_id} className="border-b">
                    <td className="py-2 pr-4">{sp.sku_id}</td>
                    <td className="py-2 pr-4">{sp.current_price_eur != null ? sp.current_price_eur.toFixed(2) : '–'}</td>
                    <td className="py-2 pr-4">{sp.floor_price_eur != null ? sp.floor_price_eur.toFixed(2) : '–'}</td>
                    <td className="py-2">{sp.proposed_price_eur != null ? sp.proposed_price_eur.toFixed(2) : '–'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">No per-SKU pricing for this PCR (open a PCR with SKUs and pricing context).</p>
        )}
      </div>

      {/* ================= MAIN LAYOUT ================= */}
      <div className="flex">

        {/* -------- LEFT SIDE - TABS & CONTENT -------- */}
        <div className="flex-1 overflow-auto">
          <div className="bg-white m-4 rounded shadow">

            {/* -------- TABS -------- */}
            <div className="flex border-b">
              <Tab to="." label="SUMMARY" end/>
              <Tab to="PriceProposalPage" label="PRICE PROPOSAL" />
              {(loggedInUser?.role === "REGIONAL USER" ||
                loggedInUser?.role === "GLOBAL USER") && (
              <>
              
              <Tab to="RecommendationPage" label="RECOMMENDATION" />
              </>
              )}
            </div>

            {/* -------- TAB CONTENT -------- */}
            <div className="p-4">
             <Outlet context={{ row, formData, setFormData, isEditable, pcrDetail }} />


            </div>
          </div>
        </div>

        {/* -------- RIGHT SIDE - APPROVERS -------- */}
        <div className="w-80 bg-white border-l shadow-lg overflow-y-auto h-full mr-4 mt-4 mb-4">
          <div className="p-5">
            {/* Header with Menu Button */}
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-base font-bold text-gray-800">APPROVERS</h3>
             
            </div>
            
            {/* Local MAP */}
            <div className="mb-8">
              <div className="flex items-center mb-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-3 ${
                  
                  (row.approvalStatus === 'Pending' || row.approvalStatus === 'Escalated to Global' || row.approvalStatus === 'Approved' || row.approvalStatus === 'Finalized')
                    ? 'bg-green-500'
                  
                  : row.approvalStatus === 'Rejected by Local'
                    ? 'bg-red-500'
                  
                  : (row.approvalStatus === 'Draft' || row.approvalStatus === 'Submitted for Local Approval')
                    ? 'border-2 border-blue-500'
                 
                  : 'border-2 border-gray-400'
                }`}>
                  {/* Green tick for approved */}
                  {(row.approvalStatus === 'Pending' || row.approvalStatus === 'Escalated to Global' || row.approvalStatus === 'Approved' || row.approvalStatus === 'Finalized') && (
                    <span className="text-white text-sm font-bold">✓</span>
                  )}
                  {/* Red X for rejected */}
                  {row.approvalStatus === 'Rejected by Local' && (
                    <span className="text-white text-sm font-bold">✕</span>
                  )}
                  {/* Blue dot for current stage */}
                  {(row.approvalStatus === 'Draft' || row.approvalStatus === 'Submitted for Local Approval') && (
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  )}
                </div>
                <span className="font-semibold text-sm text-gray-800">Local MAP</span>
              </div>
              <div className="ml-9 space-y-2">
                <div className="flex items-center text-sm text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  <span>Seria Muis</span>
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  <span>Lian Eres</span>
                </div>
              </div>
            </div>
            
            {/* Regional MAP */}
            <div className="mb-8">
              <div className="flex items-center mb-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-3 ${
                  
                  (row.approvalStatus === 'Escalated to Global' || row.approvalStatus === 'Approved' || row.approvalStatus === 'Finalized')
                    ? 'bg-green-500'
                 
                  : row.approvalStatus === 'Rejected by Regional'
                    ? 'bg-red-500'
                  
                  : row.approvalStatus === 'Pending'
                    ? 'border-2 border-blue-500'
                  
                  : 'border-2 border-gray-400'
                }`}>
                  {/* Green tick for approved/escalated */}
                  {(row.approvalStatus === 'Escalated to Global' || row.approvalStatus === 'Approved' || row.approvalStatus === 'Finalized') && (
                    <span className="text-white text-sm font-bold">✓</span>
                  )}
                  {/* Red X for rejected */}
                  {row.approvalStatus === 'Rejected by Regional' && (
                    <span className="text-white text-sm font-bold">✕</span>
                  )}
                  {/* Blue dot for current stage */}
                  {row.approvalStatus === 'Pending' && (
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  )}
                </div>
                <span className="font-semibold text-sm text-gray-800">Regional MAP</span>
              </div>
              <div className="ml-9 space-y-2">
                <div className="flex items-center text-sm text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  <span>Sameer Huns</span>
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  <span>Frius Huang</span>
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  <span>Gill Numo</span>
                </div>
                <div className="flex items-center text-sm text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  <span>Deria Matt</span>
                </div>
              </div>
            </div>
            
            {/* Global MAP */}
            <div className="mb-8">
              <div className="flex items-center mb-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-3 ${
                  
                  (row.approvalStatus === 'Approved' || row.approvalStatus === 'Finalized')
                    ? 'bg-green-500'
                  
                  : row.approvalStatus === 'Escalated to Global'
                    ? 'border-2 border-blue-500'
                  
                  : 'border-2 border-gray-400'
                }`}>
                  {/* Green tick for approved */}
                  {(row.approvalStatus === 'Approved' || row.approvalStatus === 'Finalized') && (
                    <span className="text-white text-sm font-bold">✓</span>
                  )}
                  {/* Blue dot for current stage */}
                  {row.approvalStatus === 'Escalated to Global' && (
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  )}
                </div>
                <span className="font-semibold text-sm text-gray-800">Global MAP</span>
              </div>
              <div className="ml-9">
                <div className="flex items-center text-sm text-gray-700">
                  <svg className="w-4 h-4 mr-2 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  <span>Raj Jush</span>
                </div>
              </div>
            </div>

            {/* Back Button */}
            <button 
              onClick={onBack}
              className="w-full mt-8 px-4 py-2 bg-gray-200 text-black text-sm font-medium rounded hover:bg-purple-600 hover:text-white">
              ← Back to Table
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


function Tab({ to, label, end = false }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex-1 px-4 py-3 text-sm font-medium text-center border-r last:border-r-0 
         ${
           isActive
             ? "bg-purple-900 text-white"
             : "bg-purple-600 text-white hover:bg-purple-500 "
         }`
      }
    >
      {label}
    </NavLink>
  );
}