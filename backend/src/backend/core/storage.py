from fastapi import UploadFile

from .supabase import get_supabase_client

_PUBLIC_BUCKETS = {"avatars", "service-covers"}


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
