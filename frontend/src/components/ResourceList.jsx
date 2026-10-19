import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";

function ResourceList({ serviceId }) {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [resourceName, setResourceName] = useState("");

  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");

  useEffect(() => {
    loadResources();
  }, [serviceId]);

  async function loadResources() {
    try {
      const data = await apiRequest(
        `/api/services/${serviceId}/resources/`
      );

      setResources(data.results || data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function createResource() {
    if (!resourceName.trim()) {
      setError("Please enter a resource name.");
      return;
    }

    try {
      setError("");

      const newResource = await apiRequest(
        `/api/services/${serviceId}/resources/`,
        {
          method: "POST",
          body: JSON.stringify({
            name: resourceName,
          }),
        }
      );

      setResources((current) => [...current, newResource]);

      setResourceName("");
      setShowForm(false);
    } catch (error) {
      setError(error.message);
    }
  }

  async function updateResource(id) {
    if (!editName.trim()) {
      setError("Please enter a resource name.");
      return;
    }

    try {
      setError("");

      const updatedResource = await apiRequest(
        `/api/resources/${id}/`,
        {
          method: "PATCH",
          body: JSON.stringify({
            name: editName,
          }),
        }
      );

      setResources((current) =>
        current.map((resource) =>
          resource.id === id ? updatedResource : resource
        )
      );

      setEditingId(null);
      setEditName("");
    } catch (error) {
      setError(error.message);
    }
  }

  async function deleteResource(id) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this resource?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");

      await apiRequest(`/api/resources/${id}/`, {
        method: "DELETE",
      });

      setResources((current) =>
        current.filter((resource) => resource.id !== id)
      );
    } catch (error) {
      setError(error.message);
    }
  }

  if (loading) {
    return <p>Loading resources...</p>;
  }

  return (
    <div className="resource-section">
      <h4>Resources</h4>

      {error && <p>{error}</p>}

      {resources.length === 0 ? (
        <p>No resources added yet.</p>
      ) : (
        <div>
          {resources.map((resource) => (
            <div key={resource.id}>
              {editingId === resource.id ? (
                <>
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                  />

                  <button
                    onClick={() => updateResource(resource.id)}
                  >
                    Save
                  </button>

                  <button
                    onClick={() => {
                      setEditingId(null);
                      setEditName("");
                    }}
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <p>
                    {resource.name} —{" "}
                    {resource.is_active
                      ? "Active"
                      : "Inactive"}
                  </p>

                  <button
                    onClick={() => {
                      setEditingId(resource.id);
                      setEditName(resource.name);
                    }}
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => deleteResource(resource.id)}
                  >
                    Delete
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {!showForm && (
        <button onClick={() => setShowForm(true)}>
          + Add Resource
        </button>
      )}

      {showForm && (
        <div className="resource-form">
          <input
            type="text"
            placeholder="Resource name"
            value={resourceName}
            onChange={(e) => setResourceName(e.target.value)}
          />

          <button onClick={createResource}>
            Create Resource
          </button>

          <button
            onClick={() => {
              setShowForm(false);
              setResourceName("");
              setError("");
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

export default ResourceList;