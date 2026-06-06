# Flujos del SDK — qué puedo hacer y cómo

Cada flujo responde a una intención real del developer.

---

## "Quiero que Carolina le escriba a un deudor"

```
Tu sistema                    Kobra
─────────────────────────────────────────────────────
Vence una cuota
    │
    ├─► iniciar_cobranza() ──► Carolina escribe por WhatsApp
    │
    │   Kobra responde:
    │   ✓ conversation_id    ← guardalo para rastrear el caso
    │   ✓ primer_mensaje     ← el texto que Carolina le mandó
```

**Cuándo se usa:** cada vez que un cliente no paga en el plazo definido.
**Frecuencia:** una vez por deuda vencida.

---

## "Quiero saber cuándo me pagan"

```
Tu sistema                    Kobra
─────────────────────────────────────────────────────
[Una sola vez al integrar]
    │
    ├─► registrar_webhook() ──► Kobra registra tu URL
    │   (URL de tu sistema)
    │
    │   [Días después, el deudor paga]
    │
    ◄── POST a tu URL ◄──────── Kobra detecta el pago
        evento: "cobrado"
        deudor_id, monto
    │
    ▼
Tu sistema marca la deuda como pagada
```

**Cuándo se usa:** una sola vez al configurar la integración.
**Lo que llega:** eventos `cobrado`, `acuerdo`, `no_responde`, `cancelado`.

---

## "Quiero ver en qué están mis cobranzas"

```
Tu sistema                    Kobra
─────────────────────────────────────────────────────
¿Cuántas están activas?
    ├─► listar_cobranzas()        ← todas, o filtradas por estado
    │   estados: en_curso / cobrado / acuerdo / rendido / cancelado

¿Qué pasó con esta en particular?
    ├─► obtener_cobranza(id)      ← detalle de una cobranza
        incluir: "mensajes"       ← conversación completa con el deudor
        incluir: "eventos"        ← historial de lo que pasó
```

**Cuándo se usa:** para reconciliación, reportes, o debugging.

---

## "Quiero parar una cobranza"

```
Tu sistema                    Kobra
─────────────────────────────────────────────────────
El cliente pagó por otro medio / error / disputa
    │
    ├─► cancelar_cobranza(id, motivo)
    │   motivos: pago_externo_verificado / deuda_disputada /
    │            deudor_fallecido / error_carga / otro
    │
    │   notificar_deudor=True → Carolina le avisa al deudor
    │   notificar_deudor=False → cancelación silenciosa
```

**Cuándo se usa:** cuando la deuda se resuelve por fuera de Kobra.

---

## "Tengo muchos deudores para dar de alta de una vez"

```
Tu sistema                    Kobra
─────────────────────────────────────────────────────
Fin de mes: 300 cuotas vencieron
    │
    ├─► cobranzas_bulk([...])    ← hasta 500 en una llamada
    │
    │   Kobra responde:
    │   iniciadas:  297          ← arrancaron OK
    │   duplicadas:   2          ← ya tenían cobranza activa
    │   errores:      1          ← teléfono inválido
```

**Cuándo se usa:** procesos de fin de mes, migraciones, cargas masivas.

---

## "Quiero verificar que todo está configurado"

```
Tu sistema                    Kobra
─────────────────────────────────────────────────────
    ├─► status()                 ← sin autenticación
    │
    │   sdk_version: "0.5.0"
    │   configurado: true
    │   webhooks_activos: 1
```

**Cuándo se usa:** health check en monitoreo, o antes de una demo.
