import { useEffect, useState } from "react";
import DashboardCard from "../components/DashboardCard";
import api from "../api/client";

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalEmployees: 0,
    activeThreats: 0,
    blockedIntrusions: 0,
  });

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await api.get("/stats"); 
        setStats(res.data);
      } catch (err) {
        console.error("Error fetching stats", err);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <DashboardCard title="Total Employees" value={stats.totalEmployees} />
      <DashboardCard title="Active Threats" value={stats.activeThreats} />
      <DashboardCard title="Blocked Intrusions" value={stats.blockedIntrusions} />
    </div>
  );
}
