from __future__ import annotations

import hashlib
import json
from typing import Any


def tool_fingerprint(name: str, arguments: dict[str, Any]) -> str:
    payload = {
        "name": name,
        "arguments": arguments,
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()
