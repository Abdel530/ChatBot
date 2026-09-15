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


def format_whatsapp_message(from_number: str, text: str) -> dict:
    return {
        "from": from_number,
        "text": text,
    }
