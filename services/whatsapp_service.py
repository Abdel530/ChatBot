import httpx
from config import settings


async def send_whatsapp_message(to: str, text: str) -> dict | None:
    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        f"/{settings.whatsapp_phone_id}/messages"
    )
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error sending WhatsApp message to {to}: {e}")
        return None


async def send_interactive_buttons(to_phone: str, text_body: str, buttons: list) -> dict | None:
    """Envía un mensaje con hasta 3 botones de respuesta rápida (type: button)."""
    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        f"/{settings.whatsapp_phone_id}/messages"
    )
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
    action_buttons = [
        {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
        for btn in buttons[:3]
    ]
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text_body},
            "action": {"buttons": action_buttons},
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error sending interactive buttons to {to_phone}: {e}")
        return None


async def send_interactive_list(to_phone: str) -> dict | None:
    """Envía un menú desplegable (type: list) con opciones de reserva del Hotel Paraíso."""
    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        f"/{settings.whatsapp_phone_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Menú Principal"
            },
            "body": {
                "text": "Selecciona la opción que deseas:"
            },
            "action": {
                "button": "Ver opciones",
                "sections": [
                    {
                        "title": "Gestiones",
                        "rows": [
                            {
                                "id": "opt_nueva_reserva",
                                "title": "Nueva reserva",
                                "description": "Hacer una nueva reserva"
                            },
                            {
                                "id": "opt_consultar",
                                "title": "Consultar reserva",
                                "description": "Ver detalles de tu estancia"
                            },
                            {
                                "id": "opt_llegada",
                                "title": "Registrar llegada",
                                "description": "Información de check-in"
                            },
                            {
                                "id": "opt_servicios",
                                "title": "Servicios hotel",
                                "description": "WiFi, desayuno y horarios"
                            },
                            {
                                "id": "opt_cancelar",
                                "title": "Cancelar reserva",
                                "description": "Gestionar cancelación"
                            },
                            {
                                "id": "opt_recepcion",
                                "title": "Hablar con recepción",
                                "description": "Atención personalizada"
                            }
                        ]
                    }
                ]
            }
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            print(f"ERROR META API: {e.response.text}")
        else:
            print(f"ERROR META API: {e}")
        return None


async def send_interactive_list_custom(to_phone: str, text_body: str, button_label: str, sections: list) -> dict | None:
    """Envía un menú desplegable (type: list) personalizado con secciones y filas seleccionables."""
    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        f"/{settings.whatsapp_phone_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": text_body},
            "action": {
                "button": button_label,
                "sections": sections,
            },
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"[WHATSAPP API Error] send_interactive_list_custom to {to_phone}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[WHATSAPP API Error] Response body: {e.response.text}")
        return None


def format_whatsapp_message(from_number: str, text: str) -> dict:
    return {
        "from": from_number,
        "text": text,
    }


async def send_room_type_list(to_phone: str) -> dict | None:
    """Envía una lista interactiva con los tipos de habitación para reserva."""
    return await send_interactive_list_custom(
        to_phone,
        "🏨 Selecciona el tipo de habitación que deseas:",
        "Tipo Habitación",
        [
            {
                "title": "Tipos Disponibles",
                "rows": [
                    {"id": "hab_sencilla", "title": "Habitación Sencilla", "description": "Habitación individual cómoda"},
                    {"id": "hab_doble", "title": "Habitación Doble", "description": "Habitación doble con camas twin o king"},
                    {"id": "hab_triple", "title": "Habitación Triple", "description": "Habitación para 3 personas"},
                    {"id": "hab_cuadruple", "title": "Habitación Cuádruple", "description": "Habitación para 4 personas"},
                    {"id": "hab_suite", "title": "Suite", "description": "Suite premium con sala de estar"},
                ],
            }
        ],
    )


async def send_transfer_buttons(to_phone: str) -> dict | None:
    """Envía botones preguntando si necesita servicio de transfer."""
    return await send_interactive_buttons(
        to_phone,
        "¿Requieres servicio de transfer desde el aeropuerto?",
        [
            {"id": "transfer_sí", "title": "Sí"},
            {"id": "transfer_no", "title": "No"},
        ],
    )
