import { useOutletContext } from 'react-router-dom';

const EscalationPage = () => {
    const row = useOutletContext();
    const NetFloorData = [
  {
    sku: row.productFamily,
    channel: 'Retail',
    Listprice: '5.678,21EUR',
    Listfloor: '',
    Escalation: 'No',
    GlobalRedLine:'NO',
    GlobalRedBrea:'NO',
  },
  {
    sku: row.productFamily,
    channel: 'Hospital',
    Listprice: '5.679,21EUR',
    Listfloor: '',
    Escalation: 'No',
    GlobalRedLine:'NO',
    GlobalRedBrea:'NO',
  },
  {
    sku: row.productFamily,
    channel: 'Distributor',
    Listprice: '5.687,21EUR',
    Listfloor: '',
    Escalation: 'No',
    GlobalRedLine:'NO',
    GlobalRedBrea:'NO',
  },
  {
    sku: row.productFamily,
    channel: 'Other',
    Listprice: '5.666,21EUR',
    Listfloor: '',
    Escalation: 'Escalation',
    GlobalRedLine:'NO',
    GlobalRedBrea:'NO',
  },
];

          const columns1= [
    { key: 'channel', label: 'Channel', info: true },
    { key: 'Listprice', label: 'Proposed List Price', info: true },
    { key: 'Listfloor', label: 'List Floor', info: true },
    { key: 'Escalation', label: 'Escalation', info: true },

  ];

   
  return (
    
     <div className="overflow-x-auto w-full">
        <h1 className="text-center font-bold ">List Floor</h1>
            <table className="w-full border border-gray-300 border-collapse min-w-[800px]">
            <thead>
            <tr className="bg-gray-50">
              <th className="text-left p-1 border border-gray-300 font-semibold text-gray-700 text-xs sm:text-sm sticky left-0 bg-gray-50 z-10 ">
                Product SKU
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
            
  {NetFloorData.map((row, index) => (
    <tr key={index} className="hover:bg-gray-50">
      <td className="p-2 sm:p-3 border border-gray-300 font-medium text-gray-700 text-xs sm:text-sm sticky left-0 bg-white z-10">
        {row.sku}
      </td>
      {columns1.map(col => (
        <td key={col.key} className={`p-2 sm:p-3 border border-gray-300 text-xs sm:text-sm ${
                    col.key === 'Escalation'
                      ? row[col.key] === 'No'
                        ? 'text-green-600 font-semibold'
                        : 'text-red-600 font-semibold'
                      : ''
                  }`}>
          {row[col.key]}
        </td>
      ))}
    </tr>
  ))}
</tbody>

                      
         

          </table>

       
        </div>
  )
}

export default EscalationPage