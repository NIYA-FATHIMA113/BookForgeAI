import assert from "node:assert/strict";
import test from "node:test";
import { createObjectUrlPreview } from "./objectUrlPreview.js";

test("creates a preview URL for the selected file and revokes it once", () => {
  const file = { name: "restaurant.jpg" };
  const revoked = [];
  const preview = createObjectUrlPreview(file, {
    createObjectURL: (selectedFile) => {
      assert.equal(selectedFile, file);
      return "blob:local-preview";
    },
    revokeObjectURL: (url) => revoked.push(url),
  });

  assert.equal(preview.url, "blob:local-preview");
  preview.revoke();
  preview.revoke();
  assert.deepEqual(revoked, ["blob:local-preview"]);
});

test("does not create a preview URL when no file is selected", () => {
  let created = false;
  assert.equal(createObjectUrlPreview(null, {
    createObjectURL: () => { created = true; return "blob:unused"; },
  }), null);
  assert.equal(created, false);
});
