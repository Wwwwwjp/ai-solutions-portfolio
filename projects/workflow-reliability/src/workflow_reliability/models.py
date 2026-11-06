"""Domain models for deterministic record synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Mapping


class ValidationError(ValueError):
    """Raised when an input record does not satisfy the sync contract."""


@dataclass(frozen=True)
class Record:
    """A versioned business record."""

    key: str
    version: int
    fields: Mapping[str, Any]
    updated_at: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Record":
        if not isinstance(value, Mapping):
            raise ValidationError("record must be an object")

        key = value.get("key")
        version = value.get("version")
        fields = value.get("fields")
        updated_at = value.get("updated_at")

        if not isinstance(key, str) or not key.strip():
            raise ValidationError("record key must be a non-empty string")
        if not isinstance(version, int) or isinstance(version, bool) or version < 0:
            raise ValidationError("record version must be a non-negative integer")
        if not isinstance(fields, Mapping):
            raise ValidationError("record fields must be an object")
        if not isinstance(updated_at, str) or not updated_at.strip():
            raise ValidationError("record updated_at must be a non-empty string")

        try:
            datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError("record updated_at must be ISO-8601") from exc

        return cls(
            key=key.strip(),
            version=version,
            fields=dict(fields),
            updated_at=updated_at,
        )

    @property
    def fingerprint(self) -> str:
        """Stable hash of business fields, excluding timing metadata."""
        payload = json.dumps(
            self.fields,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "version": self.version,
            "fields": dict(self.fields),
            "updated_at": self.updated_at,
        }
