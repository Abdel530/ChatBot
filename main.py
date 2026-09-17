from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse

from config import settings
from services.whatsapp_service import (
    send_whatsapp_message,
    send_interactive_buttons,
    send_interactive_list,
    send_interactive_list_custom,
    format_whatsapp_message,
)
from services.session import add_message, get_history, clear_session
from services.gemini_service import chat_with_tools_and_session, TOOLS, TOOL_HANDLERS, execute_tool, register_tool, process_message
from tools.reservas import (
    buscar_reserva,
    calcular_penalizacion,
    confirmar_cancelacion,
    registrar_llegada,
    escalar_recepcion,
)
from tools.acceso import generar_codigo_acceso
from tools.limpieza import consultar_limpieza
from tools.costos import consultar_costo_habitacion
from google.genai.types import FunctionDeclaration

app = FastAPI(title="Hotel WhatsApp Bot", version="0.2.0")

WELCOME_TEXT = "¡Bienvenido al Hotel Paraíso! ¿En qué puedo ayudarte?"


def _setup_tools():
    register_tool("buscar_reserva", buscar_reserva, FunctionDeclaration(
        name="buscar_reserva",
        description="Busca la reserva activa de un huésped por su teléfono",
        parameters={
            "type": "object",
            "properties": {"telefono": {"type": "string"}},
            "required": ["telefono"],
        },
    ))
    register_tool("calcular_penalizacion", calcular_penalizacion, FunctionDeclaration(
        name="calcular_penalizacion",
        description="Calcula la penalización por cancelación según la política de la reserva",
        parameters={
            "type": "object",
            "properties": {"reserva_id": {"type": "integer"}},
            "required": ["reserva_id"],
        },
    ))
    register_tool("confirmar_cancelacion", confirmar_cancelacion, FunctionDeclaration(
        name="confirmar_cancelacion",
        description="Confirma la cancelación de una reserva",
        parameters={
            "type": "object",
            "properties": {"reserva_id": {"type": "integer"}},
            "required": ["reserva_id"],
        },
    ))
    register_tool("generar_codigo_acceso", generar_codigo_acceso, FunctionDeclaration(
        name="generar_codigo_acceso",
        description="Genera un código de acceso de 6 dígitos para una habitación",
        parameters={
            "type": "object",
            "properties": {"habitacion_id": {"type": "integer"}},
            "required": ["habitacion_id"],
        },
    ))
    register_tool("registrar_llegada", registrar_llegada, FunctionDeclaration(
        name="registrar_llegada",
        description="Registra la hora estimada de llegada del huésped",
        parameters={
            "type": "object",
            "properties": {"reserva_id": {"type": "integer"}, "hora_llegada": {"type": "string"}},
            "required": ["reserva_id", "hora_llegada"],
        },
    ))
    register_tool("consultar_limpieza", consultar_limpieza, FunctionDeclaration(
        name="consultar_limpieza",
        description="Consulta el estado de limpieza de una habitación",
        parameters={
            "type": "object",
            "properties": {"habitacion_id": {"type": "integer"}},
            "required": ["habitacion_id"],
        },
    ))
    register_tool("consultar_costo_habitacion", consultar_costo_habitacion, FunctionDeclaration(
        name="consultar_costo_habitacion",
        description="Consulta el coste operativo de una habitación (solo staff)",
        parameters={
            "type": "object",
            "properties": {"habitacion_id": {"type": "integer"}},
            "required": ["habitacion_id"],
        },
    ))
    register_tool("escalar_recepcion", escalar_recepcion, FunctionDeclaration(
        name="escalar_recepcion",
        description="Escalona la conversación a recepción humana",
        parameters={
            "type": "object",
            "properties": {"telefono": {"type": "string"}, "mensaje": {"type": "string"}},
            "required": ["telefono", "mensaje"],
        },
    ))


_setup_tools()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.verify_token:
        return PlainTextResponse(content=hub_challenge, status_code=200)
    return PlainTextResponse(content="OK", status_code=200)


@app.post("/webhook")
async def receive_webhook(request: Request):
    print(f"[POST /webhook] Petición recibida - 200 OK")
    try:
        body = await request.json()
        print(f"[POST /webhook] Body recibido: {body}", flush=True)
    except Exception:
        print(f"[POST /webhook] Cuerpo inválido - 200 OK")
        return {"status": "ok"}

    try:
        msg = extract_message(body)

        if not msg:
            return {"status": "ok"}

        phone = msg["from"]
        message_type = msg.get("type", "text")
        text = msg.get("text") or ""
        selected_id = msg.get("selected_id")

        if message_type == "interactive" and selected_id:
            await _handle_interactive(phone, selected_id)
            print(f"[POST /webhook] {phone}: interactive event - {selected_id} - 200 OK")
            return {"status": "ok"}

        text_lower = text.strip().lower()
        if text_lower in ("hola", "buenas", "menu", "opciones", "seleccion simple", "selección simple", "menú"):
            try:
                await send_interactive_list(phone)
                print(f"[POST /webhook] {phone}: menú interactivo enviado - 200 OK")
            except Exception as e:
                print(f"[POST /webhook] {phone}: Error al enviar menú interactivo: {e}")
            return {"status": "ok"}

        add_message(phone, "user", text)

        if text.strip().lower() == "reiniciar":
            clear_session(phone)
            await send_whatsapp_message(phone, "¡Hola! Soy el asistente del Hotel Paraíso. En qué puedo ayudarte?")
            print(f"[POST /webhook] {phone}: reiniciado - 200 OK")
            return {"status": "ok"}

        result = chat_with_tools_and_session(text, phone, tools=TOOLS)

        response_text = result.get("text", "")
        tool_calls = result.get("tool_calls", [])

        if tool_calls:
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_result = execute_tool(tool_name, tool_args)
                add_message(phone, "tool", f"{tool_name}: {tool_result}")

                gemini_result = chat_with_tools_and_session(
                    f"El resultado de la herramienta {tool_name} es: {tool_result}. Responde al huésped de forma natural.",
                    phone, tools=TOOLS,
                )
                response_text = gemini_result.get("text", tool_result)

        add_message(phone, "model", response_text)
        await send_whatsapp_message(phone, response_text)

        print(f"[WEBHOOK] {phone}: {text}")
        print(f"[WEBHOOK] Response: {response_text[:100]}")

    except Exception as e:
        print(f"Error procesando mensaje: {e}", flush=True)
        import traceback
        traceback.print_exc()

    print(f"[POST /webhook] Procesado - 200 OK")
    return {"status": "ok"}


async def _send_welcome_buttons(phone: str):
    """Envía los botones de bienvenida al usuario."""
    buttons = [
        {"id": "btn_habitaciones", "title": "Ver Habitaciones"},
        {"id": "btn_servicios", "title": "Servicios"},
        {"id": "btn_contacto", "title": "Contacto"},
    ]
    await send_interactive_buttons(phone, WELCOME_TEXT, buttons)


async def _handle_interactive(phone: str, selected_id: str):
    """Maneja los eventos interactivos (botones presionados o listas seleccionadas)."""
    if selected_id == "btn_habitaciones":
        sections = [
            {
                "title": "Tipos de Habitación",
                "rows": [
                    {"id": "habitacion_sencilla", "title": "Habitación Sencilla", "description": "Habitación individual con cama queen size"},
                    {"id": "habitacion_doble", "title": "Habitación Doble", "description": "Habitación doble con camas twin o cama king"},
                    {"id": "habitacion_suite", "title": "Suite", "description": "Suite premium con sala de estar y vista al mar"},
                ],
            },
        ]
        await send_interactive_list_custom(
            phone,
            "Selecciona el tipo de habitación que deseas:",
            "Ver Habitaciones",
            sections,
        )
    elif selected_id == "btn_servicios":
        await send_whatsapp_message(
            phone,
            "Nuestros servicios incluyen: recepción 24h, limpieza diaria, restaurante, piscina, spa y estacionamiento. ¡Contáctanos para más detalles!",
        )
    elif selected_id == "btn_contacto":
        await send_whatsapp_message(
            phone,
            "Puedes contactarnos al teléfono +52 123 456 7890 o por email a recepcion@hotelparaiso.com",
        )
    elif selected_id == "opt_reserva":
        await send_whatsapp_message(
            phone,
            "Para consultar tu reserva, por favor proporciona tu número de reserva o teléfono asociado.",
        )
    elif selected_id == "opt_checkin":
        await send_whatsapp_message(
            phone,
            "Para registrar tu hora de llegada, indícanos tu número de reserva y la hora estimada de llegada.",
        )
    elif selected_id == "opt_servicios":
        await send_whatsapp_message(
            phone,
            "Nuestros servicios incluyen: WiFi gratuito, desayuno incluido, parking seguro, y horarios de piscina y spa. ¡Contáctanos para más detalles!",
        )
    elif selected_id == "opt_cancelar":
        await send_whatsapp_message(
            phone,
            "Para calcular la penalización por cancelación, por favor proporciona tu número de reserva.",
        )
    elif selected_id == "opt_recepcion":
        await send_whatsapp_message(
            phone,
            "Serás conectado con recepción para atención personalizada. Por favor espera un momento.",
        )
    elif selected_id.startswith("habitacion_"):
        habitacion_tipo = selected_id.replace("habitacion_", "").capitalize()
        await send_whatsapp_message(
            phone,
            f"Hemso recibido interés en la habitación {habitacion_tipo}. Un asesor se pondrá en contacto contigo brevemente.",
        )
    else:
        await send_whatsapp_message(
            phone,
            f"Opción seleccionada: {selected_id}. Gracias por tu interés.",
        )


def extract_message(body: dict) -> dict | None:
    try:
        entry = body["entry"][0]
        change = entry["changes"][0]["value"]
        if "messages" not in change:
            return None
        msg = change["messages"][0]
        msg_type = msg.get("type", "text")
        text = ""
        selected_id = None

        if msg_type == "text":
            text_field = msg.get("text")
            text = text_field.get("body", "") if isinstance(text_field, dict) else ""
        elif msg_type == "interactive":
            interactive = msg.get("interactive", {})
            if "button_reply" in interactive:
                selected_id = interactive["button_reply"].get("id")
            elif "list_reply" in interactive:
                selected_id = interactive["list_reply"].get("id")

        return {
            "from": msg["from"],
            "text": text,
            "selected_id": selected_id,
            "type": msg_type,
            "message_id": msg["id"],
            "timestamp": msg["timestamp"],
        }
    except (KeyError, IndexError, AttributeError):
        return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)

    