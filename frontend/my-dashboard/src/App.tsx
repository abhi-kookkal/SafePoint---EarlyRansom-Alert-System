import { useEffect, useState } from "react";
import api from "./api/client";
import EndpointList from "./components/EndpointList";
import AlertList from "./components/AlertList";
import ActionPanel from "./components/ActionPanel";

function App() {
  const [endpoints, setEndpoints] = useState<any>({});
  const [alerts, setAlerts] = useState<any[]>([]);
  const [selectedEndpoint, setSelectedEndpoint] = useState<string | null>(null);

  const fetchData = async () => {
    const epRes = await api.get("/endpoints");
    setEndpoints(epRes.data);

    const alRes = await api.get("/alerts");
    setAlerts(alRes.data);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // auto-refresh
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <h1 className="text-2xl font-bold mb-4">🛡️ Ransomware Detection Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="col-span-1">
          <EndpointList endpoints={endpoints} setSelected={setSelectedEndpoint} />
        </div>
        <div className="col-span-2">
          <AlertList alerts={alerts} />
          {selectedEndpoint && (
            <ActionPanel endpointId={selectedEndpoint} />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
