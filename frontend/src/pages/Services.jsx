import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import "./Services.css";

function Services() {
  const [businesses, setBusinesses] = useState([]);
  const [services, setServices] = useState([]);

  const [selectedBusiness, setSelectedBusiness] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);

  const [serviceName, setServiceName] = useState("");
  const [servicePrice, setServicePrice] = useState("");
  const [serviceDuration, setServiceDuration] = useState("");

  const [editingService, setEditingService] = useState(null);
  

  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  // --------------------------------
  // Load businesses
  // --------------------------------

  const loadBusinesses = async () => {
    const businessData = await apiRequest(
      "/api/tenants/"
    );

    const businessList =
      businessData.results || businessData;

    setBusinesses(businessList);

    if (businessList.length > 0) {
      setSelectedBusiness(
        String(businessList[0].id)
      );
    }

    return businessList;
  };

  // --------------------------------
  // Load services
  // --------------------------------

  const loadServices = async (tenantId) => {
    if (!tenantId) {
      setServices([]);
      return;
    }

    const serviceData = await apiRequest(
      `/api/tenants/${tenantId}/services/`
    );

    setServices(
      serviceData.results || serviceData
    );
  };

  // --------------------------------
  // Initial load
  // --------------------------------

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError("");

        const businessList =
          await loadBusinesses();

        if (businessList.length > 0) {
          await loadServices(
            businessList[0].id
          );
        }

      } catch (err) {
        setError(
          err.message ||
            "Failed to load services."
        );
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // --------------------------------
  // Change business
  // --------------------------------

  useEffect(() => {
    if (!selectedBusiness) return;

    async function loadSelectedServices() {
      try {
        setError("");

        await loadServices(
          selectedBusiness
        );

      } catch (err) {
        setError(
          err.message ||
            "Failed to load services."
        );
      }
    }

    loadSelectedServices();
  }, [selectedBusiness]);

  // --------------------------------
  // Reset form
  // --------------------------------

  const resetForm = () => {
    setServiceName("");
    setServicePrice("");
    setServiceDuration("");
    setEditingService(null);
    setShowForm(false);
  };

  // --------------------------------
  // Add / Edit service
  // --------------------------------

  const handleSaveService = async () => {
    if (!serviceName.trim()) {
      alert("Please enter a service name.");
      return;
    }

    if (
      servicePrice === "" ||
      Number(servicePrice) < 0
    ) {
      alert("Please enter a valid price.");
      return;
    }

    if (
      serviceDuration === "" ||
      Number(serviceDuration) <= 0
    ) {
      alert(
        "Please enter a valid duration."
      );
      return;
    }

    if (!selectedBusiness) {
      alert("Please select a business.");
      return;
    }

    try {
      setSaving(true);
      setError("");

      const body = {
        name: serviceName.trim(),
        price: Number(servicePrice),
        duration: Number(serviceDuration),
      };

      let savedService;

      // Edit
      if (editingService) {
        savedService = await apiRequest(
          `/api/services/${editingService.id}/`,
          {
            method: "PATCH",
            body: JSON.stringify(body),
          }
        );
      }

      // Create
      else {
        savedService = await apiRequest(
          `/api/tenants/${selectedBusiness}/services/`,
          {
            method: "POST",
            body: JSON.stringify(body),
          }
        );
      }

      // Update UI immediately
      if (editingService) {
        setServices((current) =>
          current.map((service) =>
            service.id ===
            editingService.id
              ? {
                  ...service,
                  ...(savedService || {}),
                  ...body,
                }
              : service
          )
        );
      } else {
        setServices((current) => [
          ...current,
          savedService || body,
        ]);
      }

      resetForm();

    } catch (err) {
      setError(
        err.message ||
          "Failed to save service."
      );
    } finally {
      setSaving(false);
    }
  };

  // --------------------------------
  // Edit service
  // --------------------------------

  const handleEdit = (service) => {
    setEditingService(service);

    setServiceName(
      service.name || ""
    );

    setServicePrice(
      service.price ?? ""
    );

    setServiceDuration(
      service.duration ?? ""
    );

    setShowForm(true);
  };

  // --------------------------------
  // Delete service
  // --------------------------------

  const handleDelete = async (service) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${service.name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(service.id);
      setError("");

      await apiRequest(
        `/api/services/${service.id}/`,
        {
          method: "DELETE",
        }
      );

      setServices((current) =>
        current.filter(
          (item) =>
            item.id !== service.id
        )
      );

    } catch (err) {
      setError(
        err.message ||
          "Failed to delete service."
      );
    } finally {
      setDeletingId(null);
    }
  };

  // --------------------------------
  // Loading
  // --------------------------------

  if (loading) {
    return (
      <div className="services-page">

        <h1>Services</h1>

        <p>
          Loading services...
        </p>

      </div>
    );
  }

  // --------------------------------
  // Page
  // --------------------------------

  return (
    <div className="services-page">

      {/* Header */}

      <header>
        <h1>Services</h1>

        <p>
          Manage the services offered by
          your business.
        </p>
      </header>

      {/* Error */}

      {error && (
        <p className="services-error">
          {error}
        </p>
      )}

      {/* No business */}

      {businesses.length === 0 ? (

        <div className="empty-services">

          <h2>
            No businesses yet
          </h2>

          <p>
            Create a business first before
            adding services.
          </p>

        </div>

      ) : (

        <>

          {/* Business selector */}

          <div className="services-toolbar">

            <div className="business-selector">

              <label>
                Business
              </label>

              <select
                value={selectedBusiness}
                onChange={(e) =>
                  setSelectedBusiness(
                    e.target.value
                  )
                }
              >

                {businesses.map(
                  (business) => (

                    <option
                      key={business.id}
                      value={business.id}
                    >
                      {business.business_name}
                    </option>

                  )
                )}

              </select>

            </div>

            <button
              type="button"
              onClick={() => {
                if (showForm) {
                  resetForm();
                } else {
                  setShowForm(true);
                }
              }}
            >
              {showForm
                ? "Close"
                : "+ Add Service"}
            </button>

          </div>

          {/* Form */}

          {showForm && (

            <div className="service-form">

              <h2>
                {editingService
                  ? "Edit Service"
                  : "Add Service"}
              </h2>

              <div className="form-field">

                <label>
                  Service Name
                </label>

                <input
                  type="text"
                  value={serviceName}
                  onChange={(e) =>
                    setServiceName(
                      e.target.value
                    )
                  }
                  placeholder="e.g. Haircut"
                />

              </div>

              <div className="form-field">

                <label>
                  Price
                </label>

                <input
                  type="number"
                  min="0"
                  value={servicePrice}
                  onChange={(e) =>
                    setServicePrice(
                      e.target.value
                    )
                  }
                  placeholder="e.g. 500"
                />

              </div>

              <div className="form-field">

                <label>
                  Duration (minutes)
                </label>

                <input
                  type="number"
                  min="1"
                  value={serviceDuration}
                  onChange={(e) =>
                    setServiceDuration(
                      e.target.value
                    )
                  }
                  placeholder="e.g. 60"
                />

              </div>

              <div className="service-form-actions">

                <button
                  type="button"
                  onClick={resetForm}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="button"
                  disabled={saving}
                  onClick={
                    handleSaveService
                  }
                >
                  {saving
                    ? "Saving..."
                    : editingService
                    ? "Update Service"
                    : "Save Service"}
                </button>

              </div>

            </div>

          )}

          {/* Services */}

          {services.length === 0 ? (

            <div className="empty-services">

              <h2>
                No services yet
              </h2>

              <p>
                Add your first service to
                start accepting bookings.
              </p>

            </div>

          ) : (

            <div className="services-list">

              {services.map(
                (service) => (

                  <article
                    className="service-card"
                    key={service.id}
                  >

                    <div className="service-info">

                      <h2>
                        {service.name}
                      </h2>

                      <p>
                        ₹{service.price} •{" "}
                        {service.duration} minutes
                      </p>

                      <span
                        className={
                          service.is_active
                            ? "service-active"
                            : "service-inactive"
                        }
                      >
                        {service.is_active
                          ? "Active"
                          : "Inactive"}
                      </span>

                    </div>

                    <div className="service-actions">

                      <button
                        type="button"
                        onClick={() =>
                          handleEdit(
                            service
                          )
                        }
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        disabled={
                          deletingId ===
                          service.id
                        }
                        onClick={() =>
                          handleDelete(
                            service
                          )
                        }
                      >
                        {deletingId ===
                        service.id
                          ? "Deleting..."
                          : "Delete"}
                      </button>

                    </div>

                  </article>

                )
              )}

            </div>

          )}

        </>

      )}

    </div>
  );
}

export default Services;