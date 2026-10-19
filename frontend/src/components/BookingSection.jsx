import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";

function BookingSection({ tenantId }) {
  const [services, setServices] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [slug, setSlug] = useState("");

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    customer_name: "",
    customer_phone: "",
    service: "",
    booking_date: "",
    booking_time: "",
  });

  useEffect(() => {
    loadData();
  }, [tenantId]);

  async function loadData() {
    try {
      setLoading(true);
      setError("");

      const [tenant, serviceData, bookingData] =
        await Promise.all([
          apiRequest(`/api/tenants/${tenantId}/`),
          apiRequest(`/api/tenants/${tenantId}/services/`),
          apiRequest(`/api/bookings/`),
        ]);

      setSlug(tenant.slug);
      setServices(serviceData.results || serviceData);

      const allBookings =
        bookingData.results || bookingData;

      // Show only bookings belonging to this business
      setBookings(
        allBookings.filter(
          (booking) =>
            booking.service &&
            servicesBelongToTenant(
              booking.service,
              serviceData.results || serviceData
            )
        )
      );
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  function servicesBelongToTenant(serviceId, serviceList) {
    return serviceList.some(
      (service) => service.id === serviceId
    );
  }

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function createBooking(event) {
    event.preventDefault();

    try {
      setCreating(true);
      setError("");
      setSuccess("");

      const booking = await apiRequest(
        `/api/book/${slug}/`,
        {
          method: "POST",
          body: JSON.stringify({
            customer_name: form.customer_name,
            customer_phone: form.customer_phone,
            booking_date: form.booking_date,
            booking_time: form.booking_time,
            service: Number(form.service),
          }),
        }
      );

      setBookings((current) => [
        ...current,
        booking,
      ]);

      setForm({
        customer_name: "",
        customer_phone: "",
        service: "",
        booking_date: "",
        booking_time: "",
      });

      setSuccess("Booking created successfully.");
    } catch (error) {
      setError(error.message);
    } finally {
      setCreating(false);
    }
  }

  async function deleteBooking(id) {
    if (!window.confirm("Cancel this booking?")) {
      return;
    }

    try {
      setError("");

      await apiRequest(`/api/bookings/${id}/`, {
        method: "DELETE",
      });

      setBookings((current) =>
        current.filter(
          (booking) => booking.id !== id
        )
      );
    } catch (error) {
      setError(error.message);
    }
  }

  async function updateStatus(id, status) {
    try {
      setError("");

      const updated = await apiRequest(
        `/api/bookings/${id}/status/`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status,
          }),
        }
      );

      setBookings((current) =>
        current.map((booking) =>
          booking.id === id
            ? updated
            : booking
        )
      );
    } catch (error) {
      setError(error.message);
    }
  }

  if (loading) {
    return <p>Loading bookings...</p>;
  }

  return (
    <section>
      <h2>Bookings</h2>

      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}

      {success && (
        <p style={{ color: "green" }}>
          {success}
        </p>
      )}

      <h3>Create Booking</h3>

      <form onSubmit={createBooking}>
        <input
          name="customer_name"
          placeholder="Customer name"
          value={form.customer_name}
          onChange={handleChange}
          required
        />

        <input
          name="customer_phone"
          placeholder="Customer phone"
          value={form.customer_phone}
          onChange={handleChange}
          required
        />

        <select
          name="service"
          value={form.service}
          onChange={handleChange}
          required
        >
          <option value="">
            Select service
          </option>

          {services
            .filter((service) => service.is_active)
            .map((service) => (
              <option
                key={service.id}
                value={service.id}
              >
                {service.name} — ₹{service.price}
              </option>
            ))}
        </select>

        <input
          type="date"
          name="booking_date"
          value={form.booking_date}
          onChange={handleChange}
          required
        />

        <input
          type="time"
          name="booking_time"
          value={form.booking_time}
          onChange={handleChange}
          required
        />

        <button
          type="submit"
          disabled={creating}
        >
          {creating
            ? "Creating..."
            : "Create Booking"}
        </button>
      </form>

      <hr />

      <h3>Existing Bookings</h3>

      {bookings.length === 0 ? (
        <p>No bookings yet.</p>
      ) : (
        bookings.map((booking) => (
          <div key={booking.id}>
            <p>
              <strong>
                {booking.customer_name}
              </strong>
            </p>

            <p>
              Phone: {booking.customer_phone}
            </p>

            <p>
              Date: {booking.booking_date}
            </p>

            <p>
              Time: {booking.booking_time}
            </p>

            <p>
              Status: {booking.status}
            </p>

            {booking.resource && (
              <p>
                Resource:{" "}
                {booking.resource.name ||
                  booking.resource}
              </p>
            )}

            <button
              onClick={() =>
                updateStatus(
                  booking.id,
                  "confirmed"
                )
              }
            >
              Confirm
            </button>

            <button
              onClick={() =>
                updateStatus(
                  booking.id,
                  "completed"
                )
              }
            >
              Complete
            </button>

            <button
              onClick={() =>
                deleteBooking(booking.id)
              }
            >
              Cancel Booking
            </button>

            <hr />
          </div>
        ))
      )}
    </section>
  );
}

export default BookingSection;