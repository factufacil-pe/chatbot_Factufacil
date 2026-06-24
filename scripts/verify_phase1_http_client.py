"""
RED -> GREEN -> TRIANGULATE for adapters/facturadorpro7_api/http_client.py.

Uses httpx.MockTransport (built into httpx 0.28.1, already in the venv) to
exercise the client's request/response/error-mapping plumbing WITHOUT any
network call — these are unit-level checks on real branching logic (status
code -> exception type). The separate live smoke test
(scripts/smoke_test_http_client_live.py) proves the same client against the
real sandbox tenant end-to-end.

Run: PYTHONPATH=. venv/bin/python3 scripts/verify_phase1_http_client.py
"""
import asyncio
import sys

import httpx

from adapters.facturadorpro7_api.auth import TenantCredentials
from adapters.facturadorpro7_api.http_client import (
    AuthError,
    FacturadorPro7Client,
    UpstreamError,
    ValidationError,
)

PASS = []
FAIL = []


def check(name: str, condition: bool):
    if condition:
        PASS.append(name)
    else:
        FAIL.append(name)
        print(f"FAIL: {name}")


def make_client(handler) -> FacturadorPro7Client:
    creds = TenantCredentials(base_url="https://fake.tenant.test", token="fake-token-123")
    client = FacturadorPro7Client(creds)
    # Swap the internal httpx.AsyncClient's transport for a mock — this is
    # the standard httpx testing pattern, does not touch the network.
    client._client._transport = httpx.MockTransport(handler)
    return client


def check_bearer_header_sent():
    """Real assertion: the client must send the EXACT token from
    TenantCredentials as a Bearer header — not a hardcoded/fake one."""
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"data": []})

    client = make_client(handler)
    asyncio.run(client.get("/api/items/records"))
    check("GET request carries 'Bearer fake-token-123' Authorization header",
          seen["auth"] == "Bearer fake-token-123")


def check_successful_get_returns_json():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"id": 1, "description": "Tornillo"}]})

    client = make_client(handler)
    result = asyncio.run(client.get("/api/items/records"))
    check("Successful GET returns parsed JSON body with real data",
          result["data"][0]["description"] == "Tornillo")


def check_401_raises_auth_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthenticated."})

    client = make_client(handler)
    try:
        asyncio.run(client.get("/api/items/records"))
        check("401 response raises AuthError", False)
    except AuthError as e:
        check("401 response raises AuthError", True)
        check("AuthError message includes upstream message",
              "Unauthenticated" in str(e))


def check_422_raises_validation_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "The description field is required.",
                                          "errors": {"description": ["required"]}})

    client = make_client(handler)
    try:
        asyncio.run(client.post("/api/item", json={"price": 1.0}))
        check("422 response raises ValidationError", False)
    except ValidationError as e:
        check("422 response raises ValidationError", True)
        check("ValidationError exposes upstream field errors",
              "description" in str(e))


def check_500_raises_upstream_error():
    """Triangulation case #1 for the 5xx branch: 500 -> UpstreamError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    client = make_client(handler)
    try:
        asyncio.run(client.get("/api/report"))
        check("500 response raises UpstreamError", False)
    except UpstreamError as e:
        check("500 response raises UpstreamError", True)
        check("UpstreamError carries status_code=500", e.status_code == 500)


def check_503_also_raises_upstream_error():
    """Triangulation case #2 for the 5xx branch: a DIFFERENT 5xx status
    (503) must hit the same UpstreamError branch, proving the mapping is a
    range check (>=500), not a hardcoded == 500."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    client = make_client(handler)
    try:
        asyncio.run(client.get("/api/report"))
        check("503 response ALSO raises UpstreamError (range, not ==500)", False)
    except UpstreamError as e:
        check("503 response ALSO raises UpstreamError (range, not ==500)", True)
        check("UpstreamError carries status_code=503 (different from prior test)",
              e.status_code == 503)


def check_token_never_appears_in_exception_str():
    """Security-critical assertion from design.md: never log/leak the
    Bearer token. Force an error path and confirm the token string is
    absent from the exception's string representation."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Unauthenticated."})

    client = make_client(handler)
    try:
        asyncio.run(client.get("/api/items/records"))
    except AuthError as e:
        check("Token does not leak into AuthError string representation",
              "fake-token-123" not in str(e))


def check_post_sends_json_body():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content
        return httpx.Response(201, json={"id": 42})

    client = make_client(handler)
    result = asyncio.run(client.post("/api/item", json={"description": "Nuevo", "price": 5.0}))
    check("POST sends a non-empty JSON body", b"Nuevo" in seen["body"])
    check("POST returns parsed JSON response", result["id"] == 42)


def check_per_request_instantiation_not_singleton():
    """Design decision: FacturadorPro7Client must be instantiated PER
    REQUEST, never global/singleton. Prove two instances with different
    creds carry independent state (different tokens, different underlying
    httpx.AsyncClient objects)."""
    creds_a = TenantCredentials(base_url="https://tenant-a.test", token="token-a")
    creds_b = TenantCredentials(base_url="https://tenant-b.test", token="token-b")
    client_a = FacturadorPro7Client(creds_a)
    client_b = FacturadorPro7Client(creds_b)
    check("Two client instances are NOT the same object", client_a is not client_b)
    check("Two client instances hold different underlying httpx.AsyncClient objects",
          client_a._client is not client_b._client)


def main():
    check_bearer_header_sent()
    check_successful_get_returns_json()
    check_401_raises_auth_error()
    check_422_raises_validation_error()
    check_500_raises_upstream_error()
    check_503_also_raises_upstream_error()
    check_token_never_appears_in_exception_str()
    check_post_sends_json_body()
    check_per_request_instantiation_not_singleton()

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILED CHECKS:")
        for name in FAIL:
            print(f"  - {name}")
        sys.exit(1)
    print("ALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
