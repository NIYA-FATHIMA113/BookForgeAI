import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import BusinessHours from "../components/BusinessHours";
import OwnerNavigation from "../components/OwnerNavigation";
import "./BusinessHoursPage.css";

function BusinessHoursPage() {
  const [tenantId, setTenantId] = useState(null);
  const [businessName, setBusinessName] = useState("");
  const [businesses, setBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadBusiness() {
      try {
        setLoading(true);
        setError("");

        const data = await apiRequest("/api/tenants/");

        const businesses = data.results || data;

        if (!businesses || businesses.length === 0) {
          setError(
            "No business found. Please create a business first."
          );
          return;
        }

        setBusinesses(businesses);
        setTenantId(businesses[0].id);
        setBusinessName(businesses[0].business_name);
      } catch (err) {
        setError(
          err.message || "Failed to load business."
        );
      } finally {
        setLoading(false);
      }
    }

    loadBusiness();
  }, []);

  return (
    <div className="business-hours-page">
      <OwnerNavigation />
      <main className="business-hours-content">
        <header className="business-hours-heading">
          <p className="business-hours-eyebrow">BUSINESS SETUP</p>
          <h1>Business Hours</h1>
          <p>Set the times customers can book your business.</p>
        </header>
        {loading ? <p className="business-hours-message">Loading business…</p> : error ? <p className="business-hours-page-error" role="alert">{error}</p> : !tenantId ? <p className="business-hours-message">Business ID not found.</p> : <>
          {businesses.length > 1 ? <label className="hours-business-selector">Business
            <select value={tenantId} onChange={(event) => {
              const selected = businesses.find((business) => String(business.id) === event.target.value);
              setTenantId(Number(event.target.value));
              setBusinessName(selected?.business_name || "");
            }}>
              {businesses.map((business) => <option key={business.id} value={business.id}>{business.business_name}</option>)}
            </select>
          </label> : <div className="business-hours-context"><span>Editing hours for</span><strong>{businessName}</strong></div>}
          <section className="business-hours-panel">
            <div className="business-hours-panel-heading"><div><h2>Weekly schedule</h2><p>Open the days you accept bookings and set their hours.</p></div><span>7 days</span></div>
            <BusinessHours tenantId={tenantId} />
          </section>
        </>}
      </main>
    </div>
  );
}

export default BusinessHoursPage;
