export function createObjectUrlPreview(
  file,
  {
    createObjectURL = (value) => URL.createObjectURL(value),
    revokeObjectURL = (url) => URL.revokeObjectURL(url),
  } = {},
) {
  if (!file) return null;

  const url = createObjectURL(file);
  let revoked = false;

  return {
    url,
    revoke() {
      if (revoked) return;
      revoked = true;
      revokeObjectURL(url);
    },
  };
}
