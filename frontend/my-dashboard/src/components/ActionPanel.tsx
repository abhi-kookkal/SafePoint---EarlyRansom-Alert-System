import { useState } from "react";
import api from "../api/client";

interface Props {
  endpointId: string;
}

export default function ActionPanel({ endpointId }: Props) {
  const [command, setCommand] = useState("kill");

  const sendAction = async () => {
    await api.post("/actions", { endpoint_id: endpointId, command });
    alert(`Action '${command}' sent to ${endpointId}`);
  };

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="text-lg font-semibold mb-2">Send Action to {endpointId}</h2>
      <select
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        className="border p-2 rounded mr-2"
      >
        <option value="kill">Kill Process</option>
        <option value="isolate">Isolate Endpoint</option>
        <option value="message">Send Message</option>
      </select>
      <button
        onClick={sendAction}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Send
      </button>
    </div>
  );
}
