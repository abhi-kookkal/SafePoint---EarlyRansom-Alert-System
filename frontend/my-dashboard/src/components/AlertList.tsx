interface Props {
    alerts: any[];
  }
  
  export default function AlertList({ alerts }: Props) {
    return (
      <div className="bg-white p-4 rounded shadow mb-4">
        <h2 className="text-lg font-semibold mb-2">Alerts</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-200 text-left">
              <th className="p-2">ID</th>
              <th className="p-2">Endpoint</th>
              <th className="p-2">Process</th>
              <th className="p-2">Risk</th>
              <th className="p-2">Reason</th>
              <th className="p-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id} className="border-b">
                <td className="p-2">{a.id}</td>
                <td className="p-2">{a.endpoint_id}</td>
                <td className="p-2">{a.process_name}</td>
                <td className={`p-2 font-bold ${a.risk_score >= 80 ? "text-red-600" : "text-green-600"}`}>
                  {a.risk_score}
                </td>
                <td className="p-2">{a.reason}</td>
                <td className="p-2">{a.action_taken || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  