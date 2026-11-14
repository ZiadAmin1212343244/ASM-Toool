"""Signed cookie session management (local accounts; Entra-ready later)."""

from __future__ import annotations

import json
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import Settings


class SessionManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._serializer = URLSafeTimedSerializer(
            settings.secret_key, salt="tpm-session-v1"
        )

    def dump(self, data: dict) -> str:
        return self._serializer.dumps(data)

    def load(self, token: str) -> dict | None:
        try:
            payload = self._serializer.loads(
                token, max_age=self.settings.session_max_age_seconds
            )
        except (BadSignature, SignatureExpired):
            return None
        if not isinstance(payload, dict):
            return None
        return payload

    def dumps_json(self, data: dict) -> str:
        return json.dumps(data)
