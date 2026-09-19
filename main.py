import re
from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse

from config import settings
from services.whatsapp_service import (
    send_whatsapp_message,
    send_interactive_buttons,
    send_interactive_list,
    send_interactive_list_custom,
    format_whatsapp_message,
    send_room_type_list,
)
from services.session import (
    add_message, get_history, clear_session, get_pending_action, clear_pending_action,
    set_reservation_state, get_reservation_state, set_reservation_data, get_reservation_data,
    clear_reservation, clear_reservation_data,
    RESERVATION_STATE_IDLE, RESERVATION_STATE_SELECT_HABITACION, RESERVATION_STATE_FECHAS,
    RESERVATION_STATE_PERSONAL, RESERVATION_STATE_HORA_LLEGADA, RESERVATION_STATE_COMPLETE,
    PASO_PERSONAL_NAMES,
)
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
from tools.servicios import consultar_servicios
from tools.consulta_reserva import consultar_reserva
from tools.registro_llegada_db import registrar_llegada_db
from tools.cancelacion_db import cancelar_reserva_db
import re

from tools.nueva_reserva import (
    consultar_disponibilidad, registrar_reserva, upsert_huesped,
    ddmmyyyy_to_yyyymmdd, validar_hora_12h,
)
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
    register_tool("consultar_servicios", consultar_servicios, FunctionDeclaration(
        name="consultar_servicios",
        description="Consulta la lista de servicios del hotel con horarios y descripciones",
        parameters={"type": "object", "properties": {}, "required": []},
    ))
    register_tool("consultar_reserva", consultar_reserva, FunctionDeclaration(
        name="consultar_reserva",
        description="Consulta los detalles de una reserva por teléfono o ID de reserva",
        parameters={
            "type": "object",
            "properties": {"identificador": {"type": "string"}},
            "required": ["identificador"],
        },
    ))
    register_tool("registrar_llegada_db", registrar_llegada_db, FunctionDeclaration(
        name="registrar_llegada_db",
        description="Registra la hora de llegada de un huésped para una reserva",
        parameters={
            "type": "object",
            "properties": {"identificador": {"type": "string"}},
            "required": ["identificador"],
        },
    ))
    register_tool("cancelar_reserva_db", cancelar_reserva_db, FunctionDeclaration(
        name="cancelar_reserva_db",
        description="Cancela una reserva activa por número de reserva o teléfono",
        parameters={
            "type": "object",
            "properties": {"identificador": {"type": "string"}},
            "required": ["identificador"],
        },
    ))
    register_tool("consultar_disponibilidad", consultar_disponibilidad, FunctionDeclaration(
        name="consultar_disponibilidad",
        description="Consulta la disponibilidad de habitaciones por tipo para un rango de fechas",
        parameters={
            "type": "object",
            "properties": {"fecha_entrada": {"type": "string"}, "fecha_salida": {"type": "string"}},
            "required": ["fecha_entrada", "fecha_salida"],
        },
    ))
    register_tool("registrar_reserva", registrar_reserva, FunctionDeclaration(
        name="registrar_reserva",
        description="Registra una nueva reserva confirmada para un huésped",
        parameters={
            "type": "object",
            "properties": {
                "huesped_id": {"type": "integer"},
                "habitacion_id": {"type": "integer"},
                "check_in": {"type": "string"},
                "check_out": {"type": "string"},
                "politica": {"type": "string"},
                "importe_total": {"type": "number"},
            },
            "required": ["huesped_id", "habitacion_id", "check_in", "check_out", "politica", "importe_total"],
        },
    ))


_setup_tools()


@app.get("/health")
def health():
    return {"status": "ok"}


MENSAJE_CONTINGENCIA = (
    "⚠️ Ocurrió un problema inesperado. "
    "No te preocupes, puedes intentar de nuevo.\n\n"
    "Selecciona cualquier opción del menú para continuar:\n"
    "• Consultar mi reserva\n"
    "• Registrar hora de llegada\n"
    "• Información de servicios\n"
    "• Cancelar reserva\n"
    "• Hablar con recepción"
)


def _validar_telefono(telefono: str) -> bool:
    """Valida que el teléfono tenga un formato mínimo aceptable."""
    if not telefono or not isinstance(telefono, str):
        return False
    digitos = ''.join(c for c in telefono if c.isdigit())
    return len(digitos) >= 7


def _validar_id_entero(valor: str, nombre_campo: str = "ID") -> int | None:
    """Convierte y valida que un valor sea un entero positivo. Retorna None si es inválido."""
    try:
        resultado = int(str(valor).strip())
        if resultado > 0:
            return resultado
    except (ValueError, AttributeError):
        pass
    return None


def _validar_texto_entrada(texto: str, max_longitud: int = 200) -> str | None:
    """Valida que la entrada de texto no sea vacía ni exceda la longitud máxima."""
    if not texto or not isinstance(texto, str):
        return None
    texto = texto.strip()
    if not texto:
        return None
    if len(texto) > max_longitud:
        return None
    return texto


def _es_resultado_no_encontrado(texto: str) -> bool:
    """Detecta si el resultado de una consulta indica que no se encontraron registros."""
    if not isinstance(texto, str):
        return False
    texto_lower = texto.lower()
    return any(kw in texto_lower for kw in ["no se encontró", "no se pudo", "no fue posible"])


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
            try:
                await _handle_interactive(phone, selected_id)
            except Exception as e:
                print(f"[POST /webhook] {phone}: Error en _handle_interactive: {e}", flush=True)
                import traceback
                traceback.print_exc()
                try:
                    await send_whatsapp_message(phone, MENSAJE_CONTINGENCIA)
                except Exception:
                    pass
            print(f"[POST /webhook] {phone}: interactive event - {selected_id} - 200 OK")
            return {"status": "ok"}

        if not _validar_texto_entrada(text):
            await send_whatsapp_message(
                phone,
                "No pude leer tu mensaje. Por favor, envía tu consulta de nuevo o selecciona una opción del menú.",
            )
            return {"status": "ok"}

        text_lower = text.strip().lower()
        ESCAPE_KEYWORDS = {"cancelar", "salir", "reiniciar", "menu", "menú", "inicio", "hola"}
        if text_lower in ESCAPE_KEYWORDS:
            clear_session(phone)
            clear_pending_action(phone)
            print(f"[POST /webhook] {phone}: sesión reseteada por comando '{text_lower}'")
            try:
                await send_interactive_list(phone)
                print(f"[POST /webhook] {phone}: menú interactivo enviado tras reset - 200 OK")
            except Exception as e:
                print(f"ERROR META API: {str(e)}", flush=True)
                try:
                    fallback = (
                        "¡Hola! Bienvenido/a al Hotel Paraíso. 🌴\n¿En qué puedo ayudarte hoy?\n"
                        "📋 **Menú Principal:**\n"
                        "1. 🏨 Nueva reserva\n"
                        "2. 🔍 Consultar reserva\n"
                        "3. 📋 Registrar llegada\n"
                        "4. 🛎️ Servicios\n"
                        "5. ❌ Cancelar reserva\n"
                        "6. 📞 Hablar con recepción"
                    )
                    await send_whatsapp_message(phone, fallback)
                except Exception:
                    pass
            return {"status": "ok"}

        estado_reserva = get_reservation_state(phone)
        if estado_reserva != RESERVATION_STATE_IDLE:
            try:
                resultado = await _procesar_estado_reserva(text, phone)
                await send_whatsapp_message(phone, resultado)
            except Exception as e:
                print(f"[POST /webhook] {phone}: Error en estado de reserva: {e}", flush=True)
                try:
                    await send_whatsapp_message(phone, "Hubo un problema. Intenta de nuevo o selecciona el menú.")
                except Exception:
                    pass
            return {"status": "ok"}

        pending_action = get_pending_action(phone)
        if pending_action:
            clear_pending_action(phone)
            try:
                if pending_action == "consultar_reserva":
                    resultado = consultar_reserva(text)
                elif pending_action == "registrar_llegada":
                    resultado = registrar_llegada_db(text)
                elif pending_action == "cancelar_reserva":
                    resultado = cancelar_reserva_db(text)
                elif pending_action == "escalar_recepcion":
                    resultado = escalar_recepcion(phone, text)
                else:
                    resultado = f"No se reconoce la acción pendiente: {pending_action}"
                await send_whatsapp_message(phone, resultado)
            except Exception as e:
                print(f"[POST /webhook] {phone}: Error en acción pendiente: {e}", flush=True)
                try:
                    await send_whatsapp_message(phone, "Hubo un problema al procesar tu solicitud. Intenta de nuevo.")
                except Exception:
                    pass
            print(f"[POST /webhook] {phone}: acción pendiente '{pending_action}' completada - 200 OK")
            return {"status": "ok"}

        add_message(phone, "user", text)

        result = chat_with_tools_and_session(text, phone, tools=TOOLS)

        response_text = result.get("text", "")
        tool_calls = result.get("tool_calls", [])

        if tool_calls:
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                try:
                    tool_result = execute_tool(tool_name, tool_args)
                except Exception as e:
                    print(f"[POST /webhook] {phone}: Error ejecutando {tool_name}: {e}", flush=True)
                    tool_result = f"No fue posible procesar '{tool_name}'. Intenta de nuevo."
                add_message(phone, "tool", f"{tool_name}: {tool_result}")

                if isinstance(tool_result, str) and _es_resultado_no_encontrado(tool_result):
                    clear_session(phone)
                    print(f"[POST /webhook] {phone}: sesión reseteada por búsqueda sin resultados")
                    response_text = tool_result + "\n\nPuedes seleccionar cualquier opción del menú para reiniciar."
                    break

                if isinstance(tool_result, str) and tool_result.startswith("Error"):
                    clear_session(phone)
                    print(f"[POST /webhook] {phone}: sesión reseteada por error en herramienta")
                    response_text = tool_result + "\n\nPuedes seleccionar cualquier opción del menú para reiniciar."
                    break

                try:
                    gemini_result = chat_with_tools_and_session(
                        f"El resultado de la herramienta {tool_name} es: {tool_result}. Responde al huésped de forma natural.",
                        phone, tools=TOOLS,
                    )
                    response_text = gemini_result.get("text", tool_result)
                except Exception as e:
                    print(f"[POST /webhook] {phone}: Error en Gemini tras tool {tool_name}: {e}", flush=True)
                    response_text = "Ocurrió un problema al procesar tu solicitud. Intenta de nuevo o selecciona una opción del menú."
                    break

        add_message(phone, "model", response_text)
        await send_whatsapp_message(phone, response_text)

        print(f"[WEBHOOK] {phone}: {text}")
        print(f"[WEBHOOK] Response: {response_text[:100]}")

    except Exception as e:
        print(f"[POST /webhook] Error crítico procesando mensaje: {e}", flush=True)
        import traceback
        traceback.print_exc()
        try:
            phone = msg["from"] if msg else "desconocido"
            await send_whatsapp_message(phone, MENSAJE_CONTINGENCIA)
        except Exception:
            print(f"[POST /webhook] No fue posible enviar mensaje de contingencia.", flush=True)

    print(f"[POST /webhook] Procesado - 200 OK")
    return {"status": "ok"}


async def _procesar_estado_reserva(texto: str, phone: str) -> str:
    estado = get_reservation_state(phone)
    clear_pending_action(phone)

    if estado == RESERVATION_STATE_SELECT_HABITACION:
        return "🤷 No entendí la selección. Usa el menú para elegir un tipo de habitación."

    if estado == RESERVATION_STATE_FECHAS:
        texto = texto.strip()
        fechas = re.findall(r'\d{2}-\d{2}-\d{4}', texto)

        if len(fechas) < 2:
            return "Formato de fecha no válido. Por favor envíalo así: DD-MM-YYYY -- DD-MM-YYYY (Ejemplo: 25-09-2026 -- 28-09-2026)."

        try:
            check_in = ddmmyyyy_to_yyyymmdd(fechas[0])
            check_out = ddmmyyyy_to_yyyymmdd(fechas[1])
        except ValueError as e:
            return str(e)

        resultado_disp = consultar_disponibilidad(fechas[0], fechas[1])
        if resultado_disp.startswith("Lo sentimos") or resultado_disp.startswith("Formato de fecha"):
            return resultado_disp

        set_reservation_data(phone, "check_in", fechas[0])
        set_reservation_data(phone, "check_out", fechas[1])
        set_reservation_state(phone, RESERVATION_STATE_PERSONAL)

        tipo = get_reservation_data(phone, "tipo_habitacion")
        return "¡Habitación disponible para esas fechas! Por favor, indícame tu Nombre."

    if estado == RESERVATION_STATE_PERSONAL:
        paso = get_reservation_data(phone, "paso_personal") or 0
        datos = get_reservation_data(phone)
        texto = texto.strip()
        huesped_id = datos.get("huesped_id", 1)

        if not texto:
            return "Por favor, envía la información solicitada."

        if paso == 0:
            set_reservation_data(phone, "nombre", texto)
            set_reservation_data(phone, "paso_personal", 1)
            return "📋 Paso 2/7: Apellidos\nEnvíame tus apellidos."
        elif paso == 1:
            set_reservation_data(phone, "apellidos", texto)
            set_reservation_data(phone, "paso_personal", 2)
            return "🆔 Paso 3/7: Cédula / Pasaporte\nEnvíame tu número de cédula o pasaporte."
        elif paso == 2:
            set_reservation_data(phone, "cedula", texto)
            set_reservation_data(phone, "paso_personal", 3)
            return "🌍 Paso 4/7: Nacionalidad\nEnvíame tu nacionalidad."
        elif paso == 3:
            set_reservation_data(phone, "nacionalidad", texto)
            set_reservation_data(phone, "paso_personal", 4)
            return "📧 Paso 5/7: Correo Electrónico\nEnvíame tu correo electrónico."
        elif paso == 4:
            set_reservation_data(phone, "email", texto)
            set_reservation_data(phone, "paso_personal", 5)
            return "📱 Paso 6/7: Número Telefónico de Contacto\nEnvíame tu número de teléfono."
        elif paso == 5:
            set_reservation_data(phone, "telefono", texto)
            set_reservation_data(phone, "paso_personal", 6)

            set_reservation_state(phone, RESERVATION_STATE_HORA_LLEGADA)
            return (
                "✅ Datos personales recibidos.\n\n"
                "🕐 Paso 7/7: Hora Estimada de Llegada\n"
                "Envíame tu hora estimada de llegada en formato 12 horas.\n"
                "Ejemplo: 8:30 PM o 10:00 AM"
            )
        else:
            return "Paso no reconocido. Usa el menú para continuar."

    if estado == RESERVATION_STATE_HORA_LLEGADA:
        datos = get_reservation_data(phone)
        check_in = datos.get("check_in", "")
        check_out = datos.get("check_out", "")
        huesped_id = datos.get("huesped_id", 1)
        tipo = datos.get("tipo_habitacion", "Sencilla")
        precio_map = {"Sencilla": 150.0, "Doble": 250.0, "Triple": 350.0, "Cuádruple": 450.0, "Suite": 600.0}
        importe_total = precio_map.get(tipo, 150.0)

        try:
            hora_llegada = validar_hora_12h(texto)
        except ValueError as e:
            return str(e)

        check_in_yyyymmdd = ddmmyyyy_to_yyyymmdd(check_in)
        check_out_yyyymmdd = ddmmyyyy_to_yyyymmdd(check_out)

        nombre = datos.get("nombre", "")
        apellidos = datos.get("apellidos", "")
        cedula = datos.get("cedula", "")
        nacionalidad = datos.get("nacionalidad", "")
        email = datos.get("email", "")
        telefono = datos.get("telefono", "")

        resultado = registrar_reserva(huesped_id, tipo, check_in_yyyymmdd, check_out_yyyymmdd,
                                        "flexible", importe_total, hora_llegada,
                                        nombre=nombre, apellidos=apellidos, cedula=cedula,
                                        nacionalidad=nacionalidad, email=email, telefono=telefono)
        clear_reservation(phone)
        return resultado

    return "Estado de reserva no reconocido. Selecciona una opción del menú."


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
    try:
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
            resultado = consultar_servicios()
            await send_whatsapp_message(phone, resultado)
        elif selected_id == "btn_contacto":
            await send_whatsapp_message(
                phone,
                "Puedes contactarnos al teléfono +52 123 456 7890 o por email a recepcion@hotelparaiso.com",
            )
        elif selected_id == "opt_nueva_reserva":
            set_reservation_state(phone, RESERVATION_STATE_SELECT_HABITACION)
            clear_reservation_data(phone)
            clear_pending_action(phone)
            await send_room_type_list(phone)
        elif selected_id in ("hab_sencilla", "hab_doble", "hab_triple", "hab_cuadruple", "hab_suite"):
            tipo_map = {"hab_sencilla": "Sencilla", "hab_doble": "Doble", "hab_triple": "Triple", "hab_cuadruple": "Cuádruple", "hab_suite": "Suite"}
            tipo = tipo_map.get(selected_id, selected_id)
            set_reservation_data(phone, "tipo_habitacion", tipo)
            set_reservation_state(phone, RESERVATION_STATE_FECHAS)
            await send_whatsapp_message(
                phone,
                f"🏠 Tipo seleccionado: {tipo}\n\n📅 Envíame tus fechas de entrada y salida en formato DD-MM-YYYY.\nEjemplo: 25-09-2026 -- 28-09-2026",
            )
        elif selected_id == "opt_consultar":
            set_pending_action(phone, "consultar_reserva")
            await send_whatsapp_message(
                phone,
                "🔍 Para consultar tu reserva, envíame tu número de teléfono o ID de reserva.",
            )
        elif selected_id == "opt_llegada":
            set_pending_action(phone, "registrar_llegada")
            await send_whatsapp_message(
                phone,
                "📋 Para registrar tu llegada, envíame tu número de teléfono o ID de reserva.",
            )
        elif selected_id == "opt_servicios":
            resultado = consultar_servicios()
            await send_whatsapp_message(phone, resultado)
        elif selected_id == "opt_cancelar":
            set_pending_action(phone, "cancelar_reserva")
            await send_whatsapp_message(
                phone,
                "❌ Para cancelar tu reserva, envíame tu número de reserva o teléfono asociado.",
            )
        elif selected_id == "opt_recepcion":
            set_pending_action(phone, "escalar_recepcion")
            await send_whatsapp_message(
                phone,
                "🔔 Serás conectado con recepción para atención personalizada. "
                "Envíame tu consulta y un agente se pondrá en contacto contigo.",
            )
        elif selected_id == "opt_menu":
            clear_session(phone)
            clear_pending_action(phone)
            try:
                await send_interactive_list(phone)
            except Exception:
                fallback = (
                    "📋 **Menú Principal:**\n"
                    "1. 🏨 Nueva reserva\n"
                    "2. 🔍 Consultar reserva\n"
                    "3. 📋 Registrar llegada\n"
                    "4. 🛎️ Servicios\n"
                    "5. ❌ Cancelar reserva\n"
                    "6. 📞 Hablar con recepción"
                )
                await send_whatsapp_message(phone, fallback)
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
    except Exception as e:
        print(f"[POST /webhook] {phone}: Error en _handle_interactive: {e}", flush=True)
        import traceback
        traceback.print_exc()
        try:
            await send_whatsapp_message(phone, MENSAJE_CONTINGENCIA)
        except Exception:
            pass


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

    