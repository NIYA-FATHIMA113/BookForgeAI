import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import "./Bookings.css";

function Bookings() {
    const [filters, setFilters] = useState({
    date: "",
    customer: "",
    service: "",
    status: "",
    resource: "",
  });
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [updatingBooking, setUpdatingBooking] = useState(null);

  // --------------------------------
  // Fetch bookings
  // --------------------------------

 const fetchBookings = async () => {
  try {
    setLoading(true);
    setError("");

    const params = new URLSearchParams();

    if (filters.date) {
      params.append("date", filters.date);
    }

    if (filters.customer) {
      params.append("customer", filters.customer);
    }

    if (filters.service) {
      params.append("service", filters.service);
    }

    if (filters.status) {
      params.append("status", filters.status);
    }

    if (filters.resource) {
      params.append("resource", filters.resource);
    }

    const queryString = params.toString();

    const data = await apiRequest(
      `/api/bookings/${queryString ? `?${queryString}` : ""}`
    );

    setBookings(data.results || data);
  } catch (err) {
    setError(
      err.message || "Failed to load bookings."
    );
  } finally {
    setLoading(false);
  }
};

    useEffect(() => {
  fetchBookings();
}, [
  filters.date,
  filters.customer,
  filters.service,
  filters.status,
  filters.resource,
]);

  // --------------------------------
  // Update booking status
  // --------------------------------

  const updateBookingStatus = async (
    bookingId,
    newStatus
  ) => {
    try {
      setError("");
      setUpdatingBooking(bookingId);

      const updatedBooking = await apiRequest(
        `/api/bookings/${bookingId}/status/`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status: newStatus,
          }),
        }
      );

      // Update booking immediately
      setBookings((currentBookings) =>
        currentBookings.map((booking) =>
          booking.id === bookingId
            ? {
                ...booking,
                ...(updatedBooking || {}),
                status: newStatus,
              }
            : booking
        )
      );

      // Also update details panel if it is open
      setSelectedBooking((current) => {
        if (
          current &&
          current.id === bookingId
        ) {
          return {
            ...current,
            ...(updatedBooking || {}),
            status: newStatus,
          };
        }

        return current;
      });

    } catch (err) {
      setError(
        err.message ||
          "Failed to update booking status."
      );
    } finally {
      setUpdatingBooking(null);
    }
  };

  // --------------------------------
  // Delete booking
  // --------------------------------

  const deleteBooking = async (id) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this booking?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      await apiRequest(
        `/api/bookings/${id}/`,
        {
          method: "DELETE",
        }
      );

      // Remove immediately from UI
      setBookings((currentBookings) =>
        currentBookings.filter(
          (booking) => booking.id !== id
        )
      );

      // Close details if deleted booking is open
      setSelectedBooking((current) =>
        current?.id === id
          ? null
          : current
      );

    } catch (err) {
      setError(
        err.message ||
          "Failed to delete booking."
      );
    }
  };

  // --------------------------------
  // Loading
  // --------------------------------

  if (loading) {
    return (
      <div className="bookings-loading">
        <h1>Bookings</h1>
        <p>Loading bookings...</p>
      </div>
    );
  }

  // --------------------------------
  // Page
  // --------------------------------

  return (
    <div className="bookings-page">

      {/* Header */}

      <header className="bookings-header">

        <h1>Bookings</h1>

        <p>
          Manage bookings made by your customers.
        </p>
              <div className="booking-filters">

        <input
          type="date"
          value={filters.date}
          onChange={(e) =>
            setFilters({
              ...filters,
              date: e.target.value,
            })
          }
        />

        <input
          type="text"
          placeholder="Customer name"
          value={filters.customer}
          onChange={(e) =>
            setFilters({
              ...filters,
              customer: e.target.value,
            })
          }
        />

        <input
          type="text"
          placeholder="Service"
          value={filters.service}
          onChange={(e) =>
            setFilters({
              ...filters,
              service: e.target.value,
            })
          }
        />

        <select
          value={filters.status}
          onChange={(e) =>
            setFilters({
              ...filters,
              status: e.target.value,
            })
          }
        >
          <option value="">All statuses</option>
          <option value="PENDING">Pending</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>

        <input
          type="text"
          placeholder="Resource"
          value={filters.resource}
          onChange={(e) =>
            setFilters({
              ...filters,
              resource: e.target.value,
            })
          }
        />

        <button
          type="button"
          onClick={() =>
            setFilters({
              date: "",
              customer: "",
              service: "",
              status: "",
              resource: "",
            })
          }
        >
          Clear Filters
        </button>

      </div>

      </header>

      {/* Error */}

      {error && (
        <p className="bookings-error">
          {error}
        </p>
      )}

      {/* Empty */}

      {bookings.length === 0 ? (

        <div className="bookings-empty">

          <h2>No bookings yet</h2>

          <p>
            Customer bookings will appear here.
          </p>

        </div>

      ) : (

        <div className="bookings-list">

          {bookings.map((booking) => (

            <article
              className="booking-card"
              key={booking.id}
            >

              {/* Card Header */}

              <div className="booking-card-header">
                <div className="booking-card-title">
                  <h2>{booking.customer_name}</h2>
                  <span className="booking-business-name">
                    {booking.tenant?.business_name || "Business unavailable"}
                  </span>
                </div>

                {/* Status */}

                <select
                  className={`booking-status status-${(
                    booking.status || "PENDING"
                  ).toLowerCase()}`}
                  value={
                    booking.status || "PENDING"
                  }
                  disabled={
                    updatingBooking ===
                    booking.id
                  }
                  onChange={(e) =>
                    updateBookingStatus(
                      booking.id,
                      e.target.value
                    )
                  }
                >

                  <option value="PENDING">
                    Pending
                  </option>

                  <option value="CONFIRMED">
                    Confirmed
                  </option>

                  <option value="COMPLETED">
                    Completed
                  </option>

                  <option value="CANCELLED">
                    Cancelled
                  </option>

                </select>

              </div>

              {/* Booking Details */}

              <div className="booking-details">

                <div className="booking-detail">

                  <span className="booking-detail-label">
                    Phone
                  </span>

                  <span className="booking-detail-value">
                    {booking.customer_phone}
                  </span>

                </div>

                <div className="booking-detail">

                  <span className="booking-detail-label">
                    Service
                  </span>

                  <span className="booking-detail-value">
                    {booking.service?.name ||
                      "N/A"}
                  </span>

                </div>

                <div className="booking-detail">

                  <span className="booking-detail-label">
                    Date
                  </span>

                  <span className="booking-detail-value">
                    {booking.booking_date}
                  </span>

                </div>

                <div className="booking-detail">

                  <span className="booking-detail-label">
                    Time
                  </span>

                  <span className="booking-detail-value">
                    {booking.booking_time}
                  </span>

                </div>

                <div className="booking-detail">

                  <span className="booking-detail-label">
                    Resource
                  </span>

                  <span className="booking-detail-value">
                    {booking.resource?.name ||
                      "N/A"}
                  </span>

                </div>

              </div>

              {/* Actions */}

              <div className="booking-actions">

                {/* Confirm */}

                {booking.status ===
                  "PENDING" && (

                  <button
                    className="confirm-button"
                    type="button"
                    disabled={
                      updatingBooking ===
                      booking.id
                    }
                    onClick={() =>
                      updateBookingStatus(
                        booking.id,
                        "CONFIRMED"
                      )
                    }
                  >
                    {updatingBooking ===
                    booking.id
                      ? "Updating..."
                      : "Confirm"}
                  </button>

                )}

                {/* Complete */}

                {booking.status ===
                  "CONFIRMED" && (

                  <button
                    className="confirm-button"
                    type="button"
                    disabled={
                      updatingBooking ===
                      booking.id
                    }
                    onClick={() =>
                      updateBookingStatus(
                        booking.id,
                        "COMPLETED"
                      )
                    }
                  >
                    {updatingBooking ===
                    booking.id
                      ? "Updating..."
                      : "Complete"}
                  </button>

                )}

                {/* Cancel */}

                {(booking.status ===
                  "PENDING" ||
                  booking.status ===
                    "CONFIRMED") && (

                  <button
                    className="cancel-button"
                    type="button"
                    disabled={
                      updatingBooking ===
                      booking.id
                    }
                    onClick={() =>
                      updateBookingStatus(
                        booking.id,
                        "CANCELLED"
                      )
                    }
                  >
                    Cancel
                  </button>

                )}

                {/* View Details */}

                <button
                  type="button"
                  onClick={() =>
                    setSelectedBooking(
                      booking
                    )
                  }
                >
                  View Details
                </button>

                {/* Delete */}

                <button
                  className="delete-button"
                  type="button"
                  onClick={() =>
                    deleteBooking(
                      booking.id
                    )
                  }
                >
                  Delete
                </button>

              </div>

            </article>

          ))}

        </div>

      )}

      {/* Details Panel */}

      {selectedBooking && (

        <div className="booking-details-panel">

          <h2>
            Booking Details
          </h2>

          <p>
            <strong>Customer:</strong>{" "}
            {selectedBooking.customer_name}
          </p>

          <p>
            <strong>Business:</strong>{" "}
            {selectedBooking.tenant?.business_name || "Business unavailable"}
          </p>

          <p>
            <strong>Phone:</strong>{" "}
            {selectedBooking.customer_phone}
          </p>

          <p>
            <strong>Service:</strong>{" "}
            {selectedBooking.service?.name ||
              "N/A"}
          </p>

          <p>
            <strong>Price:</strong>{" "}
            ₹
            {selectedBooking.service?.price ||
              0}
          </p>

          <p>
            <strong>Duration:</strong>{" "}
            {selectedBooking.service?.duration ||
              0}{" "}
            minutes
          </p>

          <p>
            <strong>Date:</strong>{" "}
            {selectedBooking.booking_date}
          </p>

          <p>
            <strong>Time:</strong>{" "}
            {selectedBooking.booking_time}
          </p>

          <p>
            <strong>Resource:</strong>{" "}
            {selectedBooking.resource?.name ||
              "N/A"}
          </p>

          <p>
            <strong>Status:</strong>{" "}
            {selectedBooking.status}
          </p>

          <button
            type="button"
            onClick={() =>
              setSelectedBooking(null)
            }
          >
            Close
          </button>

        </div>

      )}

    </div>
  );
}

export default Bookings;
