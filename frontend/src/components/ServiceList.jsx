import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";

const EMPTY_FORM = { name: "", price: "", duration: "" };

function ServiceList({ tenantId }) {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingService, setEditingService] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    async function loadServices() {
      try {
        setLoading(true);
        setError("");
        const data = await apiRequest(`/api/tenants/${tenantId}/services/`);
        setServices(data.results || data);
      } catch (err) {
        setError(err.message || "Unable to load services.");
      } finally {
        setLoading(false);
      }
    }
    loadServices();
  }, [tenantId]);

  const startEditing = (service) => {
    setEditingService(service);
    setForm({
      name: service.name || "",
      price: String(service.price ?? ""),
      duration: String(service.duration ?? ""),
    });
    setError("");
  };

  const saveService = async (event) => {
    event.preventDefault();
    const price = Number(form.price);
    const duration = Number(form.duration);
    if (!form.name.trim() || !Number.isFinite(price) || price < 0 || !Number.isFinite(duration) || duration <= 0) {
      setError("Enter a service name, a valid price, and a duration greater than zero.");
      return;
    }
    try {
      setSaving(true);
      setError("");
      const updated = await apiRequest(`/api/services/${editingService.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ name: form.name.trim(), price, duration }),
      });
      setServices((current) => current.map((service) => service.id === updated.id ? updated : service));
      setEditingService(null);
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err.message || "Unable to update this service.");
    } finally {
      setSaving(false);
    }
  };

  const deleteService = async (service) => {
    if (!window.confirm(`Delete “${service.name}”? Services with existing bookings cannot be deleted.`)) return;
    try {
      setDeletingId(service.id);
      setError("");
      await apiRequest(`/api/services/${service.id}/`, { method: "DELETE" });
      setServices((current) => current.filter((item) => item.id !== service.id));
    } catch (err) {
      setError(err.message || "Unable to delete this service.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <section className="manage-service-list">
      <div className="manage-section-heading">
        <div><h2>Services</h2><p>Manage the services customers can book.</p></div>
        <span className="manage-service-count">{services.length} {services.length === 1 ? "service" : "services"}</span>
      </div>

      {error && <p className="manage-service-error" role="alert">{error}</p>}
      {loading ? <p className="manage-service-muted">Loading services…</p> : services.length === 0 ? (
        <div className="manage-service-empty"><h3>No services yet</h3><p>Add services from the Services page to start accepting bookings.</p></div>
      ) : <div className="manage-service-grid">
        {services.map((service) => <article className="manage-service-card" key={service.id}>
          <div className="manage-service-card-main">
            <div className="manage-service-symbol" aria-hidden="true">S</div>
            <div className="manage-service-details">
              <h3>{service.name}</h3>
              <p>{service.duration} min <span aria-hidden="true">·</span> ₹{service.price}</p>
            </div>
            <span className={`manage-service-status ${service.is_active ? "is-active" : "is-inactive"}`}>
              {service.is_active ? "Active" : "Inactive"}
            </span>
          </div>
          <div className="manage-service-actions">
            <button type="button" className="manage-service-edit" onClick={() => startEditing(service)}>Edit service</button>
            <button type="button" className="manage-service-delete" disabled={deletingId === service.id} onClick={() => deleteService(service)}>{deletingId === service.id ? "Deleting…" : "Delete"}</button>
          </div>
        </article>)}
      </div>}

      {editingService && <form className="manage-service-edit-form" onSubmit={saveService}>
        <h3>Edit {editingService.name}</h3>
        <div className="manage-service-edit-fields">
          <label>Service name<input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required /></label>
          <label>Price<input type="number" min="0" step="0.01" value={form.price} onChange={(event) => setForm((current) => ({ ...current, price: event.target.value }))} required /></label>
          <label>Duration (minutes)<input type="number" min="1" value={form.duration} onChange={(event) => setForm((current) => ({ ...current, duration: event.target.value }))} required /></label>
        </div>
        <div className="manage-service-edit-actions">
          <button type="button" className="manage-service-edit-cancel" onClick={() => { setEditingService(null); setForm(EMPTY_FORM); }}>Cancel</button>
          <button type="submit" className="manage-service-edit-save" disabled={saving}>{saving ? "Saving…" : "Save changes"}</button>
        </div>
      </form>}
    </section>
  );
}

export default ServiceList;
