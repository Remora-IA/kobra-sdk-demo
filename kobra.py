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
    link_pago: str | None = None


@dataclass
class WebhookResponse:
    ok: bool
    url: str
    eventos: list[str]
    signing_secret: str | None = None
    """
    Secreto para verificar firmas HMAC-SHA256 en los webhooks entrantes.
    Se muestra UNA SOLA VEZ — guardalo de inmediato en tu configuración.
    Usalo en servidor_webhooks.py para validar X-Kobra-Signature.
    """


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
    """
    Ya existe una cobranza activa para ese número de teléfono.

    Dos sub-casos:
    - Creada por el SDK → existing_conversation_id disponible, podés
      consultarla con obtener_cobranza() o cancelarla con cancelar_cobranza().
    - Creada desde el panel de operadores (externa) → existing_conversation_id
      es None, no es gestionable vía API. Contactá al equipo de Kobra.
    """
    def __init__(self, status_code: int, detail: str | dict):
        self.existing_conversation_id: str | None = None
        self.es_externa: bool = False

        if isinstance(detail, dict):
            # El backend puede devolver {"detail": {...}} o directo {"existing_conversation_id": ...}
            inner = detail.get("detail", detail) if isinstance(detail.get("detail"), dict) else detail
            self.existing_conversation_id = inner.get("existing_conversation_id")
            self.es_externa = inner.get("tipo") == "externa"
            message = inner.get("message", str(detail))
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
            CobranzaYaActiva — si ya hay una cobranza activa para ese teléfono.
                               Revisá .es_externa y .existing_conversation_id.
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
            link_pago=data.get("link_pago"),
        )

    def listar_cobranzas(
        self,
        estado: str | None = None,
        creadas_desde: str | None = None,
        cambiado_desde: str | None = None,
        cursor: str | None = None,
        limite: int = 100,
    ) -> dict:
        """
        Lista cobranzas con filtros opcionales.

        Parámetros:
            estado          — "en_curso", "cobrado", "acuerdo", "rendido", "cancelado"
            creadas_desde   — ISO 8601, ej: "2026-06-01T00:00:00Z"
            cambiado_desde  — ISO 8601, útil para reconciliaciones incrementales
            cursor          — token opaco devuelto en next_cursor para paginar
            limite          — 1-100, default 100
        """
        params: dict = {"limite": limite}
        if estado:
            params["estado"] = estado
        if creadas_desde:
            params["creadas_desde"] = creadas_desde
        if cambiado_desde:
            params["cambiado_desde"] = cambiado_desde
        if cursor:
            params["cursor"] = cursor
        return self._get("/api/sdk/cobranzas", params)

    def obtener_cobranza(self, conversation_id: str, incluir: str | None = None) -> dict:
        """
        Detalle de una cobranza por su conversation_id.

        Parámetros:
            incluir — "mensajes", "eventos", o "mensajes,eventos"
                      Sin este parámetro devuelve solo metadatos livianos.
        """
        params = {"incluir": incluir} if incluir else None
        return self._get(f"/api/sdk/cobranzas/{conversation_id}", params)

    def cancelar_cobranza(
        self,
        conversation_id: str,
        motivo: str = "error_carga",
        notificar_deudor: bool = False,
    ) -> dict:
        """
        Cancela una cobranza activa creada por el SDK.

        Parámetros:
            motivo          — "pago_externo_verificado", "deudor_fallecido",
                              "deuda_disputada", "error_carga", "otro"
            notificar_deudor — si True, Carolina envía mensaje final al deudor
        """
        body: dict = {
            "motivo": motivo,
            "notificar_deudor": notificar_deudor,
        }
        return self._post(f"/api/sdk/cobranzas/{conversation_id}/cancelar", body)

    def cobranzas_bulk(self, cobranzas: list[dict]) -> dict:
        """
        Dispara hasta 500 cobranzas en una sola llamada.
        Las que fallen (duplicadas, teléfono inválido) no bloquean las demás.
        Respuesta incluye: iniciadas, duplicadas, errores.
        """
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

        Eventos disponibles: "cobrado", "acuerdo", "no_responde", "cancelado".
        Sin especificar eventos, recibís todos.

        IMPORTANTE: la respuesta incluye signing_secret UNA SOLA VEZ.
        Guardalo en tu configuración — lo necesitás para verificar
        X-Kobra-Signature en cada webhook entrante.
        """
        body: dict = {"url": url}
        if eventos:
            body["eventos"] = eventos
        data = self._put("/api/sdk/webhook", body)
        return WebhookResponse(
            ok=data["ok"],
            url=data["url"],
            eventos=data["eventos"],
            signing_secret=data.get("signing_secret"),
        )

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
        is_json = "application/json" in resp.headers.get("content-type", "")
        body = resp.json() if is_json else {}
        detail = body.get("detail", resp.text) if is_json else resp.text
        if resp.status_code == 409:
            raise CobranzaYaActiva(409, body if is_json else detail)
        raise KobraError(resp.status_code, detail)
