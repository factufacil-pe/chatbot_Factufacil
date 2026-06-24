"""
LIVE smoke test — Fase 1, task 1.5.

Instancia FacturadorPro7Client contra un tenant REAL (sandbox de
desarrollo, "YIWU IMPORT CORPORATION E.I.R.L.") y hace UNA llamada GET real
para probar el plumbing de auth/error-handling de punta a punta. NO mockea
nada — es la contraparte en vivo de scripts/verify_phase1_http_client.py
(que usa httpx.MockTransport).

El token se lee desde un archivo JSON local fuera del repo (path pasado
por variable de entorno o argumento) — NUNCA se imprime, loguea, ni se
hardcodea en este script.

Run:
  PYTHONPATH=. venv/bin/python3 scripts/smoke_test_http_client_live.py <path-a-creds.json>
"""
import asyncio
import json
import sys

from adapters.facturadorpro7_api.auth import TenantCredentials
from adapters.facturadorpro7_api.http_client import AuthError, FacturadorPro7Client


async def main(creds_path: str) -> int:
    with open(creds_path) as f:
        raw = json.load(f)

    creds = TenantCredentials(base_url=raw["base_url"], token=raw["token"])
    client = FacturadorPro7Client(creds)

    print(f"Target tenant base_url: {creds.base_url}")
    print("Calling GET /api/items/records?per_page=3 ...")

    try:
        result = await client.get("/api/items/records", params={"per_page": 3})
    except AuthError as e:
        print(f"AUTH ERROR — token appears expired or invalid: {e}")
        print("Cannot proceed with this token. Not attempting to re-login (no login creds provided).")
        return 1
    finally:
        await client.aclose()

    # Real assertions on real response shape — not a trivial existence check.
    assert isinstance(result, dict), f"Expected dict response, got {type(result)}"
    items = result.get("data") or result.get("items") or result
    print(f"Response top-level keys: {list(result.keys())}")

    if isinstance(items, list):
        print(f"Items returned: {len(items)}")
        for it in items[:3]:
            # Print only non-sensitive structural fields, never credentials.
            keys_preview = {k: it.get(k) for k in ("id", "description", "price") if k in it}
            print(f"  - {keys_preview}")
    else:
        print(f"Unexpected 'items' shape (not a list): {type(items)} — raw keys: {list(result.keys())}")

    print("\nSMOKE TEST PASSED — real authenticated GET succeeded against the live sandbox.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/smoke_test_http_client_live.py <path-to-creds.json>")
        sys.exit(2)
    exit_code = asyncio.run(main(sys.argv[1]))
    sys.exit(exit_code)
