# Chatbot Hotelero — Prototipo WhatsApp + Gemini + FastAPI

> **Alcance:** Prototipo funcional para demostración. No está pensado para producción.
> **Stack:** Python 3.11+, FastAPI, SQLite, Google Gemini API, WhatsApp Cloud API (Meta).

---

## Tabla de contenidos

1. [Resumen del proyecto](#1-resumen-del-proyecto)
2. [Arquitectura](#2-arquitectura)
3. [Funcionalidades del prototipo](#3-funcionalidades-del-prototipo)
4. [Requisitos previos](#4-requisitos-previos)
5. [Estructura del proyecto](#5-estructura-del-proyecto)
6. [Fases de desarrollo](#6-fases-de-desarrollo)
   - [Fase 0 — Preparación del entorno](#fase-0--preparación-del-entorno)
   - [Fase 1 — Cuentas y credenciales](#fase-1--cuentas-y-credenciales)
   - [Fase 2 — Scaffold del backend FastAPI](#fase-2--scaffold-del-backend-fastapi)
   - [Fase 3 — Webhook de WhatsApp](#fase-3--webhook-de-whatsapp)
   - [Fase 4 — Base de datos SQLite](#fase-4--base-de-datos-sqlite)
   - [Fase 5 — Integración con Gemini](#fase-5--integración-con-gemini)
   - [Fase 6 — Tools (reglas de negocio)](#fase-6--tools-reglas-de-negocio)
   - [Fase 7 — Orquestador conversacional](#fase-7--orquestador-conversacional)
   - [Fase 8 — Pruebas de escenarios](#fase-8--pruebas-de-escenarios)
   - [Fase 9 — Demo y cierre del prototipo](#fase-9--demo-y-cierre-del-prototipo)
7. [Variables de entorno](#7-variables-de-entorno)
8. [Costes del prototipo](#8-costes-del-prototipo)
9. [Limitaciones conocidas](#9-limitaciones-conocidas)
10. [Roadmap sugerido (4 días)](#10-roadmap-sugerido-4-días)
11. [Referencias](#11-referencias)

---

## 1. Resumen del proyecto

Asistente conversacional para el sector hotelero que opera por **WhatsApp**. El huésped escribe mensajes; un backend **FastAPI** los recibe, consulta datos en **SQLite** y usa **Gemini** para entender lenguaje natural y generar respuestas. Las acciones críticas (cancelaciones, códigos de acceso, penalizaciones) las ejecuta **código Python determinista**, no la IA.

### Objetivos del prototipo

| Objetivo | Descripción |
|----------|-------------|
| Confirmar acceso | Entregar código de habitación tras validar reserva |
| Cancelaciones | Calcular penalización según política y confirmar |
| Notificación de llegada | Registrar hora estimada de llegada del huésped |
| Soporte en horas pico | Responder FAQs; escalar a "recepción humana" simulada |
| Limpieza | Consultar estado y horario de housekeeping |
| Reservas | Consultar reserva por teléfono WhatsApp |
| Costos (staff) | Consulta interna de coste operativo por habitación |

---

## 2. Arquitectura

```
┌─────────────┐     webhook      ┌──────────────────┐
│  WhatsApp   │ ───────────────► │  FastAPI         │
│  (Meta API) │ ◄─────────────── │  /webhook        │
└─────────────┘     respuesta    └────────┬─────────┘
                                          │
                         ┌────────────────┼────────────────┐
                         ▼                ▼                ▼
                  ┌───────────┐   ┌────────────┐   ┌───────────┐
                  │  Gemini   │   │  SQLite    │   │  Tools    │
                  │  (NLU +   │   │  (reservas,│   │  (reglas  │
                  │  respuesta)│   │  huéspedes)│   │  negocio) │
                  └───────────┘   └────────────┘   └───────────┘
```

### Flujo de un mensaje

1. Huésped envía mensaje por WhatsApp.
2. Meta hace `POST` al webhook público (ngrok en desarrollo).
3. FastAPI identifica el teléfono y carga historial de sesión.
4. Se envía contexto + mensaje a Gemini.
5. Si Gemini solicita una **tool**, el backend la ejecuta y reenvía el resultado.
6. FastAPI responde al huésped vía WhatsApp Cloud API.

---

## 3. Funcionalidades del prototipo

### Incluido

- Conversación en español con Gemini Flash (tier gratuito).
- Consulta de reserva por número de teléfono.
- Check-in simulado con código de acceso.
- Cancelación con cálculo de penalización (Flexible / Moderada / No reembolsable).
- Registro de hora de llegada.
- Consulta de estado de limpieza por habitación.
- FAQs hoteleras (desayuno, WiFi, parking, recepción).
- Modo "escalar a recepción" (respuesta simulada).

### Excluido (fuera de alcance)

- Integración con PMS real (Cloudbeds, Mews, etc.).
- Pasarela de pagos.
- Channel manager multicanal real.
- Despliegue en producción.
- Verificación de negocio Meta.
- App móvil para staff.

---

## 4. Requisitos previos

| Requisito | Detalle |
|-----------|---------|
| Python | 3.11 o superior |
| pip / venv | Gestión de entorno virtual |
| Cuenta Meta Developer | [developers.facebook.com](https://developers.facebook.com) |
| Cuenta Google AI Studio | [aistudio.google.com](https://aistudio.google.com) |
| ngrok o Cloudflare Tunnel | Exponer webhook local |
| Editor de código | VS Code, Cursor, etc. |
| WhatsApp en móvil | Para probar con número de test |

---

## 5. Estructura del proyecto

```
chatbot/
├── PROYECTO.md                 # Este documento
├── README.md                   # Instrucciones rápidas de ejecución
├── .env                        # Credenciales (NO commitear)
├── .env.example                # Plantilla de variables
├── .gitignore
├── requirements.txt
├── main.py                     # App FastAPI + webhook
├── config.py                   # Carga de settings desde .env
├── database/
│   ├── __init__.py
│   ├── db.py                   # Conexión SQLite
│   ├── models.py               # Esquema de tablas
│   └── seed.py                 # Datos de prueba
├── services/
│   ├── __init__.py
│   ├── whatsapp.py             # Envío/recepción mensajes Meta
│   ├── gemini_service.py       # Cliente Gemini + function calling
│   └── session.py              # Historial conversacional en memoria
├── tools/
│   ├── __init__.py
│   ├── reservas.py             # buscar, cancelar
│   ├── acceso.py               # código check-in
│   ├── limpieza.py             # estado housekeeping
│   └── costos.py               # consulta staff
├── prompts/
│   └── system.txt              # System prompt del hotel
└── tests/
    └── test_tools.py           # Tests unitarios de reglas
```

---

## 6. Fases de desarrollo

---

### Fase 0 — Preparación del entorno

**Objetivo:** Tener Python, entorno virtual y herramientas listas.

#### Pasos

1. **Verificar Python:**
   ```bash
   python3 --version   # Debe ser >= 3.11
   ```

2. **Crear y activar entorno virtual:**
   ```bash
   cd /home/usuario/Programm/chatbot
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Crear `.gitignore`:**
   ```
   .venv/
   .env
   __pycache__/
   *.pyc
   *.db
   .pytest_cache/
   ```

4. **Instalar ngrok** (o Cloudflare Tunnel):
   - ngrok: [ngrok.com/download](https://ngrok.com/download)
   - Registrarse para obtener authtoken gratuito.

#### Criterio de éxito

- [ ] `python3 --version` muestra 3.11+
- [ ] Entorno virtual activo (`(.venv)` en el prompt)
- [ ] ngrok instalado y autenticado

---

### Fase 1 — Cuentas y credenciales

**Objetivo:** Obtener todas las API keys y tokens necesarios.

#### 1.1 Meta Developer — WhatsApp Cloud API

1. Ir a [developers.facebook.com](https://developers.facebook.com) → **My Apps** → **Create App**.
2. Tipo: **Business** → Nombre: `Hotel Bot Prototype`.
3. En el panel de la app → **Add Product** → **WhatsApp** → **Set up**.
4. Ir a **WhatsApp → API Setup** y anotar:
   - **Temporary access token** (caduca; renovar en desarrollo)
   - **Phone number ID**
   - **WhatsApp Business Account ID**
5. En **To**, añadir tu número personal como **test recipient**.
6. Enviar un mensaje de prueba desde el panel para verificar.

#### 1.2 Google AI Studio — Gemini API

1. Ir a [aistudio.google.com](https://aistudio.google.com).
2. **Get API Key** → Crear clave para el proyecto.
3. Anotar la clave. Usar modelo **`gemini-2.5-flash`** (o el Flash disponible en free tier).

#### 1.3 Archivo `.env`

Crear `.env` en la raíz del proyecto:

```env
# WhatsApp Cloud API
WHATSAPP_TOKEN=tu_token_temporal_meta
WHATSAPP_PHONE_ID=tu_phone_number_id
WHATSAPP_API_VERSION=v21.0

# Webhook verification
VERIFY_TOKEN=mi_token_secreto_prototipo_123

# Gemini
GEMINI_API_KEY=tu_api_key_google
GEMINI_MODEL=gemini-2.5-flash

# App
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

Crear también `.env.example` con las mismas claves pero valores vacíos (para documentar sin exponer secretos).

#### Criterio de éxito

- [ ] Mensaje de prueba enviado desde Meta Dashboard
- [ ] API key de Gemini generada
- [ ] `.env` creado y en `.gitignore`

---

### Fase 2 — Scaffold del backend FastAPI

**Objetivo:** Servidor FastAPI mínimo que arranca y responde.

#### Pasos

1. **Crear `requirements.txt`:**
   ```
   fastapi>=0.115.0
   uvicorn[standard]>=0.32.0
   httpx>=0.27.0
   python-dotenv>=1.0.0
   google-genai>=1.0.0
   pydantic-settings>=2.0.0
   pytest>=8.0.0
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Crear `config.py`:**
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       whatsapp_token: str
       whatsapp_phone_id: str
       whatsapp_api_version: str = "v21.0"
       verify_token: str
       gemini_api_key: str
       gemini_model: str = "gemini-2.5-flash"
       app_host: str = "0.0.0.0"
       app_port: int = 8000
       debug: bool = True

       class Config:
           env_file = ".env"

   settings = Settings()
   ```

4. **Crear `main.py` inicial:**
   ```python
   from fastapi import FastAPI

   app = FastAPI(title="Hotel WhatsApp Bot", version="0.1.0")

   @app.get("/health")
   def health():
       return {"status": "ok"}
   ```

5. **Arrancar servidor:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verificar:** Abrir `http://localhost:8000/health` → debe devolver `{"status":"ok"}`.

#### Criterio de éxito

- [ ] Servidor arranca sin errores
- [ ] `/health` responde 200
- [ ] Swagger disponible en `/docs`

---

### Fase 3 — Webhook de WhatsApp

**Objetivo:** Recibir mensajes de WhatsApp y responder con eco.

#### Pasos

1. **Crear `services/whatsapp.py`:**
   - Función `send_text_message(to: str, text: str)` que hace POST a:
     ```
     https://graph.facebook.com/{version}/{phone_id}/messages
     ```
   - Headers: `Authorization: Bearer {WHATSAPP_TOKEN}`
   - Body:
     ```json
     {
       "messaging_product": "whatsapp",
       "to": "34600123456",
       "type": "text",
       "text": {"body": "Hola, soy el bot del hotel"}
     }
     ```

2. **Añadir endpoints webhook en `main.py`:**
   ```python
   from fastapi import FastAPI, Request, Query, HTTPException
   from config import settings
   from services.whatsapp import send_text_message

   @app.get("/webhook")
   def verify_webhook(
       hub_mode: str = Query(None, alias="hub.mode"),
       hub_verify_token: str = Query(None, alias="hub.verify_token"),
       hub_challenge: str = Query(None, alias="hub.challenge"),
   ):
       if hub_mode == "subscribe" and hub_verify_token == settings.verify_token:
           return int(hub_challenge)
       raise HTTPException(status_code=403, detail="Verification failed")

   @app.post("/webhook")
   async def receive_webhook(request: Request):
       body = await request.json()
       # Procesar mensajes entrantes (ver abajo)
       return {"status": "received"}
   ```

3. **Parsear mensajes entrantes:**
   ```python
   def extract_message(body: dict) -> dict | None:
       try:
           entry = body["entry"][0]
           change = entry["changes"][0]["value"]
           if "messages" not in change:
               return None
           msg = change["messages"][0]
           return {
               "from": msg["from"],
               "text": msg.get("text", {}).get("body", ""),
               "message_id": msg["id"],
               "timestamp": msg["timestamp"],
           }
       except (KeyError, IndexError):
           return None
   ```

4. **Implementar eco (temporal):**
   En el `POST /webhook`, si hay mensaje de texto:
   ```python
   send_text_message(msg["from"], f"Recibido: {msg['text']}")
   ```

5. **Exponer con ngrok:**
   ```bash
   ngrok http 8000
   ```
   Copiar URL HTTPS (ej. `https://abc123.ngrok-free.app`).

6. **Configurar webhook en Meta:**
   - App Dashboard → WhatsApp → Configuration
   - Callback URL: `https://abc123.ngrok-free.app/webhook`
   - Verify token: valor de `VERIFY_TOKEN` en `.env`
   - Click **Verify and Save**
   - Suscribir campo **messages**

7. **Probar:** Enviar "Hola" desde tu WhatsApp al número de test → debe responder "Recibido: Hola".

#### Criterio de éxito

- [ ] Webhook verificado en Meta (check verde)
- [ ] Mensaje entrante genera respuesta automática
- [ ] Logs en consola muestran el JSON recibido

---

### Fase 4 — Base de datos SQLite

**Objetivo:** Persistir reservas, huéspedes y habitaciones de prueba.

#### Pasos

1. **Crear `database/db.py`:**
   ```python
   import sqlite3
   from pathlib import Path

   DB_PATH = Path(__file__).parent.parent / "hotel.db"

   def get_connection():
       conn = sqlite3.connect(DB_PATH)
       conn.row_factory = sqlite3.Row
       return conn
   ```

2. **Crear `database/models.py`** con SQL de tablas:

   ```sql
   -- huéspedes
   CREATE TABLE IF NOT EXISTS huespedes (
       id INTEGER PRIMARY KEY,
       telefono TEXT UNIQUE NOT NULL,
       nombre TEXT NOT NULL,
       documento TEXT
   );

   -- habitaciones
   CREATE TABLE IF NOT EXISTS habitaciones (
       id INTEGER PRIMARY KEY,
       numero TEXT UNIQUE NOT NULL,
       tipo TEXT,
       estado_limpieza TEXT DEFAULT 'limpia',  -- limpia|sucia|en_proceso|mantenimiento
       costo_operativo_dia REAL DEFAULT 25.0
   );

   -- reservas
   CREATE TABLE IF NOT EXISTS reservas (
       id INTEGER PRIMARY KEY,
       huesped_id INTEGER NOT NULL,
       habitacion_id INTEGER NOT NULL,
       check_in TEXT NOT NULL,       -- ISO date: 2026-09-15
       check_out TEXT NOT NULL,
       politica TEXT NOT NULL,       -- flexible|moderada|no_reembolsable
       estado TEXT DEFAULT 'confirmada',  -- confirmada|check-in|cancelada|check-out
       importe_total REAL NOT NULL,
       codigo_acceso TEXT,
       hora_llegada TEXT,
       FOREIGN KEY (huesped_id) REFERENCES huespedes(id),
       FOREIGN KEY (habitacion_id) REFERENCES habitaciones(id)
   );
   ```

3. **Crear `database/seed.py`** con datos demo:

   | Huésped | Teléfono | Habitación | Política | Check-in |
   |---------|----------|------------|----------|----------|
   | Juan Pérez | TU_NUMERO_WA | 305 | moderada | +3 días |
   | Ana García | 34600999888 | 412 | flexible | +1 día |
   | Carlos López | 34600777666 | 201 | no_reembolsable | +7 días |

   > **Importante:** Sustituir `TU_NUMERO_WA` por tu número real (sin +, ej. `34600123456`).

4. **Ejecutar seed:**
   ```bash
   python -m database.seed
   ```

5. **Verificar:**
   ```bash
   sqlite3 hotel.db "SELECT * FROM reservas;"
   ```

#### Criterio de éxito

- [ ] Tablas creadas en `hotel.db`
- [ ] Al menos 3 reservas de prueba insertadas
- [ ] Tu número asociado a una reserva activa

---

### Fase 5 — Integración con Gemini

**Objetivo:** Enviar mensajes del huésped a Gemini y obtener respuestas contextuales.

#### Pasos

1. **Crear `prompts/system.txt`:**
   ```
   Eres el asistente virtual del Hotel Paraíso. Respondes por WhatsApp en español.
   Tono: amable, conciso, profesional. Máximo 3 párrafos cortos por respuesta.

   INFORMACIÓN DEL HOTEL:
   - Recepción: 24 horas
   - Desayuno: 7:00 - 10:30 (restaurante planta baja)
   - WiFi: red "HotelParaiso" / clave "bienvenido2026"
   - Parking: subterráneo, 15€/día
   - Check-in: 15:00 | Check-out: 12:00

   REGLAS OBLIGATORIAS:
   1. NUNCA inventes datos de reservas, códigos de acceso ni importes.
   2. Para consultar reservas, cancelar, check-in o limpieza, USA las herramientas disponibles.
   3. Antes de cancelar, SIEMPRE calcula y muestra la penalización al huésped.
   4. Si el huésped tiene una queja grave o pide hablar con una persona, responde que
      "Un agente de recepción le contactará en breve" y usa la herramienta escalar_recepcion.
   5. Solo responde sobre temas del hotel. Para otros temas, indica amablemente que no puedes ayudar.

   POLÍTICAS DE CANCELACIÓN:
   - flexible: cancelación gratuita hasta 24h antes del check-in
   - moderada: cancelación gratuita hasta 72h antes; después, penalización del 50%
   - no_reembolsable: penalización del 100% en cualquier momento
   ```

2. **Crear `services/session.py`:**
   - Diccionario en memoria: `{telefono: [{"role": "user"|"model", "text": "..."}]}`.
   - Función `add_message(phone, role, text)`.
   - Función `get_history(phone, limit=10)`.
   - Función `clear_session(phone)` (opcional, comando "reiniciar").

3. **Crear `services/gemini_service.py`:**
   ```python
   from google import genai
   from config import settings

   client = genai.Client(api_key=settings.gemini_api_key)

   def chat_with_tools(message: str, history: list, tools: list) -> dict:
       system_prompt = open("prompts/system.txt").read()
       # Construir contents con historial
       # Llamar client.models.generate_content con tools
       # Retornar {"text": "...", "tool_calls": [...]} o solo text
       ...
   ```

4. **Conectar en webhook:**
   - Recibir mensaje → `add_message(phone, "user", text)`
   - Llamar `chat_with_tools(text, get_history(phone), TOOLS_DEFINITIONS)`
   - Si hay tool call → ejecutar tool → reenviar resultado a Gemini → respuesta final
   - `add_message(phone, "model", respuesta)`
   - `send_text_message(phone, respuesta)`

5. **Probar sin tools primero:**
   Preguntar "¿A qué hora es el desayuno?" → debe responder con datos del prompt.

#### Criterio de éxito

- [ ] Gemini responde preguntas del hotel usando el system prompt
- [ ] Historial de conversación se mantiene entre mensajes
- [ ] Respuestas en español, tono adecuado

---

### Fase 6 — Tools (reglas de negocio)

**Objetivo:** Implementar acciones deterministas que Gemini invoca vía function calling.

#### Tools a implementar

| Tool | Archivo | Descripción |
|------|---------|-------------|
| `buscar_reserva` | `tools/reservas.py` | Busca reserva activa por teléfono |
| `calcular_penalizacion` | `tools/reservas.py` | Calcula cargo según política y fecha |
| `confirmar_cancelacion` | `tools/reservas.py` | Marca reserva como cancelada |
| `generar_codigo_acceso` | `tools/acceso.py` | Genera código 6 dígitos para habitación |
| `registrar_llegada` | `tools/reservas.py` | Guarda hora estimada de llegada |
| `consultar_limpieza` | `tools/limpieza.py` | Estado y horario de limpieza |
| `consultar_costo_habitacion` | `tools/costos.py` | Coste operativo (solo staff) |
| `escalar_recepcion` | `tools/reservas.py` | Marca conversación para atención humana |

#### 6.1 `tools/reservas.py` — Ejemplo de lógica de penalización

```python
from datetime import datetime, timedelta

POLITICAS = {
    "flexible": {"dias_min": 1, "porcentaje": 0},
    "moderada": {"dias_min": 3, "porcentaje": 50},
    "no_reembolsable": {"dias_min": 999, "porcentaje": 100},
}

def calcular_penalizacion(reserva_id: int) -> dict:
    reserva = get_reserva_by_id(reserva_id)
    check_in = datetime.fromisoformat(reserva["check_in"])
    dias_restantes = (check_in - datetime.now()).days
    politica = POLITICAS[reserva["politica"]]

    if dias_restantes >= politica["dias_min"]:
        return {"penalizacion": 0, "mensaje": "Cancelación gratuita"}
    
    importe = reserva["importe_total"] * politica["porcentaje"] / 100
    return {
        "penalizacion": importe,
        "porcentaje": politica["porcentaje"],
        "mensaje": f"Penalización del {politica['porcentaje']}%: {importe:.2f}€"
    }
```

#### 6.2 Definición de tools para Gemini

En `services/gemini_service.py`, declarar tools con JSON Schema:

```python
TOOLS = [
    {
        "name": "buscar_reserva",
        "description": "Busca la reserva activa de un huésped por su teléfono",
        "parameters": {
            "type": "object",
            "properties": {
                "telefono": {"type": "string", "description": "Teléfono WhatsApp del huésped"}
            },
            "required": ["telefono"]
        }
    },
    {
        "name": "calcular_penalizacion",
        "description": "Calcula la penalización por cancelación según la política de la reserva",
        "parameters": {
            "type": "object",
            "properties": {
                "reserva_id": {"type": "integer"}
            },
            "required": ["reserva_id"]
        }
    },
    # ... resto de tools
]
```

#### 6.3 Mapa de ejecución

```python
TOOL_HANDLERS = {
    "buscar_reserva": buscar_reserva,
    "calcular_penalizacion": calcular_penalizacion,
    "confirmar_cancelacion": confirmar_cancelacion,
    "generar_codigo_acceso": generar_codigo_acceso,
    "registrar_llegada": registrar_llegada,
    "consultar_limpieza": consultar_limpieza,
    "consultar_costo_habitacion": consultar_costo_habitacion,
    "escalar_recepcion": escalar_recepcion,
}
```

#### Criterio de éxito

- [ ] Cada tool funciona de forma independiente (probar con script o pytest)
- [ ] Gemini invoca tools correctamente según intención del huésped
- [ ] Penalizaciones calculadas según política, no inventadas por la IA

---

### Fase 7 — Orquestador conversacional

**Objetivo:** Unir webhook + sesión + Gemini + tools en un flujo coherente.

#### Pasos

1. **Crear función principal `process_message(phone, text)` en `main.py` o módulo dedicado:**

   ```
   1. Guardar mensaje en sesión
   2. Enviar a Gemini con historial + tools
   3. SI Gemini devuelve tool_call:
      a. Ejecutar handler correspondiente
      b. Enviar resultado de vuelta a Gemini
      c. Obtener respuesta final en lenguaje natural
   4. Guardar respuesta en sesión
   5. Enviar respuesta por WhatsApp
   ```

2. **Manejar confirmaciones:**
   - Para cancelaciones, Gemini debe preguntar "¿Confirma la cancelación con penalización de X€?"
   - Solo ejecutar `confirmar_cancelacion` si el huésped confirma explícitamente.

3. **Comando especial `reiniciar`:**
   - Si el huésped escribe "reiniciar" → limpiar sesión y saludar de nuevo.

4. **Logging básico:**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger.info(f"Mensaje de {phone}: {text}")
   logger.info(f"Tool ejecutada: {tool_name} → {result}")
   ```

5. **Manejo de errores:**
   - Si Gemini falla (429 rate limit) → "Disculpe, estoy experimentando alta demanda. Intente en unos segundos."
   - Si tool falla → "Ha ocurrido un error procesando su solicitud. Contacte recepción."

#### Criterio de éxito

- [ ] Flujo completo funciona de punta a punta
- [ ] Cancelación requiere confirmación explícita
- [ ] Errores no crashean el servidor

---

### Fase 8 — Pruebas de escenarios

**Objetivo:** Validar todos los flujos del prototipo desde WhatsApp.

#### Checklist de pruebas

| # | Escenario | Mensaje de prueba | Resultado esperado |
|---|-----------|-------------------|-------------------|
| 1 | Saludo | "Hola" | Saludo + menú de ayuda |
| 2 | Consulta reserva | "¿Tengo reserva?" | Datos de reserva (habitación, fechas) |
| 3 | Check-in | "Quiero hacer check-in" | Código de acceso de 6 dígitos |
| 4 | Cancelación gratis | Reserva flexible, >24h antes | "Cancelación gratuita" + confirmación |
| 5 | Cancelación con penalización | Reserva moderada, <72h | Muestra importe penalización |
| 6 | Confirmar cancelación | "Sí, confirmo la cancelación" | Reserva marcada cancelada |
| 7 | Llegada | "Llegaré sobre las 18:00" | Hora registrada + confirmación |
| 8 | Limpieza | "¿Cuándo limpian mi habitación?" | Estado + horario estimado |
| 9 | FAQ | "¿Hay parking?" | Info parking del prompt |
| 10 | Escalado | "Quiero hablar con una persona" | Mensaje de escalado a recepción |
| 11 | Sin reserva | Número no registrado | "No encontramos reserva activa" |
| 12 | Reiniciar | "reiniciar" | Sesión limpia, saludo inicial |

#### Tests unitarios (`tests/test_tools.py`)

```bash
pytest tests/ -v
```

Probar al menos:
- `calcular_penalizacion` con cada política
- `generar_codigo_acceso` devuelve 6 dígitos
- `buscar_reserva` con teléfono existente e inexistente

#### Criterio de éxito

- [ ] 10/12 escenarios pasan correctamente
- [ ] Tests unitarios en verde
- [ ] No hay regresiones en conversaciones previas

---

### Fase 9 — Demo y cierre del prototipo

**Objetivo:** Preparar una demostración reproducible del prototipo.

#### Pasos

1. **Crear `README.md`** con:
   - Cómo instalar y ejecutar
   - Cómo configurar `.env`
   - Cómo arrancar ngrok + servidor
   - Números/datos de prueba

2. **Script de arranque rápido** (`run.sh`):
   ```bash
   #!/bin/bash
   source .venv/bin/activate
   python -m database.seed   # re-seed si necesario
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Preparar guion de demo (5 minutos):**
   - Min 0–1: Huésped saluda y consulta reserva
   - Min 1–2: Check-in con código de acceso
   - Min 2–3: Pregunta FAQ (desayuno/parking)
   - Min 3–4: Cancelación con penalización
   - Min 4–5: Escalado a recepción

4. **Documentar limitaciones** en README (ver sección 9 de este doc).

5. **Backup:**
   - Exportar `hotel.db`
   - Guardar `.env` de forma segura (fuera del repo)

#### Criterio de éxito

- [ ] Demo ejecutable en < 2 minutos de setup
- [ ] README claro para otro desarrollador
- [ ] Guion de demo probado al menos una vez

---

## 7. Variables de entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `WHATSAPP_TOKEN` | Token de acceso Meta (temporal en dev) | `EAAxxxxx...` |
| `WHATSAPP_PHONE_ID` | ID del número de teléfono WhatsApp | `1234567890` |
| `WHATSAPP_API_VERSION` | Versión Graph API | `v21.0` |
| `VERIFY_TOKEN` | Token secreto para verificar webhook | `mi_token_secreto_123` |
| `GEMINI_API_KEY` | API key de Google AI Studio | `AIzaSy...` |
| `GEMINI_MODEL` | Modelo Gemini a usar | `gemini-2.5-flash` |
| `APP_HOST` | Host del servidor | `0.0.0.0` |
| `APP_PORT` | Puerto del servidor | `8000` |
| `DEBUG` | Modo debug | `true` |

---

## 8. Costes del prototipo

| Recurso | Coste |
|---------|-------|
| Gemini Flash (free tier) | €0 |
| WhatsApp Cloud API (test) | €0 |
| ngrok (free) | €0 |
| SQLite | €0 |
| Hosting local | €0 |
| **Total** | **€0** |

---

## 9. Limitaciones conocidas

- **Token WhatsApp temporal:** Caduca cada 24h en modo desarrollo; hay que renovarlo manualmente.
- **ngrok free:** URL cambia en cada reinicio; hay que reconfigurar webhook en Meta.
- **Gemini free tier:** Límites de requests/día; puede fallar en pruebas intensivas.
- **Sesiones en memoria:** Se pierden al reiniciar el servidor.
- **Sin autenticación staff:** Cualquiera puede preguntar por costos si conoce el comando.
- **Sin pagos reales:** Las penalizaciones se calculan pero no se cobran.
- **Un solo número de test:** Solo los números registrados en Meta pueden interactuar.

---

## 10. Roadmap sugerido (4 días)

| Día | Fases | Entregable |
|-----|-------|------------|
| **Día 1** | Fase 0 + 1 + 2 + 3 | Webhook funcional con eco de mensajes |
| **Día 2** | Fase 4 + 5 | Gemini responde FAQs con datos del hotel |
| **Día 3** | Fase 6 + 7 | Tools operativas, flujos de reserva/cancelación/check-in |
| **Día 4** | Fase 8 + 9 | Pruebas completas, README, demo lista |

---

## 11. Referencias

- [WhatsApp Cloud API — Get Started](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [WhatsApp Cloud API — Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks)
- [WhatsApp Cloud API — Send Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages)
- [WhatsApp Pricing](https://developers.facebook.com/docs/whatsapp/pricing/)
- [Google Gemini API — Python SDK](https://ai.google.dev/gemini-api/docs/quickstart?lang=python)
- [Google Gemini — Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ngrok — Download](https://ngrok.com/download)

---

*Documento generado para el prototipo Hotel WhatsApp Bot — FastAPI + Gemini + SQLite.*
