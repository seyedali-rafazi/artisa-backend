"""Migration notes for moving legacy /uploads product images to Vercel Blob.

Existing MongoDB documents may still contain URLs such as:

  https://artisa-backend.vercel.app/uploads/<filename>.webp
  /uploads/<filename>.webp

Because the Vercel filesystem is ephemeral, those files are often already gone.
New uploads always go to Vercel Blob and store a public Blob URL in `image`
(and `gallery[]`).

Recommended migration (manual / one-off script):

1. Export products whose `image` (or gallery entries) contain `/uploads/`.
2. For each URL, if the file is still reachable, download it.
3. POST the bytes through the admin upload pipeline (or call
   `process_and_upload_image` / `validate_and_optimize_image` + `upload_image`).
4. Update the product document with the new Blob URL.
5. Leave unreachable legacy URLs as-is (or replace with a placeholder) so the
   storefront keeps working for products that still have valid external images.

Do NOT delete legacy `/uploads` references automatically without verifying the
Blob copy succeeded.
"""
