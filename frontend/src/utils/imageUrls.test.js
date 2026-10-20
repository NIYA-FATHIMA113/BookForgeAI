import assert from "node:assert/strict";
import test from "node:test";
import { getImageRenderState, resolveImageUrl } from "./imageUrls.js";

const apiBaseUrl = "https://bookforge-api.onrender.com";

test("resolves root-relative media URLs against the API host", () => {
  assert.equal(
    resolveImageUrl("/media/businesses/logos/spice-garden.png", { apiBaseUrl, pageProtocol: "https:" }),
    "https://bookforge-api.onrender.com/media/businesses/logos/spice-garden.png",
  );
});

test("resolves relative upload paths against the API host, not the frontend path", () => {
  assert.equal(
    resolveImageUrl("businesses/hero/restaurant.webp", { apiBaseUrl, pageProtocol: "https:" }),
    "https://bookforge-api.onrender.com/businesses/hero/restaurant.webp",
  );
});

test("keeps valid external image URLs and query strings", () => {
  const url = "https://images.example.test/hero.jpg?width=1200&quality=85";
  assert.equal(resolveImageUrl(url, { apiBaseUrl, pageProtocol: "https:" }), url);
});

test("resolves protocol-relative image URLs using the page scheme", () => {
  assert.equal(
    resolveImageUrl("//images.example.test/hero.jpg", { apiBaseUrl, pageProtocol: "https:" }),
    "https://images.example.test/hero.jpg",
  );
});

test("upgrades an HTTP image URL on an HTTPS page to avoid mixed content", () => {
  assert.equal(
    resolveImageUrl("http://bookforge-api.onrender.com/media/logo.png", { apiBaseUrl, pageProtocol: "https:" }),
    "https://bookforge-api.onrender.com/media/logo.png",
  );
});

test("remaps localhost image URLs to the configured deployed API host", () => {
  assert.equal(
    resolveImageUrl("http://127.0.0.1:8000/media/businesses/hero/shop.jpg", { apiBaseUrl, pageProtocol: "https:" }),
    "https://bookforge-api.onrender.com/media/businesses/hero/shop.jpg",
  );
});

test("rejects missing, placeholder, malformed, whitespace, and non-web URLs", () => {
  for (const value of [null, "", "  ", "undefined", "null", "javascript:alert(1)", "file:///tmp/image.png", "https://[", "https://images.example.test/hero image.png"]) {
    assert.equal(resolveImageUrl(value, { apiBaseUrl, pageProtocol: "https:" }), null, String(value));
  }
});

test("shows the fallback when an image URL is missing or fails to load", () => {
  assert.deepEqual(getImageRenderState(null), { showFallback: true, showImage: false });
  assert.deepEqual(getImageRenderState(resolveImageUrl("not a URL", { apiBaseUrl: "" })), { showFallback: true, showImage: false });
  assert.deepEqual(getImageRenderState("https://api.example.test/media/missing.png", true), { showFallback: true, showImage: false });
});

test("shows the image when its URL is valid and it has not failed", () => {
  assert.deepEqual(getImageRenderState("https://api.example.test/media/logo.png"), { showFallback: false, showImage: true });
});
