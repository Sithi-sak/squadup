from functools import lru_cache

import httpx
from supabase import Client, ClientOptions, create_client

from .config import get_settings

# Supabase's edge closes idle keep-alive connections, and postgrest-py's own `send_with_retry`
# only retries on response *status* codes - a connection dropped before any response exists
# raises `httpx.RemoteProtocolError: Server disconnected` straight out of the call site (4.53).
# Expiring pooled connections well inside the server's idle window means we reconnect rather
# than hand PostgREST a socket it has already closed.
KEEPALIVE_EXPIRY_SECONDS = 15.0
TRANSPORT_RETRIES = 2

# One client now backs PostgREST, Storage and Auth, so this replaces three different library
# defaults (120s for PostgREST, 20s for Storage). 60s leaves room for an image upload on a slow
# connection while still capping a query that has hung.
REQUEST_TIMEOUT_SECONDS = 60.0
CONNECT_TIMEOUT_SECONDS = 10.0

# Only methods that are safe to replay. A dropped POST is left to fail loudly: every multi-step
# write that matters is a single transaction (`submit_review`), so the caller retrying is correct
# and silent replay here could double one that actually committed.
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class _RetryOnDisconnectTransport(httpx.HTTPTransport):
    """`httpx.HTTPTransport(retries=...)` covers connect failures only, not a connection that
    dies mid-request after being handed out of the pool - which is the failure we actually see."""

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        attempts = TRANSPORT_RETRIES if request.method in IDEMPOTENT_METHODS else 0
        for attempt in range(attempts + 1):
            try:
                return super().handle_request(request)
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.WriteError):
                if attempt == attempts:
                    raise
        raise AssertionError("unreachable")


def _build_httpx_client() -> httpx.Client:
    return httpx.Client(
        transport=_RetryOnDisconnectTransport(
            http2=True,
            retries=TRANSPORT_RETRIES,
            limits=httpx.Limits(keepalive_expiry=KEEPALIVE_EXPIRY_SECONDS),
        ),
        timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS),
        follow_redirects=True,
    )


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        ClientOptions(httpx_client=_build_httpx_client()),
    )
