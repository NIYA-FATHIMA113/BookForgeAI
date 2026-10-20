import assert from "node:assert/strict";
import test from "node:test";
import { getApiErrorMessage } from "./apiErrorMessage.js";

test("formats backend image validation errors with the image field label", () => {
  assert.equal(
    getApiErrorMessage({ hero_image: ["Images must be 8 MB or smaller."] }, 400),
    "Website photo: Images must be 8 MB or smaller.",
  );
});

test("uses a direct backend message and falls back to the HTTP status", () => {
  assert.equal(getApiErrorMessage({ detail: "Not authorized." }, 403), "Not authorized.");
  assert.equal(getApiErrorMessage({}, 500), "Request failed with status 500");
});
