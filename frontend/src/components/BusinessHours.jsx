import { useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import "./BusinessHours.css";

const DAYS = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
];

function BusinessHours({ tenantId }) {
  const [hours, setHours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingDay, setSavingDay] = useState(null);
  const [successDay, setSuccessDay] = useState(null);

  // -----------------------------
  // Load hours
  // -----------------------------

  useEffect(() => {
    if (!tenantId) return;

    const loadHours = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await apiRequest(
          `/api/tenants/${tenantId}/hours/`
        );

        const existingHours = data.results || data;

        const formattedHours = DAYS.map((day) => {
          const existing = existingHours.find(
            (item) =>
              Number(item.day_of_week) === day.value
          );

          if (existing) {
            return {
              id: existing.id,
              day_of_week: Number(
                existing.day_of_week
              ),
              opening_time:
                existing.opening_time || "",
              closing_time:
                existing.closing_time || "",
              is_closed:
                existing.is_closed,
            };
          }

          return {
            id: null,
            day_of_week: day.value,
            opening_time: "",
            closing_time: "",
            is_closed: true,
          };
        });

        setHours(formattedHours);

      } catch (err) {
        setError(
          err.message ||
            "Failed to load business hours."
        );
      } finally {
        setLoading(false);
      }
    };

    loadHours();
  }, [tenantId]);

  // -----------------------------
  // Change field
  // -----------------------------

  const updateDay = (
    index,
    field,
    value
  ) => {
    setHours((current) =>
      current.map((day, i) =>
        i === index
          ? {
              ...day,
              [field]: value,
            }
          : day
      )
    );

    setSuccessDay(null);
    setError("");
  };

  // -----------------------------
  // Save
  // -----------------------------

  const saveDay = async (
    day,
    index
  ) => {
    try {
      setSavingDay(index);
      setError("");
      setSuccessDay(null);

      // Open day needs both times
      if (
        !day.is_closed &&
        (!day.opening_time ||
          !day.closing_time)
      ) {
        setError(
          `Please set both opening and closing time for ${DAYS[index].label}.`
        );
        return;
      }

      // Closing must be after opening
      if (
        !day.is_closed &&
        day.opening_time >=
          day.closing_time
      ) {
        setError(
          `Closing time must be after opening time for ${DAYS[index].label}.`
        );
        return;
      }

      const body = {
        day_of_week:
          Number(day.day_of_week),

        opening_time:
          day.opening_time || "00:00",

        closing_time:
          day.closing_time || "00:00",

        is_closed:
          day.is_closed,
      };

      let saved;

      // Existing record
      if (day.id) {
        saved = await apiRequest(
          `/api/hours/${day.id}/`,
          {
            method: "PATCH",
            body: JSON.stringify(body),
          }
        );
      }

      // New record
      else {
        saved = await apiRequest(
          `/api/tenants/${tenantId}/hours/`,
          {
            method: "POST",
            body: JSON.stringify(body),
          }
        );
      }

      // Store backend response
      setHours((current) =>
        current.map(
          (item, i) =>
            i === index
              ? {
                  ...item,
                  ...saved,
                  day_of_week:
                    Number(
                      saved.day_of_week ??
                        item.day_of_week
                    ),
                }
              : item
        )
      );

      setSuccessDay(index);

    } catch (err) {
      setError(
        err.message ||
          `Failed to save ${DAYS[index].label} hours.`
      );
    } finally {
      setSavingDay(null);
    }
  };

  // -----------------------------
  // Loading
  // -----------------------------

  if (loading) {
    return (
      <div className="business-hours">
        <p>Loading business hours...</p>
      </div>
    );
  }

  // -----------------------------
  // UI
  // -----------------------------

  return (
    <div className="business-hours">

      {error && (
        <div className="business-hours-error">
          {error}
        </div>
      )}

      {hours.map((day, index) => (
        <div
          className="business-day-card"
          key={day.id || day.day_of_week}
        >

          {/* Day header */}

          <div className="business-day-header">

            <h3>
              {DAYS[index].label}
            </h3>

            <label className="business-open-toggle">

              <input
                type="checkbox"
                checked={!day.is_closed}
                onChange={(e) =>
                  updateDay(
                    index,
                    "is_closed",
                    !e.target.checked
                  )
                }
              />

              Open

            </label>

          </div>

          {/* Time fields */}

          {day.is_closed ? (

            <p className="closed-text">
              Closed
            </p>

          ) : (

            <div className="business-time-fields">

              <label>
                Opening

                <input
                  type="time"
                  value={
                    day.opening_time
                  }
                  onChange={(e) =>
                    updateDay(
                      index,
                      "opening_time",
                      e.target.value
                    )
                  }
                />
              </label>

              <label>
                Closing

                <input
                  type="time"
                  value={
                    day.closing_time
                  }
                  onChange={(e) =>
                    updateDay(
                      index,
                      "closing_time",
                      e.target.value
                    )
                  }
                />
              </label>

            </div>
          )}

          {/* Save */}
<div className="hours-save-row">
  <button
    type="button"
    className="save-hours-button"
    onClick={() =>
      saveDay(day, index)
    }
    disabled={
      savingDay === index
    }
  >
    {savingDay === index
      ? "Saving..."
      : "Save"}
  </button>

  {successDay === index && (
    <span className="hours-saved">
      ✓ Saved
    </span>
  )}
</div>

        </div>
      ))}

    </div>
  );
}

export default BusinessHours;
