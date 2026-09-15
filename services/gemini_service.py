import json
import logging
import time
from config import settings
from google import genai
from google.genai.types import Tool, GenerateContentConfig, FunctionDeclaration
from google.genai.errors import ServerError
from services.session import get_history

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.gemini_api_key)

MAX_RETRIES = 3
RETRY_DELAY = 2

TOOLS: list[Tool] = []

TOOL_HANDLERS = {}


def _retry_generate_content(**kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            return client.models.generate_content(model=settings.gemini_model, **kwargs)
        except ServerError as e:
            if e.code == 503 and attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Gemini 503, reintentando en {delay}s (intento {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError("Max retries exceeded")


def _build_config(tools: list[Tool] | None = None, tool_config: dict | None = None) -> GenerateContentConfig | None:
    kwargs: dict = {}
    if tools:
        kwargs["tools"] = tools
    if tool_config:
        kwargs["tool_config"] = tool_config
    return GenerateContentConfig(**kwargs) if kwargs else None


def process_message(message: str, phone: str) -> str:
    history = get_history(phone)
    system_prompt = _load_system_prompt()
    contents = [system_prompt]
    for entry in history:
        contents.append(entry["text"])
    contents.append(message)

    try:
        response = _retry_generate_content(contents=contents)
        return _parse_response(response)["text"]
    except ServerError as e:
        logger.error(f"Error procesando mensaje con Gemini tras reintentos: {e}")
        return "Lo siento, el servicio está muy ocupado en este momento. Por favor, intenta de nuevo en unos minutos."
    except Exception as e:
        logger.error(f"Error procesando mensaje con Gemini: {e}")
        return "Lo siento, ocurrió un error. Por favor, intenta de nuevo."


def chat_with_tools(message: str, tools: list[Tool] | None = None, tool_config: dict | None = None) -> dict:
    system_prompt = _load_system_prompt()
    history = get_history("")

    contents = [system_prompt]
    for entry in history:
        contents.append(entry["text"])
    contents.append(message)

    kwargs = {"contents": contents}
    config = _build_config(tools, tool_config)
    if config:
        kwargs["config"] = config

    try:
        response = _retry_generate_content(**kwargs)
        return _parse_response(response)
    except ServerError as e:
        logger.error(f"Error calling Gemini tras reintentos: {e}")
        return {"text": "Lo siento, el servicio está muy ocupado en este momento. Por favor, intenta de nuevo en unos minutos.", "tool_calls": []}
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
        return {"text": "Lo siento, ocurrió un error. Por favor, intenta de nuevo.", "tool_calls": []}


def chat_with_tools_and_session(message: str, phone: str, tools: list[Tool] | None = None, tool_config: dict | None = None) -> dict:
    system_prompt = _load_system_prompt()
    history = get_history(phone)

    contents = [system_prompt]
    for entry in history:
        contents.append(entry["text"])
    contents.append(message)

    kwargs = {"contents": contents}
    config = _build_config(tools, tool_config)
    if config:
        kwargs["config"] = config

    try:
        response = _retry_generate_content(**kwargs)
        return _parse_response(response)
    except ServerError as e:
        logger.error(f"Error calling Gemini tras reintentos: {e}")
        return {"text": "Lo siento, el servicio está muy ocupado en este momento. Por favor, intenta de nuevo en unos minutos.", "tool_calls": []}
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
        return {"text": "Lo siento, ocurrió un error. Por favor, intenta de nuevo.", "tool_calls": []}


def _load_system_prompt() -> str:
    try:
        with open("prompts/system.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Eres un asistente de hotel. Responde en español."


def _parse_response(response) -> dict:
    result = {"text": "", "tool_calls": []}

    text_parts = []
    for part in response.candidates:
        if part.content and part.content.parts:
            for p in part.content.parts:
                if hasattr(p, 'text') and p.text:
                    text_parts.append(p.text)

    result["text"] = "\n".join(text_parts) if text_parts else str(response.text) if hasattr(response, 'text') else ""

    if hasattr(response, 'function_calls') and response.function_calls:
        for fc in response.function_calls:
            result["tool_calls"].append({
                "name": fc.name,
                "args": fc.args if isinstance(fc.args, dict) else {},
            })

    try:
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call'):
                            result["tool_calls"].append({
                                "name": part.function_call.name,
                                "args": part.function_call.args if isinstance(part.function_call.args, dict) else {},
                            })
    except Exception:
        pass

    return result


def register_tool(name: str, handler, fn_decl: FunctionDeclaration) -> None:
    TOOL_HANDLERS[name] = handler
    TOOLS.append(Tool(function_declarations=[fn_decl]))


def execute_tool(name: str, args: dict) -> str:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return f"Error: herramienta '{name}' no encontrada"
    try:
        result = handler(**args)
        return result
    except Exception as e:
        return f"Error ejecutando {name}: {e}"