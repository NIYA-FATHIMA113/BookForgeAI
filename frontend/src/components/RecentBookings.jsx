import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiRequest } from "../services/api";

function RecentBookings() {

    
  const [bookings, setBookings] = useState([]);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecentBookings = async () => {
      try {
        const data = await apiRequest(
          "/api/recent-bookings/"
        );

        setBookings((data.results || data).slice(0, 5));
      } catch (error) {
        console.error(
          "Failed to load recent bookings:",
          error
        );
      } finally {
        setLoading(false);
      }
    };

    fetchRecentBookings();
  }, []);

  if (loading) {
    return (
      <section className="recent-bookings">
        <h2>Recent Bookings</h2>
        <p>Loading bookings...</p>
      </section>
    );
  }

  return (
    <section className="recent-bookings">
     <div className="recent-bookings-header">
        <h2>Recent Bookings</h2>

        {bookings.length > 0 && (
            <button
            type="button"
            onClick={() =>
                navigate("/dashboard/bookings")
            }
            >
            View All Bookings
            </button>
        )}
        </div>
      {bookings.length === 0 ? (
        <p>No recent bookings.</p>
      ) : (
        <div className="recent-bookings-list">
          {bookings.map((booking) => (
            <div
              className="recent-booking"
              key={booking.id}
            >
              <div>
                <strong>
                  {booking.customer_name}
                </strong>

                <p>
                  {booking.service?.name || "N/A"}
                </p>
              </div>

              <div>
                <p>
                  {booking.booking_date}
                </p>

                <p>
                  {booking.booking_time}
                </p>
              </div>

              <span
                className={`booking-status status-${booking.status.toLowerCase()}`}
              >
                {booking.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default RecentBookings;