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
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
    sections = [
        {
            "title": "Opciones de Reserva",
            "rows": [
                {"id": "opt_reserva", "title": "Consultar mi reserva", "description": "Ver detalles, estado o código"},
                {"id": "opt_checkin", "title": "Registrar hora de llegada", "description": "Check-in e información"},
                {"id": "opt_servicios", "title": "Información de servicios", "description": "WiFi, desayuno, parking, horarios"},
                {"id": "opt_cancelar", "title": "Cancelar reserva", "description": "Calcular penalización"},
                {"id": "opt_recepcion", "title": "Hablar con recepción", "description": "Atención personalizada"},
            ],
        },
    ]
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": "Menú de opciones del Hotel Paraíso. Selecciona una opción:"},
            "action": {
                "button": "Ver Opciones",
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
        print(f"Error sending interactive list to {to_phone}: {e}")
        return None


async def send_interactive_list_custom(to_phone: str, text_body: str, button_label: str, sections: list) -> dict | None:
    """Envía un menú desplegable (type: list) personalizado con secciones y filas seleccionables."""
    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        f"/{settings.whatsapp_phone_id}/messages"
    )
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
    payload = {
        "messaging_product": "whatsapp",
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
        print(f"Error sending interactive list to {to_phone}: {e}")
        return None


def format_whatsapp_message(from_number: str, text: str) -> dict:
    return {
        "from": from_number,
        "text": text,
    }
