import hashlib
import hmac
import time
from typing import Optional


def generate_signature(secret: str, timestamp: int, body: str) -> str:
    data = f"{timestamp}:{body}"
    return hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_signature(signature: str, secret: str, timestamp: int, body: str) -> bool:
    expected = generate_signature(secret, timestamp, body)
    return hmac.compare_digest(signature, expected)


def format_timestamp(dt=None) -> int:
    from datetime import datetime
    if dt is None:
        dt = datetime.now()
    return int(dt.timestamp() * 1000)


def parse_timestamp(ts: int) -> str:
    from datetime import datetime
    return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_numbers(text: str) -> list:
    import re
    return [int(n) for n in re.findall(r'\d+', text)]


def clean_text(text: str) -> str:
    import re
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text
