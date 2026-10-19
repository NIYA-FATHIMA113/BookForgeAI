import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import OwnerNavigation from "../components/OwnerNavigation";
import BusinessList from "../components/BusinessList";
import { apiRequest } from "../services/api";
import "./Dashboard.css";

function Dashboard() {
  const navigate = useNavigate();

  const [businessCount, setBusinessCount] = useState(0);
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  useEffect(() => {
    async function loadSummary() {
      try {
        const data = await apiRequest("/api/dashboard/summary/");
        setSummary(data);
      } catch (error) {
        console.error("Failed to load dashboard summary:", error);
      } finally {
        setLoadingSummary(false);
      }
    }

    loadSummary();
  }, []);

  const stats = [
    {
      label: "Businesses",
      value: businessCount,
    },
    {
      label: "Total bookings",
      value: summary?.total_bookings ?? 0,
    },
    {
      label: "Today's bookings",
      value: summary?.today_bookings ?? 0,
    },
    {
      label: "Pending",
      value: summary?.pending_bookings ?? 0,
    },
    {
      label: "Confirmed",
      value: summary?.confirmed_bookings ?? 0,
    },
    {
      label: "Completed",
      value: summary?.completed_bookings ?? 0,
    },
    {
      label: "Cancelled",
      value: summary?.cancelled_bookings ?? 0,
    },
    {
      label: "Total revenue",
      value: `₹${summary?.total_revenue ?? 0}`,
      revenue: true,
    },
  ];

  return (
    <div className="dashboard-page">
      <OwnerNavigation />

      <main className="dashboard-content">

        {/* Header */}
        <header className="dashboard-header">
          <p className="eyebrow">Owner Dashboard</p>

          <h1>Dashboard</h1>

          <p className="dashboard-subtitle">
            Manage your businesses and bookings from one place.
          </p>

          <button
            type="button"
            className="primary-button"
            onClick={() => navigate("/ai-setup")}
          >
            + Create Business with AI
          </button>
        </header>

        {/* Businesses */}
        <BusinessList
          onCountChange={setBusinessCount}
        />

        {/* Statistics */}
        <section className="dashboard-stats-section">
          <div className="section-header">
            <div>
              <h2>Booking Overview</h2>
              <p>
                A quick overview of your booking activity.
              </p>
            </div>
          </div>

          <div className="dashboard-stats">
            {stats.map((stat) => (
              <article
                className={`stat-card ${
                  stat.revenue ? "revenue-card" : ""
                }`}
                key={stat.label}
              >
                <h3>{stat.label}</h3>

                <strong>
                  {loadingSummary ? "..." : stat.value}
                </strong>
              </article>
            ))}
          </div>
        </section>

        {/* Quick actions */}
        <section className="quick-actions">
          <div className="section-header">
            <div>
              <h2>Quick Actions</h2>
              <p>Manage your booking platform quickly.</p>
            </div>
          </div>

          <div className="quick-actions-grid">

            <button
              type="button"
              onClick={() => navigate("/dashboard/services")}
            >
              <strong>+ Add Service</strong>
              <span>Create a new service</span>
            </button>

            <button
              type="button"
              onClick={() => navigate("/dashboard/resources")}
            >
              <strong>+ Add Resource</strong>
              <span>Add a bookable resource</span>
            </button>

            <button
              type="button"
              onClick={() => navigate("/dashboard/bookings")}
            >
              <strong>View Bookings</strong>
              <span>Manage customer bookings</span>
            </button>

            <button
              type="button"
              onClick={() => navigate("/dashboard/hours")}
            >
              <strong>Business Hours</strong>
              <span>Manage your availability</span>
            </button>

          </div>
        </section>

      </main>
    </div>
  );
}

export default Dashboard;
