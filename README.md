# Chatbot Hotelero — Prototipo WhatsApp + Gemini + FastAPI

## Instalación rápida

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Variables de entorno

Copiar `.env.example` a `.env` y rellenar con sus credenciales:

```bash
copy .env.example .env
```

## Ejecutar

```bash
.\.venv\Scripts\python main.py
```

o con uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /health` — Estado del servidor
- `GET /docs` — Documentación Swagger
- `GET /webhook` — Verificación de webhook de WhatsApp
- `POST /webhook` — Recepción de mensajes de WhatsApp

## Webhook

```bash
ngrok http 8000
```

Configurar `https://<tu-url>.ngrok-free.app/webhook` en el panel de Meta (callback URL y verify token).

## Tests

```bash
pytest tests/ -v
```

## Estructura

```
chatbot/
├── PROYECTO.md                 # Documento de diseño
├── README.md                   # Este archivo
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
│   └── session.py              # Historial conversacional
├── tools/
│   ├── __init__.py
│   ├── reservas.py             # buscar, cancelar
│   ├── acceso.py               # código check-in
│   ├── limpieza.py             # estado housekeeping
│   └── costos.py               # consulta staff
├── prompts/
│   └── system.txt              # System prompt del hotel
└── tests/
    └── __init__.py
    └── test_tools.py           # Tests unitarios
```

## Créditos

Prototipo desarrollado con:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs/quickstart?lang=python)
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [SQLite](https://www.sqlite.org/)