"""Cross-platform canonical hashing for controlled contract text."""
from __future__ import annotations

import hashlib
from pathlib import Path

CANONICAL_CONTRACT_HASH_ALGORITHM = "SHA256_CANONICAL_TEXT_V1"


def canonicalize_contract_text_bytes(data: bytes) -> bytes:
    """Return UTF-8 contract text with a single LF newline representation.

    A UTF-8 BOM is accepted only as an input encoding marker and is not part of
    canonical content identity. All other bytes must decode as UTF-8.
    """
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def sha256_canonical_contract_bytes(data: bytes) -> str:
    return hashlib.sha256(canonicalize_contract_text_bytes(data)).hexdigest()


def sha256_canonical_contract_file(path: Path) -> str:
    return sha256_canonical_contract_bytes(path.read_bytes())