const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem("refresh_token");

  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/auth/token/refresh/`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          refresh: refreshToken,
        }),
      }
    );

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    localStorage.setItem(
      "access_token",
      data.access
    );

    return data.access;
  } catch {
    return null;
  }
}

export async function apiRequest(
  endpoint,
  options = {}
) {
  let token = localStorage.getItem("access_token");

  const makeRequest = (accessToken) => {
    const isFormData = options.body instanceof FormData;
    return fetch(
      `${API_BASE_URL}${endpoint}`,
      {
        ...options,
        headers: {
          ...(isFormData ? {} : { "Content-Type": "application/json" }),

          ...(accessToken
            ? {
                Authorization:
                  `Bearer ${accessToken}`,
              }
            : {}),

          ...options.headers,
        },
      }
    );
  };

  let response = await makeRequest(token);

  // Access token expired
  if (response.status === 401) {
    token = await refreshAccessToken();

    // Refresh token expired/invalid
    if (!token) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");

      window.location.href = "/";

      throw new Error(
        "Your session has expired. Please log in again."
      );
    }

    // Retry original request
    response = await makeRequest(token);
  }

  if (!response.ok) {
    const errorData =
      await response.json().catch(() => ({}));

    throw new Error(
      errorData.detail ||
        errorData.error ||
        errorData.message ||
        `Request failed with status ${response.status}`
    );
  }

  // Some DELETE endpoints return 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}
