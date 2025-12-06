import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import {
  DollarSign,
  TrendingUp,
  Sparkles,
  Server,
  Database,
  HardDrive,
  Zap,
  ArrowRight,
  Building2,
} from "lucide-react";
import { getDashboard, triggerAnalysis, type DashboardData } from "../lib/api";
import {
  formatCurrency,
  formatPercent,
  SERVICE_COLORS,
  SERVICE_BG,
  CHART_COLORS,
} from "../lib/utils";
import MetricCard from "../components/MetricCard";
import LoadingSpinner from "../components/LoadingSpinner";

const SERVICE_ICONS: Record<string, any> = {
  EC2: Server,
  RDS: Database,
  S3: HardDrive,
  Lambda: Zap,
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const dashboardData = await getDashboard();
      setData(dashboardData);
    } catch (err) {
      setError("Failed to load dashboard data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      setAnalyzing(true);
      const report = await triggerAnalysis();
      navigate(`/reports/${report.id}`);
    } catch (err) {
      console.error("Analysis failed:", err);
      alert("Analysis failed. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error || "Failed to load data"}</p>
        <button onClick={loadDashboard} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  const pieData = data.services.map((s) => ({
    name: s.name,
    value: s.monthly_cost,
    percentage: s.percentage_of_total,
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Cloud Cost Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            Monitor and optimize your AWS spending
          </p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="btn-primary flex items-center gap-2"
        >
          <Sparkles className="h-4 w-4" />
          {analyzing ? "Analyzing..." : "Analyze with AI"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Monthly Spend"
          value={formatCurrency(data.total_monthly_spend)}
          trend={data.month_over_month_change}
          trendLabel="vs last month"
          icon={<DollarSign className="h-5 w-5 text-blue-600" />}
        />
        <MetricCard
          title="Optimization Potential"
          value={formatCurrency(data.optimization_potential)}
          subtitle="Estimated savings available"
          icon={<TrendingUp className="h-5 w-5 text-green-600" />}
          valueClassName="text-green-600"
        />
        <MetricCard
          title="Active Services"
          value={data.services.length}
          subtitle={`${data.services.reduce(
            (sum, s) => sum + s.resource_count,
            0
          )} total resources`}
          icon={<Server className="h-5 w-5 text-purple-600" />}
        />
        <MetricCard
          title="Projects"
          value={data?.departments?.length}
          subtitle="Cost centers tracked"
          icon={<Building2 className="h-5 w-5 text-orange-600" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Cost by Service */}
        <div className="bg-white shadow-md rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Cost by Service
          </h2>

          <div className="flex items-center gap-6">
            <div style={{ width: 260, height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={110}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={SERVICE_COLORS[entry.name] || CHART_COLORS[index]}
                        style={{ transition: "0.3s", cursor: "pointer" }}
                        onMouseEnter={(e) => (e.target.style.opacity = 0.7)}
                        onMouseLeave={(e) => (e.target.style.opacity = 1)}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{
                      borderRadius: 12,
                      padding: "10px 14px",
                      border: "none",
                      boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-3">
              {pieData.map((entry, index) => (
                <div key={entry.name} className="flex items-center gap-3">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{
                      backgroundColor:
                        SERVICE_COLORS[entry.name] || CHART_COLORS[index],
                    }}
                  ></span>
                  <span className="text-gray-700 text-sm">
                    {entry.name} — {entry.percentage.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Monthly Trend Chart */}
        <div className="bg-white shadow-md rounded-2xl p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Monthly Trend
          </h2>

          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={data.monthly_trend}
              margin={{ top: 10, right: 20, left: 0, bottom: 10 }}
            >
              {/* Soft background grid */}
              <CartesianGrid stroke="rgba(0,0,0,0.04)" vertical={false} />

              {/* Smooth fade gradient under line */}
              <defs>
                <linearGradient id="smoothGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="transparent" />
                </linearGradient>
              </defs>

              {/* Month labels */}
              <XAxis
                dataKey="month"
                tick={{ fontSize: 12, fill: "#6B7280" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => {
                  const [year, month] = value.split("-");
                  return new Date(year, month - 1).toLocaleDateString("en-US", {
                    month: "short",
                  });
                }}
              />

              {/* Y-axis formatting */}
              <YAxis
                tick={{ fontSize: 12, fill: "#6B7280" }}
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                tickLine={false}
                axisLine={false}
              />

              {/* Tooltip */}
              <Tooltip
                formatter={(value) => formatCurrency(value)}
                labelFormatter={(label) => {
                  const [year, month] = label.split("-");
                  return new Date(year, month - 1).toLocaleDateString("en-US", {
                    month: "long",
                    year: "numeric",
                  });
                }}
                contentStyle={{
                  borderRadius: 12,
                  border: "none",
                  padding: "10px 14px",
                  boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
                }}
              />

              {/* Smooth animated line */}
              <Line
                type="monotone"
                dataKey="total_cost"
                stroke="#3B82F6"
                strokeWidth={2}
                // fill="url(#smoothGradient)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Top Cost Drivers
            </h2>
            <span className="text-sm text-gray-500">Click to drill down</span>
          </div>
          <div className="space-y-3">
            {data.top_cost_drivers.map((driver, index) => {
              const Icon = SERVICE_ICONS[driver.name] || Server;
              return (
                <Link
                  key={driver.name}
                  to={`/services/${driver.name.toLowerCase()}`}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${SERVICE_BG[index]}20` }}
                    >
                      <Icon
                        className="h-5 w-5"
                        style={{ color: SERVICE_BG[index] }}
                      />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{driver.name}</p>
                      <p className="text-sm text-gray-500">
                        {driver.resource_count} resources
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">
                        {formatCurrency(driver.cost)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatPercent(driver.percentage)}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Project Spending
            </h2>
            <Link
              to="/departments"
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              View all
            </Link>
          </div>
          <div style={{ width: "100%", height: 256 }}>
            <ResponsiveContainer width="100%" height={256}>
              <BarChart data={data?.departments} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  type="number"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                  width={100}
                />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{
                    borderRadius: "8px",
                    border: "1px solid #e5e7eb",
                  }}
                />
                <Bar
                  dataKey="total_cost"
                  fill="#3B82F6"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-4">
            {data?.departments?.slice(0, 4)?.map((dept) => (
              <div
                key={dept.id}
                className="flex justify-between items-center text-sm"
              >
                <span className="text-gray-600">{dept.name}</span>
                <span className="font-medium text-gray-900">
                  {formatCurrency(dept.total_cost)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          All Services
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {data.services.map((service, index) => {
            const Icon = SERVICE_ICONS[index] || Server;
            return (
              <Link
                key={service.id}
                to={`/services/${service.name.toLowerCase()}`}
                className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all group"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="p-2 rounded-lg"
                    style={{ backgroundColor: `${SERVICE_BG[index]}20` }}
                  >
                    <Icon
                      className="h-5 w-5"
                      style={{ color: SERVICE_BG[index] }}
                    />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                      {service.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {service.service_type}
                    </p>
                  </div>
                </div>
                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-xl font-bold text-gray-900">
                      {formatCurrency(service.monthly_cost)}
                    </p>
                    <p className="text-sm text-gray-500">
                      {formatPercent(service.percentage_of_total)} of total
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-700">
                      {service.resource_count}
                    </p>
                    <p className="text-xs text-gray-500">resources</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
