"""
Cliente HTTP async para la API de FacturadorPro7.

Único punto que sabe de auth/base_url — los 8 adapters (Fase 2) lo reciben
inyectado, no hay 8 implementaciones de HTTP duplicadas. Instanciado POR
REQUEST (nunca global/singleton): `TenantCredentials` es por-request, así
que cachear este cliente entre requests mezclaría tenants. Nunca loguea ni
expone el Bearer token.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from adapters.facturadorpro7_api.auth import TenantCredentials

DEFAULT_TIMEOUT_SECONDS = 30.0


class FacturadorPro7Error(Exception):
    """Base de todos los errores de este cliente."""


class AuthError(FacturadorPro7Error):
    """401 — token inválido o expirado. El caller no debe reintentar con el
    mismo token; debe pedir al frontend que renueve la sesión."""


class ValidationError(FacturadorPro7Error):
    """422 — la API rechazó el payload (campos faltantes/inválidos).
    Expone el detalle de la API para que el agente pueda corregir el
    siguiente intento."""

    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.errors = errors or {}


class UpstreamError(FacturadorPro7Error):
    """5xx — falla del lado de FacturadorPro7, no del request. Conserva el
    status_code para que el caller decida si reintentar."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class FacturadorPro7Client:
    """Cliente Bearer-auth para la API de FacturadorPro7.

    Instanciar UNA VEZ POR REQUEST con las credenciales de ese request
    específico — nunca reusar la misma instancia entre tenants/usuarios.
    """

    def __init__(self, creds: TenantCredentials, *, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self._creds = creds
        self._client = httpx.AsyncClient(
            base_url=creds.base_url,
            headers={
                "Authorization": f"Bearer {creds.token}",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    async def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        response = await self._client.get(path, params=params)
        return self._handle_response(response)

    async def post(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Any:
        response = await self._client.post(path, json=json)
        return self._handle_response(response)

    async def aclose(self) -> None:
        await self._client.aclose()

    def _handle_response(self, response: httpx.Response) -> Any:
        if response.status_code == 401:
            raise AuthError(self._safe_message(response, default="Unauthenticated."))
        if response.status_code == 422:
            body = self._safe_json(response)
            message = (body or {}).get("message", "Validation failed.")
            errors = (body or {}).get("errors", {})
            raise ValidationError(message, errors=errors)
        if response.status_code >= 500:
            raise UpstreamError(
                self._safe_message(response, default="Upstream server error."),
                status_code=response.status_code,
            )
        response.raise_for_status()
        return self._safe_json(response)

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return None

    @classmethod
    def _safe_message(cls, response: httpx.Response, *, default: str) -> str:
        body = cls._safe_json(response)
        if isinstance(body, dict) and "message" in body:
            return str(body["message"])
        return default
