import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import ServiceList from "../components/ServiceList";
import Resources from "./Resources";
import BusinessHours from "../components/BusinessHours";
import BookingSection from "../components/BookingSection";
import ImageWithFallback from "../components/ImageWithFallback";
import OwnerNavigation from "../components/OwnerNavigation";
import { apiRequest } from "../services/api";
import { templatesForBusiness } from "../constants/websiteTemplates";
import { createObjectUrlPreview } from "../utils/objectUrlPreview";
import "./BusinessManagement.css";

function ImagePicker({ title, help, currentImage, currentAlt, selectedFile, onSelect }) {
  const [localPreviewUrl, setLocalPreviewUrl] = useState(null);
  const [localPreviewFailed, setLocalPreviewFailed] = useState(false);
  const [resolutionMessage, setResolutionMessage] = useState("");

  useEffect(() => {
    if (!selectedFile) {
      setLocalPreviewUrl(null);
      setResolutionMessage("");
      return undefined;
    }

    let preview;
    try {
      preview = createObjectUrlPreview(selectedFile);
    } catch {
      setLocalPreviewUrl(null);
      setResolutionMessage("This image could not be previewed. Try a JPG, PNG, or WebP file.");
      return undefined;
    }

    setLocalPreviewUrl(preview.url);
    setLocalPreviewFailed(false);
    setResolutionMessage("");
    const image = new Image();
    image.onload = () => {
      const minimum = title === "Logo" ? [512, 512] : [1200, 675];
      if (image.naturalWidth < minimum[0] || image.naturalHeight < minimum[1]) {
        setResolutionMessage(`This image is ${image.naturalWidth} x ${image.naturalHeight} px. A larger image will look sharper (at least ${minimum[0]} x ${minimum[1]} px recommended).`);
      } else {
        setResolutionMessage(`Image resolution: ${image.naturalWidth} x ${image.naturalHeight} px.`);
      }
    };
    image.onerror = () => setResolutionMessage("We couldn't read this image. Try a JPG, PNG, or WebP file.");
    image.src = preview.url;

    return () => preview.revoke();
  }, [selectedFile, title]);

  const imageClass = `manage-image-preview ${title === "Logo" ? "logo-preview" : ""}`;
  const imageFallback = <div className={`manage-image-fallback ${title === "Logo" ? "logo-preview" : ""}`}>Image unavailable</div>;
  return <div className="image-picker-field">
    <span className="image-picker-title">{title}</span>
    <label className="custom-image-picker">
      <span className="custom-image-picker-button">Choose image</span>
      <span className="custom-image-picker-name">{selectedFile?.name || "No new image selected"}</span>
      <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => onSelect(event.target.files?.[0] || null)} />
    </label>
    <small className="image-recommendation">{help}</small>
    {resolutionMessage && <small className={`image-resolution-message ${resolutionMessage.startsWith("This image") ? "is-low-resolution" : ""}`} aria-live="polite">{resolutionMessage}</small>}
    {localPreviewUrl
      ? (localPreviewFailed
        ? imageFallback
        : <img className={imageClass} src={localPreviewUrl} alt={currentAlt} onError={() => setLocalPreviewFailed(true)} />)
      : currentImage && <ImageWithFallback className={imageClass} src={currentImage} alt={currentAlt} fallback={imageFallback} />}
  </div>;
}

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
    website_style: "auto",
    website_template: "auto",
    website_font: "classic",
    business_name_font: "editorial",
    business_name_size: "24",
    instagram_handle: "",
    whatsapp_number: "",
    facebook_id: "",
    logo_image_external_url: "",
    hero_image_external_url: "",
  });
  const [logoFile, setLogoFile] = useState(null);
  const [heroFile, setHeroFile] = useState(null);

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
          website_style: data.website_style || "auto",
          website_template: data.website_template || "auto",
          website_font: data.website_font || "classic",
          business_name_font: data.business_name_font || "editorial",
          business_name_size: String(data.business_name_size || 24),
          instagram_handle: data.instagram_handle || "",
          whatsapp_number: data.whatsapp_number || "",
          facebook_id: data.facebook_id || "",
          logo_image_external_url: data.logo_image_external_url || "",
          hero_image_external_url: data.hero_image_external_url || "",
        });
      })
      .catch((err) => setError(err.message || "Unable to load this business."));
  }, [tenantId]);

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({
      ...current,
      [name]: value,
      ...(name === "business_type" ? { website_template: "auto" } : {}),
    }));
  };

  const saveBusiness = async (event) => {
    event.preventDefault();
    try {
      setSaving(true);
      setError("");
      const body = new FormData();
      Object.entries(form).forEach(([key, value]) => body.append(key, value));
      if (logoFile) body.append("logo_image", logoFile);
      if (heroFile) body.append("hero_image", heroFile);
      if (logoFile) body.set("logo_image_external_url", "");
      if (heroFile) body.set("hero_image_external_url", "");
      const updated = await apiRequest(`/api/tenants/${tenantId}/`, {
        method: "PATCH",
        body,
      });
      setBusiness(updated);
      setLogoFile(null);
      setHeroFile(null);
      setEditing(false);
    } catch (err) {
      const hasImageUpload = Boolean(logoFile || heroFile);
      setError(hasImageUpload
        ? `Business save failed while uploading the image. Check the connection and backend media storage, then try again. ${err.message || ""}`.trim()
        : err.message || "Unable to update this business.");
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
            <label>Website look<select name="website_style" value={form.website_style} onChange={updateField}><option value="auto">Match business type</option><option value="modern">Modern & minimal</option><option value="warm">Warm & welcoming</option><option value="bold">Bold & energetic</option><option value="elegant">Elegant & premium</option><option value="nature">Natural & relaxed</option><option value="3d">3D motion</option><option value="illustrated">Illustrated</option><option value="playful">Cartoon pop</option></select></label>
            <label>Website template<select name="website_template" value={form.website_template} onChange={updateField}><option value="auto">Default for my business type</option>{templatesForBusiness(form.business_type).map(([value, title]) => <option key={value} value={value}>{title}</option>)}</select><small>Choose from layouts made for this business type.</small></label>
            <label>Website font<select name="website_font" value={form.website_font} onChange={updateField}><option value="classic">Classic serif</option><option value="modern">Modern sans serif</option><option value="friendly">Friendly rounded</option><option value="editorial">Editorial display</option><option value="mono">Minimal mono</option></select><small>The preview on your public site updates after saving.</small></label>
            <label>Business name font<select name="business_name_font" value={form.business_name_font} onChange={updateField}><option value="classic">Classic serif</option><option value="modern">Modern sans serif</option><option value="friendly">Friendly rounded</option><option value="editorial">Editorial display</option><option value="mono">Minimal mono</option></select><small>Choose how your business name appears in the site header and footer.</small></label>
            <label className="business-name-size-control">Business name size: {form.business_name_size}px<input name="business_name_size" type="range" min="16" max="48" step="1" value={form.business_name_size} onChange={updateField} /><small>Adjust the name size in the public website header and footer.</small></label>
            <div className={`business-name-font-preview name-font-${form.business_name_font}`}><small>BUSINESS NAME PREVIEW</small><strong style={{ fontSize: `${form.business_name_size}px` }}>{form.business_name || business?.business_name || "Your business"}</strong></div>
            <label>Instagram username<input name="instagram_handle" value={form.instagram_handle} onChange={updateField} placeholder="@yourbusiness" /></label>
            <label>WhatsApp number<input name="whatsapp_number" type="tel" value={form.whatsapp_number} onChange={updateField} placeholder="+91 98765 43210" /></label>
            <label>Facebook page ID or link<input name="facebook_id" value={form.facebook_id} onChange={updateField} placeholder="Your page name, ID, or URL" /></label>
            <ImagePicker title="Logo" help="Square image recommended: 512 × 512 px. PNG or WebP works well." currentImage={business?.logo_image_external_url || business?.logo_image} selectedFile={logoFile} currentAlt="Current business logo" onSelect={setLogoFile} />
            <label>Or use an existing logo URL<input type="url" name="logo_image_external_url" value={form.logo_image_external_url} onChange={updateField} placeholder="https://…" /></label>
            <ImagePicker title="Website photo" help="Landscape image recommended: 1600 × 900 px (16:9). Use a sharp original photo for best results." currentImage={business?.hero_image_external_url || business?.hero_image} selectedFile={heroFile} currentAlt="Current website hero photo" onSelect={setHeroFile} />
            <label>Or use an existing website photo URL<input type="url" name="hero_image_external_url" value={form.hero_image_external_url} onChange={updateField} placeholder="https://…" /></label>
            <div className="manage-business-form-actions"><button className="manage-cancel-button" type="button" onClick={() => setEditing(false)}>Cancel</button><button className="manage-save-button" type="submit" disabled={saving}>{saving ? "Saving…" : "Save changes"}</button></div>
          </form>
          {business?.business_type === "restaurant" && <section className="restaurant-spaces-editor" aria-labelledby="restaurant-spaces-title">
            <div className="manage-section-heading"><div><h3 id="restaurant-spaces-title">Dining and celebration spaces</h3><p>These active spaces determine which experiences customers can select on your website.</p></div></div>
            <Resources tenantId={tenantId} embedded />
          </section>}
        </section>}

        <section className="manage-panel manage-services"><ServiceList tenantId={tenantId} /></section>
        <section className="manage-panel"><div className="manage-section-heading"><div><h2>Business hours</h2><p>Set the weekly schedule customers can book.</p></div></div><BusinessHours tenantId={tenantId} /></section>
        {business?.business_type !== "restaurant" && <section className="manage-panel"><Resources tenantId={tenantId} embedded /></section>}
        <section className="manage-panel manage-bookings"><BookingSection tenantId={tenantId} /></section>
      </main>
    </div>
  );
}

export default BusinessManagement;
