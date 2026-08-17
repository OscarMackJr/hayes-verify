from pathlib import Path

from hayes_verify.contract_hashing import (
    CANONICAL_CONTRACT_HASH_ALGORITHM,
    canonicalize_contract_text_bytes,
    sha256_canonical_contract_bytes,
    sha256_canonical_contract_file,
)


def test_lf_and_crlf_have_same_canonical_hash(tmp_path: Path) -> None:
    lf = b'{"type":"object"}\n'
    crlf = b'{"type":"object"}\r\n'
    assert sha256_canonical_contract_bytes(lf) == sha256_canonical_contract_bytes(crlf)
    path = tmp_path / "contract.json"
    path.write_bytes(crlf)
    assert sha256_canonical_contract_file(path) == sha256_canonical_contract_bytes(lf)


def test_bom_is_deterministic_and_non_newline_whitespace_is_significant() -> None:
    canonical = b'{"type":"object"}\n'
    assert canonicalize_contract_text_bytes(b"\xef\xbb\xbf" + canonical) == canonical
    assert sha256_canonical_contract_bytes(canonical) != sha256_canonical_contract_bytes(b'{ "type":"object"}\n')


def test_semantic_character_change_changes_hash() -> None:
    assert sha256_canonical_contract_bytes(b'{"const":"A"}\n') != sha256_canonical_contract_bytes(b'{"const":"B"}\n')


def test_algorithm_identifier_is_stable() -> None:
    assert CANONICAL_CONTRACT_HASH_ALGORITHM == "SHA256_CANONICAL_TEXT_V1"