import io

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError
from storage3.exceptions import StorageApiError

from .supabase import get_supabase_client

_PUBLIC_BUCKETS = {"avatars", "service-covers", "post-images", "message-images"}

_MAX_IMAGE_DIMENSION = 1920


def _store(bucket: str, path: str, data: bytes, content_type: str) -> str:
    """Uploads raw bytes and returns the public URL for public buckets, or the bare storage path
    for private ones. A bucket's `file_size_limit` rejection (413) comes back as a readable
    HTTPException instead of a 500 - an unhandled error escapes the CORS middleware, so the
    browser only ever sees "Failed to fetch"."""
    bucket_client = get_supabase_client().storage.from_(bucket)
    try:
        bucket_client.upload(path, data, {"content-type": content_type, "upsert": "true"})
    except StorageApiError as exc:
        if str(exc.status) == "413":
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "That file is too large. Please upload a smaller image.",
            ) from exc
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not store that file") from exc
    if bucket in _PUBLIC_BUCKETS:
        return bucket_client.get_public_url(path)
    return path


def upload_file(bucket: str, path: str, file: UploadFile) -> str:
    """Uploads a file as-is to a Supabase Storage bucket via the service-role client (the buckets
    have no write policies for anon/authenticated yet, see supabase/migrations 2.4)."""
    return _store(bucket, path, file.file.read(), file.content_type or "application/octet-stream")


def _encode_image(file: UploadFile, image_format: str, quality: int) -> bytes:
    """Downscales an upload to fit `_MAX_IMAGE_DIMENSION` and re-encodes it, so a full-resolution
    phone photo doesn't burn through Supabase Storage (or trip a bucket's size limit) for no
    visual benefit."""
    try:
        image = ImageOps.exif_transpose(Image.open(file.file))
    except UnidentifiedImageError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "That file isn't a readable image") from exc
    if image is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "That file isn't a readable image")
    keep_alpha = image_format == "WEBP" and image.mode == "RGBA"
    image = image if keep_alpha else image.convert("RGB")
    image.thumbnail((_MAX_IMAGE_DIMENSION, _MAX_IMAGE_DIMENSION))

    buffer = io.BytesIO()
    image.save(buffer, format=image_format, quality=quality)
    return buffer.getvalue()


def upload_image_as_webp(bucket: str, path: str, file: UploadFile, quality: int = 80) -> str:
    """Re-encodes an uploaded image as WebP before storing it. `path` should have no extension -
    `.webp` is appended here."""
    return _store(bucket, f"{path}.webp", _encode_image(file, "WEBP", quality), "image/webp")


def upload_document(bucket: str, path: str, file: UploadFile, quality: int = 85) -> str:
    """ID / verification uploads into a private bucket. Photos are re-encoded as JPEG (the
    `id-documents` bucket only allows png/jpeg/pdf, so WebP is out) at a higher quality than feed
    images since a reviewer has to read the text on the card; PDFs pass through untouched."""
    if (file.content_type or "").startswith("image/"):
        return _store(bucket, f"{path}.jpg", _encode_image(file, "JPEG", quality), "image/jpeg")
    return upload_file(bucket, path, file)


def remove_prefix(bucket: str, prefix: str) -> int:
    """Deletes every object directly under `prefix/` in `bucket` and returns how many went.

    Used by account deletion (4.52) - the DB cascade never reaches `storage.objects`, so the
    files have to be swept explicitly. Every upload path in this app is `{owner_id}/{file}`, one
    flat level, so a single listing per prefix covers it.

    The empty prefix is refused outright: Storage would happily list the bucket root and this
    would turn into "delete every user's files". Listing is capped at 100 rows per call, so this
    re-lists from offset 0 after each batch (the removed rows are gone from the next listing)
    until the prefix is empty.
    """
    if not prefix or "/" in prefix:
        raise ValueError(f"remove_prefix expects a single non-empty path segment, got {prefix!r}")
    bucket_client = get_supabase_client().storage.from_(bucket)
    removed = 0
    # A prefix holds one file per upload, so this bound is generous; it only exists so a Storage
    # bug that keeps returning the same rows can't spin forever.
    for _ in range(100):
        entries = bucket_client.list(prefix)
        # Storage returns a placeholder row with a null id for a nested folder; there are none
        # under these prefixes today, and skipping them keeps the call from 400-ing if that changes.
        names = [entry["name"] for entry in entries if entry.get("id")]
        if not names:
            return removed
        bucket_client.remove([f"{prefix}/{name}" for name in names])
        removed += len(names)
    return removed


def create_signed_url(bucket: str, path: str, expires_in: int = 3600) -> str:
    """Signed URL for a private bucket (e.g. `id-documents`), so a bare storage path from
    `upload_file` can actually be viewed (admin Pal-application review, 3.19)."""
    signed = get_supabase_client().storage.from_(bucket).create_signed_url(path, expires_in)
    return signed["signedURL"]
