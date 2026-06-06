"""
kobra.py — cliente SDK de Kobra.

Único archivo que el desarrollador necesita copiar a su proyecto.
Dependencia: pip install httpx

Uso:
    from kobra import KobraClient

    kobra = KobraClient(api_key="...", base_url="...")
    resultado = kobra.iniciar_cobranza(
        deudor_id="SR-12345",
        nombre="Juan Pérez",
        telefono="+56912345678",
        monto=150000,
    )
    print(resultado.conversation_id)
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx


# ---------------------------------------------------------------------------
# Tipos de respuesta
# ---------------------------------------------------------------------------

@dataclass
class CobranzaResponse:
    ok: bool
    conversation_id: str
    deudor_id: str
    estado: str
    primer_mensaje: str | None = None


@dataclass
class WebhookResponse:
    ok: bool
    url: str
    eventos: list[str]


@dataclass
class StatusResponse:
    sdk_version: str
    configurado: bool
    webhooks_activos: int


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------

class KobraError(Exception):
    """Error retornado por la API de Kobra."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Kobra error {status_code}: {detail}")


class CobranzaYaActiva(KobraError):
    """Ya existe una cobranza activa para ese número de teléfono.

    Atributos:
        existing_conversation_id — ID de la cobranza activa existente.
            Usalo en GET /cobranzas/{id} para consultarla, o en
            POST /cobranzas/{id}/cancelar para cerrarla antes de crear una nueva.
    """
    def __init__(self, status_code: int, detail: str | dict):
        self.existing_conversation_id: str | None = None
        if isinstance(detail, dict):
            self.existing_conversation_id = detail.get("existing_conversation_id")
            message = detail.get("message", str(detail))
        else:
            message = str(detail)
        super().__init__(status_code, message)


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

class KobraClient:
    """
    Cliente para la API SDK de Kobra.

    Parámetros:
        api_key   — la clave que te entregó el equipo de Kobra
        base_url  — URL base del servidor (default: producción)
    """

    DEFAULT_BASE_URL = "https://kobra.remora-ia.com"

    def __init__(self, api_key: str, base_url: str | None = None):
        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._headers = {
            "X-Kobra-Api-Key": api_key,
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Cobranzas
    # ------------------------------------------------------------------

    def iniciar_cobranza(
        self,
        deudor_id: str,
        nombre: str,
        telefono: str,
        monto: float,
        concepto: str | None = None,
        metadata: dict | None = None,
    ) -> CobranzaResponse:
        """
        Dispara una cobranza para un deudor.
        Carolina le escribe por WhatsApp en segundos.

        Lanza:
            CobranzaYaActiva — si ya hay una cobranza activa para ese teléfono
            KobraError       — para cualquier otro error de la API
        """
        body: dict = {
            "deudor_id": deudor_id,
            "nombre": nombre,
            "telefono": telefono,
            "monto": monto,
        }
        if concepto:
            body["concepto"] = concepto
        if metadata:
            body["metadata"] = metadata

        data = self._post("/api/sdk/cobranzas", body, expected_status=201)
        return CobranzaResponse(
            ok=data["ok"],
            conversation_id=data["conversation_id"],
            deudor_id=data["deudor_id"],
            estado=data["estado"],
            primer_mensaje=data.get("primer_mensaje"),
        )

    def listar_cobranzas(
        self,
        estado: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Lista cobranzas con filtros opcionales."""
        params: dict = {"page": page, "page_size": page_size}
        if estado:
            params["estado"] = estado
        return self._get("/api/sdk/cobranzas", params)

    def obtener_cobranza(self, conversation_id: str) -> dict:
        """Detalle de una cobranza por su conversation_id."""
        return self._get(f"/api/sdk/cobranzas/{conversation_id}")

    def cancelar_cobranza(
        self,
        conversation_id: str,
        motivo: str | None = None,
        notificar_deudor: bool = True,
    ) -> dict:
        """Cancela una cobranza activa."""
        body: dict = {"notificar_deudor": notificar_deudor}
        if motivo:
            body["motivo"] = motivo
        return self._post(f"/api/sdk/cobranzas/{conversation_id}/cancelar", body)

    def cobranzas_bulk(self, cobranzas: list[dict]) -> dict:
        """Dispara hasta 500 cobranzas en una sola llamada."""
        return self._post("/api/sdk/cobranzas/bulk", {"cobranzas": cobranzas})

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    def registrar_webhook(
        self,
        url: str,
        eventos: list[str] | None = None,
    ) -> WebhookResponse:
        """
        Registra la URL a la que Kobra enviará eventos.
        Eventos disponibles: "cobrado", "acuerdo". Default: todos.
        Solo necesitás llamar esto una vez.
        """
        body: dict = {"url": url}
        if eventos:
            body["eventos"] = eventos
        data = self._put("/api/sdk/webhook", body)
        return WebhookResponse(ok=data["ok"], url=data["url"], eventos=data["eventos"])

    # ------------------------------------------------------------------
    # Sistema
    # ------------------------------------------------------------------

    def status(self) -> StatusResponse:
        """Verifica que el SDK está configurado y el servidor responde. Sin auth."""
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self._base_url}/api/sdk/status")
            data = resp.json()
        return StatusResponse(
            sdk_version=data["sdk_version"],
            configurado=data["configurado"],
            webhooks_activos=data["webhooks_activos"],
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _post(self, path: str, body: dict, expected_status: int = 200) -> dict:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{self._base_url}{path}",
                json=body,
                headers=self._headers,
            )
        return self._handle(resp, expected_status)

    def _put(self, path: str, body: dict) -> dict:
        with httpx.Client(timeout=30.0) as client:
            resp = client.put(
                f"{self._base_url}{path}",
                json=body,
                headers=self._headers,
            )
        return self._handle(resp, 200)

    def _get(self, path: str, params: dict | None = None) -> dict:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                f"{self._base_url}{path}",
                params=params,
                headers=self._headers,
            )
        return self._handle(resp, 200)

    def _handle(self, resp: httpx.Response, expected_status: int) -> dict:
        if resp.status_code == expected_status:
            return resp.json()
        detail = (
            resp.json().get("detail", resp.text)
            if "application/json" in resp.headers.get("content-type", "")
            else resp.text
        )
        if resp.status_code == 409:
            raise CobranzaYaActiva(409, detail)
        raise KobraError(resp.status_code, detail)
