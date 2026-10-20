import { useEffect, useState } from "react";
import { API_BASE_URL } from "../services/api";
import { getImageRenderState, resolveImageUrl } from "../utils/imageUrls";

function ImageWithFallback({
  src,
  alt = "",
  className,
  fallback = null,
  apiBaseUrl = API_BASE_URL,
  onImageError,
  ...imageProps
}) {
  const pageProtocol = typeof window === "undefined" ? "" : window.location.protocol;
  const resolvedUrl = resolveImageUrl(src, { apiBaseUrl, pageProtocol });
  const [failedUrl, setFailedUrl] = useState(null);
  const failed = failedUrl === resolvedUrl;
  const { showFallback } = getImageRenderState(resolvedUrl, failed);

  useEffect(() => {
    setFailedUrl(null);
  }, [resolvedUrl]);

  if (showFallback) return fallback;

  return (
    <img
      {...imageProps}
      className={className}
      src={resolvedUrl}
      alt={alt}
      onError={(event) => {
        setFailedUrl(resolvedUrl);
        onImageError?.(event);
      }}
    />
  );
}

export default ImageWithFallback;
