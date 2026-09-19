from typing import Any

_sessions: dict[str, list[dict[str, Any]]] = {}

RESERVATION_STATE_IDLE = "idle"
RESERVATION_STATE_SELECT_HABITACION = "select_habitacion"
RESERVATION_STATE_FECHAS = "fechas"
RESERVATION_STATE_PERSONAL = "personal"
RESERVATION_STATE_HORA_LLEGADA = "hora_llegada"
RESERVATION_STATE_COMPLETE = "complete"

PASO_PERSONAL_NAMES = ["nombre", "cedula", "nacionalidad", "email", "telefono"]


def add_message(phone: str, role: str, text: str) -> None:
    if phone not in _sessions:
        _sessions[phone] = []
    _sessions[phone].append({"role": role, "text": text})


def get_history(phone: str, limit: int = 10) -> list[dict[str, Any]]:
    history = _sessions.get(phone, [])
    return history[-limit:]


def clear_session(phone: str) -> None:
    _sessions.pop(phone, None)


def get_session(phone: str) -> list[dict[str, Any]]:
    return _sessions.get(phone, [])


def set_pending_action(phone: str, action: str) -> None:
    if phone not in _sessions:
        _sessions[phone] = []
    for entry in _sessions[phone]:
        if entry.get("role") == "pending_action":
            entry["text"] = action
            return
    _sessions[phone].append({"role": "pending_action", "text": action})


def get_pending_action(phone: str) -> str | None:
    history = _sessions.get(phone, [])
    for entry in reversed(history):
        if entry.get("role") == "pending_action":
            return entry["text"]
    return None


def clear_pending_action(phone: str) -> None:
    if phone in _sessions:
        _sessions[phone] = [e for e in _sessions[phone] if e.get("role") != "pending_action"]


def set_reservation_state(phone: str, state: str) -> None:
    if phone not in _sessions:
        _sessions[phone] = []
    for entry in _sessions[phone]:
        if entry.get("role") == "reservation_state":
            entry["text"] = state
            return
    _sessions[phone].append({"role": "reservation_state", "text": state})


def get_reservation_state(phone: str) -> str:
    history = _sessions.get(phone, [])
    for entry in reversed(history):
        if entry.get("role") == "reservation_state":
            return entry["text"]
    return RESERVATION_STATE_IDLE


def set_reservation_data(phone: str, key: str, value: Any) -> None:
    if phone not in _sessions:
        _sessions[phone] = []
    for entry in _sessions[phone]:
        if entry.get("role") == "reservation_data" and entry.get("key") == key:
            entry["value"] = value
            return
    _sessions[phone].append({"role": "reservation_data", "key": key, "value": value})


def get_reservation_data(phone: str, key: str = None) -> Any:
    history = _sessions.get(phone, [])
    if key:
        for entry in reversed(history):
            if entry.get("role") == "reservation_data" and entry.get("key") == key:
                return entry["value"]
        return None
    data = {}
    for entry in reversed(history):
        if entry.get("role") == "reservation_data":
            data[entry["key"]] = entry["value"]
    return data


def clear_reservation(phone: str) -> None:
    if phone in _sessions:
        _sessions[phone] = [e for e in _sessions[phone] if e.get("role") not in ("reservation_state", "reservation_data")]
    clear_pending_action(phone)


def clear_reservation_data(phone: str) -> None:
    if phone in _sessions:
        _sessions[phone] = [e for e in _sessions[phone] if e.get("role") != "reservation_data"]