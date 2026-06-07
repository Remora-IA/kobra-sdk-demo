# seed_real.csv — Datos realistas para test e2e contra producción

> **Cuándo usar:** cuando quieras probar el flujo COMPLETO con datos representativos del cliente real (Sur Profundo / Somos Rentable), no con `+56912345678` ni "Juan Pérez". El founder recibe el WhatsApp en su teléfono real (`+56 9 4294 9490`, fila SR-2026-003).

## Qué tiene el archivo

10 deudores chilenos con datos realistas:

| Campo | Convención |
|---|---|
| `deudor_id` | Patrón `SR-2026-XXX` (formato que Somos Rentable usaría internamente) |
| `nombre` | Nombre + dos apellidos (convención chilena estándar) |
| `telefono` | Formato E.164 con prefijo `+56 9` (móviles Chile). Fila 003 usa `$FOUNDER_WHATSAPP_E164` (se reemplaza con el número del founder desde `kobra/.env.paladin` antes de cargar). |
| `monto` | Pesos chilenos sin decimales. Rango realista para financiamiento de parcelas (CLP 1.4M–4.3M). |
| `concepto` | Frase contextualizada con proyectos reales de Sur Profundo (Parcela 47 Camino Real, Departamento 304 Bello Horizonte, Casa 17 Condominio Las Vertientes, etc.) |

## Cómo cargarlo

### Opción A — Google Sheet (el flujo real del cliente)

1. Abrí Google Drive del founder (`tom3bs@gmail.com`).
2. Creá un nuevo Sheet llamado `Somos Rentable — Cartera Test E2E`.
3. Importá el CSV (Archivo → Importar → Subir).
4. Antes de la sincronización a Kobra, en la fila SR-2026-003 reemplazá `$FOUNDER_WHATSAPP_E164` con el valor de la variable (ver `kobra/.env.paladin`).
5. Compartí el URL del Sheet con la sesión que claimee P-021 (`recursos.sheet_url`).

### Opción B — Direct CSV upload al SDK (cuando el LoadPort Google Sheets aún no exista)

Si `app/providers/load/google_sheets/` no está implementado, una sesión puede iterar el CSV y llamar `POST /api/sdk/cobranzas` por cada fila desde `kobra-sdk-demo`. Esto NO es el flujo del customer, pero sirve como verificación intermedia hasta que P-001 termine de materializar el LoadPort según PR-001.

## Por qué los datos importan

- **Realistic name length**: Carolina genera mensajes que adaptan tono según largo y formalidad del nombre. "Juan Pérez" rompe ese tuning. "Cristóbal Andrés Muñoz Soto" es lo que ve en producción.
- **Realistic amounts**: $150.000 sintético no captura los tonos de cobranza de $3.650.000 reales (más insistencia, menos casualidad).
- **Realistic concepts**: "Cuota octubre" sintético no captura cómo Carolina hace referencia a "Departamento 304 Bello Horizonte" en su opener.
- **Realistic phones**: prefijos chilenos reales (+56 9) — los carriers locales pueden tener handling distinto al sintético.

Si una sesión cae en el atajo de usar el escenario `02_iniciar_cobranza.py` con `+56912345678`, no está probando el producto. Está probando un mock.

## Privacidad

- El número del founder (`+56 9 4294 9490`) NO está en el CSV literalmente — se inyecta desde `kobra/.env.paladin` (gitignored).
- Los otros 9 números son **falsos pero formato real** — no corresponden a personas reales (verificado: prefijos correctos pero sufijos arbitrarios).
- Si alguna fila accidentalmente matchea un número real, reemplazar antes de cargar.
