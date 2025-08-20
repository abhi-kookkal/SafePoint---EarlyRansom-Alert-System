export default function Sidebar() {
    return (
      <aside className="bg-gray-800 text-white w-64 min-h-screen p-4">
        <ul className="space-y-4">
          <li className="hover:bg-gray-700 p-2 rounded">Dashboard</li>
          <li className="hover:bg-gray-700 p-2 rounded">Employees</li>
          <li className="hover:bg-gray-700 p-2 rounded">Alerts</li>
          <li className="hover:bg-gray-700 p-2 rounded">Reports</li>
        </ul>
      </aside>
    );
  }
  