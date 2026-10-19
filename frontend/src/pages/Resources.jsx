import { useEffect, useState } from "react";
import OwnerNavigation from "../components/OwnerNavigation";
import { apiRequest } from "../services/api";
import "./Resources.css";

function Resources({ tenantId: initialTenantId = null, embedded = false }) {
  const [businesses, setBusinesses] = useState([]);
  const [tenantId, setTenantId] = useState(initialTenantId ? String(initialTenantId) : "");
  const [resources, setResources] = useState([]);
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadResources = async (id) => {
    if (!id) return setResources([]);
    const data = await apiRequest(`/api/tenants/${id}/resources/`);
    setResources(data.results || data);
  };

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await apiRequest("/api/tenants/");
        const tenantList = data.results || data;
        setBusinesses(tenantList);
        const selectedId = initialTenantId || tenantList[0]?.id;
        if (selectedId) {
          setTenantId(String(selectedId));
          await loadResources(selectedId);
        } else {
          setResources([]);
        }
      } catch (err) {
        setError(err.message || "Failed to load resources.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [initialTenantId]);

  const changeTenant = async (event) => {
    const id = event.target.value;
    setTenantId(id);
    setEditing(null);
    setName("");
    try {
      setError("");
      await loadResources(id);
    } catch (err) {
      setError(err.message || "Failed to load resources.");
    }
  };

  const saveResource = async (event) => {
    event.preventDefault();
    if (!name.trim() || !tenantId) return;
    try {
      setSaving(true);
      setError("");
      const saved = editing
        ? await apiRequest(`/api/resources/${editing.id}/`, { method: "PATCH", body: JSON.stringify({ name: name.trim() }) })
        : await apiRequest(`/api/tenants/${tenantId}/resources/`, { method: "POST", body: JSON.stringify({ name: name.trim() }) });
      setResources((current) => editing
        ? current.map((resource) => resource.id === editing.id ? saved : resource)
        : [...current, saved]);
      setName("");
      setEditing(null);
    } catch (err) {
      setError(err.message || "Failed to save resource.");
    } finally {
      setSaving(false);
    }
  };

  const toggleResource = async (resource) => {
    try {
      setError("");
      const saved = await apiRequest(`/api/resources/${resource.id}/`, {
        method: "PATCH", body: JSON.stringify({ is_active: !resource.is_active }),
      });
      setResources((current) => current.map((item) => item.id === resource.id ? saved : item));
    } catch (err) {
      setError(err.message || "Failed to update resource.");
    }
  };

  return (
    <div className={`resources-page ${embedded ? "resources-embedded" : ""}`}>
      {!embedded && <OwnerNavigation />}
      <main className="resources-content">
        {!embedded && <header className="resources-header">
          <p className="resources-eyebrow">BUSINESS SETUP</p>
          <h1>Resources</h1>
          <p>Manage the spaces and equipment customers can book.</p>
        </header>}

        {loading ? <p className="resources-loading">Loading resources…</p> : <>
          {error && <p className="resources-error" role="alert">{error}</p>}
          {!businesses.length ? <div className="empty-resources"><h2>No business yet</h2><p>Create a business before adding resources.</p></div> : <>
            {!embedded && <label className="business-selector">Business
              <select value={tenantId} onChange={changeTenant}>
                {businesses.map((business) => <option key={business.id} value={business.id}>{business.business_name}</option>)}
              </select>
            </label>}

            <section className="resources-panel">
              <div className="resources-panel-heading">
                <div><h2>{embedded ? "Shared resources" : "Your resources"}</h2><p>Resources are shared across all services in this business.</p></div>
                <span className="resources-count">{resources.length} {resources.length === 1 ? "resource" : "resources"}</span>
              </div>

              <form className="resource-form" onSubmit={saveResource}>
                <label htmlFor="resource-name">{editing ? "Resource name" : "Add a resource"}</label>
                <div className="resource-form-controls">
                  <input id="resource-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Pitch 1" required />
                  <button disabled={saving}>{saving ? "Saving…" : editing ? "Save changes" : "Add resource"}</button>
                  {editing && <button className="resource-cancel" type="button" onClick={() => { setEditing(null); setName(""); }}>Cancel</button>}
                </div>
              </form>

              {!resources.length ? <div className="empty-resources"><h3>No resources yet</h3><p>Add a pitch, room, table, or other bookable resource.</p></div> : <div className="resources-list">
                {resources.map((resource) => <article className="resource-card" key={resource.id}>
                  <div className="resource-card-title"><span className="resource-icon" aria-hidden="true">↗</span><div><h3>{resource.name}</h3><span className={resource.is_active ? "resource-active" : "resource-inactive"}>{resource.is_active ? "Active" : "Inactive"}</span></div></div>
                  <div className="resource-actions">
                    <button type="button" onClick={() => { setEditing(resource); setName(resource.name); }}>Edit</button>
                    <button type="button" onClick={() => toggleResource(resource)}>{resource.is_active ? "Deactivate" : "Activate"}</button>
                  </div>
                </article>)}
              </div>}
            </section>
          </>}
        </>}
      </main>
    </div>
  );
}

export default Resources;
