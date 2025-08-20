export default function Navbar() {
    return (
      <nav className="w-full bg-blue-600 text-white px-6 py-3 flex justify-between items-center">
        <h1 className="text-xl font-bold">Enterprise Security Dashboard</h1>
        <button className="bg-white text-blue-600 px-4 py-1 rounded-lg shadow">
          Logout
        </button>
      </nav>
    );
  }
  