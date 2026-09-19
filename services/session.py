from typing import Any

_sessions: dict[str, list[dict[str, Any]]] = {}


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