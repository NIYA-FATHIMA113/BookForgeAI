import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import ServiceList from "../components/ServiceList";
import Resources from "./Resources";
import BusinessHours from "../components/BusinessHours";
import BookingSection from "../components/BookingSection";
import OwnerNavigation from "../components/OwnerNavigation";
import { apiRequest } from "../services/api";
import "./BusinessManagement.css";

function BusinessManagement() {
  const { tenantId } = useParams();
  const navigate = useNavigate();
  const [business, setBusiness] = useState(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [form, setForm] = useState({
    business_name: "",
    business_type: "salon",
    location: "",
    contact_phone: "",
    contact_email: "",
  });

  useEffect(() => {
    apiRequest(`/api/tenants/${tenantId}/`)
      .then((data) => {
        setBusiness(data);
        setForm({
          business_name: data.business_name || "",
          business_type: data.business_type || "salon",
          location: data.location || "",
          contact_phone: data.contact_phone || "",
          contact_email: data.contact_email || "",
        });
      })
      .catch((err) => setError(err.message || "Unable to load this business."));
  }, [tenantId]);

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const saveBusiness = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      setError("");
      const updated = await apiRequest(`/api/tenants/${tenantId}/`, {
        method: "PATCH",
        body: JSON.stringify(form),
      });
      setBusiness(updated);
      setEditing(false);
    } catch (err) {
      setError(err.message || "Unable to update this business.");
    } finally {
      setSaving(false);
    }
  };

  const deleteBusiness = async () => {
    const confirmed = window.confirm(
      `Delete ${business.business_name}? This also permanently deletes its services, resources, hours, and bookings.`
    );
    if (!confirmed) return;

    try {
      setDeleting(true);
      setError("");
      await apiRequest(`/api/tenants/${tenantId}/`, { method: "DELETE" });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Unable to delete this business.");
      setDeleting(false);
    }
  };

  const publicUrl = business?.slug
    ? `${window.location.origin}/book/${business.slug}`
    : "";

  return (
    <div className="business-management-page">
      <OwnerNavigation />
      <main className="business-management">
        <header className="business-management-header">
          <p className="manage-eyebrow">BUSINESS WORKSPACE</p>
          <div className="manage-hero-row">
            <div className="manage-business-identity">
              <h1>{business?.business_name || "Manage Business"}</h1>
              {business && <a className="manage-public-link" href={publicUrl} target="_blank" rel="noreferrer">
                <span className="manage-link-mark" aria-hidden="true">↗</span>
                <span><small>PUBLIC BOOKING WEBSITE</small><strong>{publicUrl}</strong></span>
              </a>}
              <p>Manage services, shared resources, hours, and bookings for this business.</p>
            </div>
            {business && <div className="manage-business-actions">
              <button className="manage-edit-button" type="button" onClick={() => setEditing((value) => !value)}>{editing ? "Close editor" : "Edit business"}</button>
              <button className="manage-delete-button" type="button" onClick={deleteBusiness} disabled={deleting}>{deleting ? "Deleting…" : "Delete business"}</button>
            </div>}
          </div>
          {error && <p className="manage-error" role="alert">{error}</p>}
        </header>

        {editing && <section className="manage-panel manage-edit-panel">
          <div className="manage-section-heading"><div><h2>Edit business details</h2><p>Update the information shown to your customers.</p></div></div>
          <form className="manage-business-form" onSubmit={saveBusiness}>
            <label>Business name<input name="business_name" value={form.business_name} onChange={updateField} required /></label>
            <label>Business type<select name="business_type" value={form.business_type} onChange={updateField}>
              <option value="restaurant">Restaurant</option><option value="salon">Salon</option><option value="clinic">Clinic</option><option value="sports_turf">Sports turf</option>
            </select></label>
            <label>Location<input name="location" value={form.location} onChange={updateField} /></label>
            <label>Contact phone<input name="contact_phone" value={form.contact_phone} onChange={updateField} /></label>
            <label>Contact email<input name="contact_email" type="email" value={form.contact_email} onChange={updateField} /></label>
            <div className="manage-business-form-actions"><button className="manage-cancel-button" type="button" onClick={() => setEditing(false)}>Cancel</button><button className="manage-save-button" type="submit" disabled={saving}>{saving ? "Saving…" : "Save changes"}</button></div>
          </form>
        </section>}

        <section className="manage-panel manage-services"><ServiceList tenantId={tenantId} /></section>
        <section className="manage-panel"><div className="manage-section-heading"><div><h2>Business hours</h2><p>Set the weekly schedule customers can book.</p></div></div><BusinessHours tenantId={tenantId} /></section>
        <section className="manage-panel"><Resources tenantId={tenantId} embedded /></section>
        <section className="manage-panel manage-bookings"><BookingSection tenantId={tenantId} /></section>
      </main>
    </div>
  );
}

export default BusinessManagement;
