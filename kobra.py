"""
kobra.py — cliente SDK de Kobra para Somos Rentable.

Este es el único archivo que Somos Rentable necesita copiar a su proyecto.
No es un package — es un módulo de una sola dependencia (httpx).

Uso:
    from kobra import KobraClient

    kobra = KobraClient(api_key="...", base_url="...")
    resultado = await kobra.iniciar_cobranza(
        deudor_id="SR-12345",
        nombre="Juan Pérez",
        telefono="+56912345678",
        monto=150000,
    )
"""

from __future__ import annotations

import httpx


class KobraError(Exception):
    """Error retornado por la API de Kobra."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Kobra error {status_code}: {detail}")


class CobranzaYaActiva(KobraError):
    """Ya existe una cobranza activa para ese número de teléfono."""
    pass


class KobraClient:
    """
    Cliente para la API SDK de Kobra.

    Parámetros:
        api_key   — la clave que te entregó el equipo de Kobra
        base_url  — URL base del servidor (default: producción)
    """

    DEFAULT_BASE_URL = "https://kobra-backend-760602975866.us-central1.run.app"

    def __init__(self, api_key: str, base_url: str | None = None):
        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._headers = {
            "X-Kobra-Api-Key": api_key,
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Métodos principales
    # ------------------------------------------------------------------

    async def iniciar_cobranza(
        self,
        deudor_id: str,
        nombre: str,
        telefono: str,
        monto: float,
        concepto: str | None = None,
    ) -> dict:
        """
        Dispara una cobranza para un deudor.

        Carolina le escribe por WhatsApp en segundos.

        Parámetros:
            deudor_id  — tu ID interno (lo recibís de vuelta en los webhooks)
            nombre     — nombre completo del deudor
            telefono   — formato E.164: "+56912345678"
            monto      — pesos chilenos, sin decimales
            concepto   — opcional, aparece en el comprobante que recibe el deudor

        Retorna dict con: ok, conversation_id, deudor_id, estado, primer_mensaje

        Lanza:
            CobranzaYaActiva  — si ya hay una cobranza activa para ese teléfono
            KobraError        — para cualquier otro error de la API
        """
        body = {
            "deudor_id": deudor_id,
            "nombre": nombre,
            "telefono": telefono,
            "monto": monto,
        }
        if concepto:
            body["concepto"] = concepto

        return await self._post("/api/sdk/cobranza", body, expected_status=201)

    async def registrar_webhook(
        self,
        url: str,
        eventos: list[str] | None = None,
    ) -> dict:
        """
        Registra la URL a la que Kobra enviará eventos.

        Eventos disponibles: "cobrado", "acuerdo"
        Si no especificás eventos, recibís todos.

        Solo necesitás llamar esto una vez (o cuando cambie tu URL).
        """
        body: dict = {"url": url}
        if eventos:
            body["eventos"] = eventos
        return await self._put("/api/sdk/webhook", body)

    async def status(self) -> dict:
        """
        Verifica que el SDK está configurado y el servidor responde.
        No requiere autenticación.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base_url}/api/sdk/status")
            return resp.json()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _post(self, path: str, body: dict, expected_status: int = 200) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}{path}",
                json=body,
                headers=self._headers,
            )
            return self._handle(resp, expected_status)

    async def _put(self, path: str, body: dict) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(
                f"{self._base_url}{path}",
                json=body,
                headers=self._headers,
            )
            return self._handle(resp, 200)

    def _handle(self, resp: httpx.Response, expected_status: int) -> dict:
        if resp.status_code == expected_status:
            return resp.json()
        detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        if resp.status_code == 409:
            raise CobranzaYaActiva(409, detail)
        raise KobraError(resp.status_code, detail)
