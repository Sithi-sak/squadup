import io

from fastapi import UploadFile
from PIL import Image, ImageOps

from .supabase import get_supabase_client

_PUBLIC_BUCKETS = {"avatars", "service-covers", "post-images"}

_MAX_IMAGE_DIMENSION = 1920


def upload_file(bucket: str, path: str, file: UploadFile) -> str:
    """Uploads a file to a Supabase Storage bucket via the service-role client (the buckets
    have no write policies for anon/authenticated yet, see supabase/migrations 2.4). Returns
    the public URL for public buckets, or the bare storage path for private ones."""
    data = file.file.read()
    content_type = file.content_type or "application/octet-stream"
    bucket_client = get_supabase_client().storage.from_(bucket)
    bucket_client.upload(path, data, {"content-type": content_type, "upsert": "true"})
    if bucket in _PUBLIC_BUCKETS:
        return bucket_client.get_public_url(path)
    return path


def upload_image_as_webp(bucket: str, path: str, file: UploadFile, quality: int = 80) -> str:
    """Re-encodes an uploaded image as WebP (downscaled to fit `_MAX_IMAGE_DIMENSION`) before
    storing it, so a full-resolution phone photo doesn't burn through Supabase Storage for no
    visual benefit at feed-card size. `path` should have no extension - `.webp` is appended
    here. Returns the public URL (the bucket must be in `_PUBLIC_BUCKETS`)."""
    image = ImageOps.exif_transpose(Image.open(file.file))
    if image is None:
        raise ValueError("Could not read image")
    image = image.convert("RGB") if image.mode not in ("RGB", "RGBA") else image
    image.thumbnail((_MAX_IMAGE_DIMENSION, _MAX_IMAGE_DIMENSION))

    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=quality)

    bucket_client = get_supabase_client().storage.from_(bucket)
    webp_path = f"{path}.webp"
    bucket_client.upload(webp_path, buffer.getvalue(), {"content-type": "image/webp", "upsert": "true"})
    return bucket_client.get_public_url(webp_path)


def create_signed_url(bucket: str, path: str, expires_in: int = 3600) -> str:
    """Signed URL for a private bucket (e.g. `id-documents`), so a bare storage path from
    `upload_file` can actually be viewed (admin Pal-application review, 3.19)."""
    signed = get_supabase_client().storage.from_(bucket).create_signed_url(path, expires_in)
    return signed["signedURL"]
