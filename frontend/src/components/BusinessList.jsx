import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import { useNavigate } from "react-router-dom";

function BusinessList({ onCountChange }) {
  const [businesses, setBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 5;

  const navigate = useNavigate();

  useEffect(() => {
    async function loadBusinesses() {
      setLoading(true);
      setError("");
      try {
        const data = await apiRequest(`/api/tenants/?page=${page}`);

        const businessList = data.results || data;

        setBusinesses(businessList);
        const count = data.count ?? businessList.length;
        setTotalCount(count);
        onCountChange(count);

      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }

    loadBusinesses();
  }, [onCountChange, page]);

  if (loading) {
    return <p>Loading businesses...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <section className="business-section">

      <div className="section-header">
        <div>
          <h2>My Businesses</h2>

          <p>
            Manage your businesses and booking platforms. {totalCount} total.
          </p>
        </div>
      </div>

      {businesses.length === 0 ? (

        <div className="empty-business">

          <h3>No businesses yet</h3>

          <p>
            Create your first business to start
            accepting bookings.
          </p>

        </div>

      ) : (

        <div className="business-grid">

          {businesses.map((business) => (

            <div
              className="business-card"
              key={business.id}
            >

              <div className="business-card-header">

                <div>

                  <h3>
                    {business.business_name}
                  </h3>

                  <p>
                    {business.business_type}
                  </p>

                  {business.location && (
                    <p>
                      📍 {business.location}
                    </p>
                  )}

                </div>

                <span
                  className={
                    business.is_active
                      ? "status active"
                      : "status inactive"
                  }
                >
                  {business.is_active
                    ? "Active"
                    : "Inactive"}
                </span>

              </div>

              <div className="business-card-footer">

                <button
                  onClick={() =>
                    navigate(
                      `/dashboard/business/${business.id}`
                    )
                  }
                >
                  Manage Business
                </button>

              </div>

            </div>

          ))}

        </div>

      )}

      {totalCount > pageSize && (
        <nav className="business-pagination" aria-label="Business list pages">
          <span>
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalCount)} of {totalCount}
          </span>
          <div className="business-pagination-controls">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page === 1 || loading}
            >
              Previous
            </button>
            <span>Page {page} of {Math.ceil(totalCount / pageSize)}</span>
            <button
              type="button"
              onClick={() => setPage((current) => current + 1)}
              disabled={page >= Math.ceil(totalCount / pageSize) || loading}
            >
              Next
            </button>
          </div>
        </nav>
      )}

    </section>
  );
}

export default BusinessList;
