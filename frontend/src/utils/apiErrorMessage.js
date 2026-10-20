const FIELD_LABELS = {
  hero_image: "Website photo",
  logo_image: "Business logo",
  hero_image_external_url: "Website photo URL",
  logo_image_external_url: "Business logo URL",
  non_field_errors: "Request",
};

export function getApiErrorMessage(errorData, status) {
  const directMessage = errorData?.detail || errorData?.error || errorData?.message;
  if (typeof directMessage === "string" && directMessage.trim()) return directMessage;

  if (errorData && typeof errorData === "object" && !Array.isArray(errorData)) {
    for (const [field, value] of Object.entries(errorData)) {
      const messages = Array.isArray(value) ? value : [value];
      const message = messages.find((item) => typeof item === "string" && item.trim());
      if (message) {
        const label = FIELD_LABELS[field] || field.replaceAll("_", " ");
        return `${label}: ${message}`;
      }
    }
  }

  return `Request failed with status ${status}`;
}
