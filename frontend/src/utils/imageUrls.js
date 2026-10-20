const IMAGE_PLACEHOLDERS = new Set(["null", "undefined", "none", "n/a"]);

export function resolveImageUrl(value, { apiBaseUrl = "", pageProtocol = "" } = {}) {
  if (typeof value !== "string") return null;

  const rawUrl = value.trim();
  if (!rawUrl || IMAGE_PLACEHOLDERS.has(rawUrl.toLowerCase())) return null;
  if (/\s/.test(rawUrl)) return null;

  let resolved;
  try {
    if (/^https?:\/\//i.test(rawUrl)) {
      resolved = new URL(rawUrl);
      if (["localhost", "127.0.0.1", "0.0.0.0", "[::1]"].includes(resolved.hostname.toLowerCase())) {
        const apiOrigin = new URL(apiBaseUrl).origin;
        resolved = new URL(`${resolved.pathname}${resolved.search}${resolved.hash}`, apiOrigin);
      }
    } else if (rawUrl.startsWith("//")) {
      const scheme = pageProtocol === "http:" ? "http:" : "https:";
      resolved = new URL(rawUrl, `${scheme}//assets.invalid`);
    } else {
      // Do not reinterpret file:, javascript:, or other non-web schemes as paths.
      if (/^[a-z][a-z\d+.-]*:/i.test(rawUrl)) return null;
      const apiOrigin = new URL(apiBaseUrl).origin;
      const path = rawUrl.replace(/^\/+/, "");
      resolved = new URL(`/${path}`, apiOrigin);
    }
  } catch {
    return null;
  }

  if (!["http:", "https:"].includes(resolved.protocol) || resolved.username || resolved.password) {
    return null;
  }

  // Avoid mixed-content blocking when an old API response contains an HTTP URL.
  if (pageProtocol === "https:" && resolved.protocol === "http:") {
    resolved.protocol = "https:";
  }

  return resolved.href;
}

export function getImageRenderState(resolvedUrl, failed = false) {
  const showFallback = !resolvedUrl || failed;
  return {
    showFallback,
    showImage: Boolean(resolvedUrl) && !failed,
  };
}
