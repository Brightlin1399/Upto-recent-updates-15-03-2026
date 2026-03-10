import { useState } from "react";
import { useOutletContext } from 'react-router-dom';


const RevenueImpactAccordion = () => {
    
         const [open, setOpen] = useState(false);
      const columns1= [
    { key: '2025', label: '2025', info: true },
    { key: '2026', label: '2026', info: true },
    { key: '2027', label: '2027', info: true },
  ];

  return (
    <div className="shadow-lg mt-4 ml-5 mr-5">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center p-3 bg-gray-100 text-left text-sm sm:text-base font-semibold hover:cursor-pointer"
      >
        <span>Revenue Impact vs Forecast</span>
        <span className="text-sm sm:text-base">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
         <div className="overflow-x-auto w-full">
            <table className="w-full border border-gray-300 border-collapse min-w-[800px]">
            <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-1 border border-gray-300 font-semibold text-gray-700 text-xs sm:text-sm sticky left-0 bg-gray-50 z-10 ">
                Scenario
              </th>
              {columns1.map(col => (
                <th key={col.key} className="text-left p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm min-w-[150px]">
                  <div className="flex items-center gap-1">
                    <span className="line-clamp-2">{col.label}</span>
                    
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Mandatory Row */}
       
                        <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Scenario-Approve
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
            
            </tr>
                        <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Scenario-Reject
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
          
            </tr>
            
                      
          </tbody>

          </table>
        </div>
      )}
    </div>
  );
    
}



const AllSKUDevelopmentAccordion = () => {
  const [open, setOpen] = useState(false);
      const columns1= [
    { key: '2025', label: '2025', info: true },
    { key: '2026', label: '2026', info: true },
    { key: '2027', label: '2027', info: true },
    { key: 'total', label: 'Total', info: true },
  ];

  return (
    <div className="shadow-lg mt-4 ml-5 mr-5">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center p-3 bg-gray-100 text-left text-sm sm:text-base font-semibold hover:cursor-pointer"
      >
        <span>All SKUs-Net Sales Development</span>
        <span className="text-sm sm:text-base">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
         <div className="overflow-x-auto w-full">
            <table className="w-full border border-gray-300 border-collapse min-w-[800px]">
            <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-1 border border-gray-300 font-semibold text-gray-700 text-xs sm:text-sm sticky left-0 bg-gray-50 z-10 ">
                Scenario
              </th>
              {columns1.map(col => (
                <th key={col.key} className="text-left p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm min-w-[150px]">
                  <div className="flex items-center gap-1">
                    <span className="line-clamp-2">{col.label}</span>
                    
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Mandatory Row */}
            <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Scenario-Forecast
              </td>
                            {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
             
            </tr>
                        <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Scenario-Approve
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
            
            </tr>
                        <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Scenario-Reject
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
          
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Incremental IRP Impact-Approve
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
            
            </tr>
                      
          </tbody>

          </table>
        </div>
      )}
    </div>
  );
};


const SalesForecastTable = () => {
  return (
    <div className="p-5 bg-gray-50 min-h-screen">
      <div className="overflow-x-auto w-full">
        <table className="w-full border-collapse bg-white shadow-sm">
          <thead>
            {/* First row - Years */}
            <tr className="bg-gray-100">
              <th rowSpan="2" className="border border-gray-300 p-3 text-left font-semibold text-gray-700 text-sm">
                Channel
              </th>
              <th colSpan="3" className="border border-gray-300 p-2 text-center font-semibold text-gray-700 text-sm">
                2025
              </th>
              <th colSpan="3" className="border border-gray-300 p-2 text-center font-semibold text-gray-700 text-sm">
                2026
              </th>
              <th colSpan="3" className="border border-gray-300 p-2 text-center font-semibold text-gray-700 text-sm">
                2027
              </th>
            </tr>
            {/* Second row - Column names */}
            <tr className="bg-gray-100">
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">Volume FY</th>
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">NSP Average</th>
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">Net Sales</th>
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">Volume FY</th>
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">NSP Average</th>
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">Net Sales</th>
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">Volume FY</th>
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">NSP Average</th>
              <th className="border border-gray-300 p-2 text-center text-gray-600 text-xs font-normal">Net Sales</th>
            </tr>
          </thead>
          <tbody>
           
            <tr>
              <td colSpan="10" className="border border-gray-300 p-2 text-center font-semibold text-gray-700 bg-gray-50 text-sm">
                Forecast
              </td>
            </tr>
            {/* Forecast Data Rows */}
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Retail</td>
              <td className="border border-gray-300 p-2 text-center text-sm">1</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm">10</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm">15</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Hospital</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Distributor</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Other</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>

            
            <tr>
              <td colSpan="10" className="border border-gray-300 p-2 text-center font-semibold text-gray-700 bg-gray-50 text-sm">
                Approve
              </td>
            </tr>
            {/* Approve Data Rows */}
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Retail</td>
              <td className="border border-gray-300 p-2 text-center text-sm">1</td>
              <td className="border border-gray-300 p-2 text-center text-sm">EUR 3,297.31</td>
              <td className="border border-gray-300 p-2 text-center text-sm">EUR 3,297.31</td>
              <td className="border border-gray-300 p-2 text-center text-sm">10</td>
              <td className="border border-gray-300 p-2 text-center text-sm">EUR 3,297.31</td>
              <td className="border border-gray-300 p-2 text-center text-sm">EUR 32,973.1</td>
              <td className="border border-gray-300 p-2 text-center text-sm">15</td>
              <td className="border border-gray-300 p-2 text-center text-sm">EUR 3,297.31</td>
              <td className="border border-gray-300 p-2 text-center text-sm">EUR 49,459.65</td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Hospital</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Distributor</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Other</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>

            {/* Section Label - Reject */}
            <tr>
              <td colSpan="10" className="border border-gray-300 p-2 text-center font-semibold text-gray-700 bg-gray-50 text-sm">
                Reject
              </td>
            </tr>
            {/* Reject Data Rows */}
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Retail</td>
              <td className="border border-gray-300 p-2 text-center text-sm">0</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm">0</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm">0</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Hospital</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Distributor</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="border border-gray-300 p-3 text-gray-700 text-sm">Other</td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
              <td className="border border-gray-300 p-2 text-center text-sm"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};


const MedicineSalesForecastAccordion = () => {
    const row = useOutletContext();

         const [open, setOpen] = useState(false);



  return (
    <div className="shadow-lg mt-2 ml-5 mr-5">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center p-3 bg-gray-100 text-left text-sm sm:text-base font-semibold hover:cursor-pointer"
      >
        <span>{row.productFamily}</span>
        <span className="text-sm sm:text-base">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <SalesForecastTable/>
    )}
    </div>
  )
}




const VolumeAccordion = () => {
  const [open, setOpen] = useState(false);

  return (
    <div className="shadow-lg mt-4">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center p-3 bg-gray-100 text-left text-sm sm:text-base font-semibold hover:cursor-pointer"
      >
        <span>Volume, NSP Average and Net Sales Development</span>
        <span className="text-sm sm:text-base">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div>
            <MedicineSalesForecastAccordion/>
            <AllSKUDevelopmentAccordion/>
            <RevenueImpactAccordion/>
        </div>
      )}
    </div>
  );
};




const MedicineGrossMarginAccordion = () => {
    const row = useOutletContext();
  const [open, setOpen] = useState(false);

    const columns1= [
    { key: 'NSPMinCurrent', label: 'NSP Min Current(%)', info: true },
    { key: 'NSPAvgCurrent', label: 'NSP Average Current(%)', info: true },
    { key: 'NSPMinApprove', label: 'NSP Min Approve Change(%)', info: true },
    { key: 'NSPAvgApprove', label: 'NSP Average Approve Change(%)', info: true },
  ];

  return (
    <div className="shadow-lg mt-2 ml-5 mr-5">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center p-3 bg-gray-100 text-left text-sm sm:text-base font-semibold hover:cursor-pointer"
      >
        <span>{row.productFamily}</span>
        <span className="text-sm sm:text-base">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="overflow-x-auto w-full">
            <table className="w-full border border-gray-300 border-collapse min-w-[800px]">
            <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-1 border border-gray-300 font-semibold text-gray-700 text-xs sm:text-sm sticky left-0 bg-gray-50 z-10 ">
                Channel
              </th>
              {columns1.map(col => (
                <th key={col.key} className="text-left p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm min-w-[150px]">
                  <div className="flex items-center gap-1">
                    <span className="line-clamp-2">{col.label}</span>
                    
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Mandatory Row */}
            <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Retail
              </td>
                            {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
             
            </tr>
                        <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Hospital
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
            
            </tr>
                        <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Distributor
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
          
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                Other
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
            
            </tr>
                        <tr className="hover:bg-gray-50">
              <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
                WeightedAverage
              </td>
                             {columns1.map(col => (
                <td key={col.key} className="p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm">
                 
                </td>
              ))}
          
            </tr>
            
          </tbody>

          </table>
        </div>
      )}
    </div>
  );
};




const GrossMarginAccordion = () => {
  const [open, setOpen] = useState(false);

  return (
    <div className="shadow-lg mt-4">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex justify-between items-center p-3 bg-gray-100 text-left text-sm sm:text-base font-semibold hover:cursor-pointer"
      >
        <span>Gross Margin</span>
        <span className="text-sm sm:text-base">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div>
            <MedicineGrossMarginAccordion/>
        </div>
      )}
    </div>
  );
};




const FinancialsPage = () => {
  return (
    <>
     <div className="flex justify-end">
        <button className="bg-blue-600 text-white p-1 rounded-md hover:bg-blue-800 hover:cursor-pointer">⟲ Refresh</button>
    </div>
     <GrossMarginAccordion/>
     <VolumeAccordion/>
    </>
   
  )
}

export default FinancialsPage