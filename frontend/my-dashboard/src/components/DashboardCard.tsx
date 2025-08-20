interface DashboardCardProps {
    title: string;
    value: string | number;
  }
  
  export default function DashboardCard({ title, value }: DashboardCardProps) {
    return (
      <div className="bg-white shadow-md rounded-xl p-6 flex flex-col items-center">
        <h3 className="text-gray-600 text-sm">{title}</h3>
        <p className="text-2xl font-bold mt-2">{value}</p>
      </div>
    );
  }
  