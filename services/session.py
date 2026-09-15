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