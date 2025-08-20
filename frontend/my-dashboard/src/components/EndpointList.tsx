interface Props {
    endpoints: any;
    setSelected: (id: string) => void;
  }
  
  export default function EndpointList({ endpoints, setSelected }: Props) {
    return (
      <div className="bg-white p-4 rounded shadow">
        <h2 className="text-lg font-semibold mb-2">Endpoints</h2>
        <ul>
          {Object.entries(endpoints).map(([id, ep]: any) => (
            <li
              key={id}
              className="p-2 border-b hover:bg-gray-100 cursor-pointer"
              onClick={() => setSelected(id)}
            >
              <span className="font-bold">{ep.name}</span> ({id})  
              <span className="ml-2 text-sm text-gray-500">[{ep.status}]</span>
            </li>
          ))}
        </ul>
      </div>
    );
  }
  