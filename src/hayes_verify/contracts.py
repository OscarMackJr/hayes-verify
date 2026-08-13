from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


class ContractBundle:
    def __init__(self, root: Path):
        self.root = root
        self.contract_root = root / "contracts"
        self.schemas = self.contract_root / "schemas"
        self.freeze = json.loads(
            (self.contract_root / "contract_freeze.json").read_text(encoding="utf-8-sig")
        )

    @classmethod
    def discover(cls) -> ContractBundle:
        return cls(Path(__file__).resolve().parents[2])

    def _load_schema(self, name: str) -> dict:
        return json.loads((self.schemas / name).read_text(encoding="utf-8-sig"))

    def validate_request(self, payload: dict) -> None:
        schema = self._load_schema("wave2d_evaluation_request.schema.json")
        Draft202012Validator(schema).validate(payload)

    def validate_result(self, payload: dict) -> None:
        schema = self._load_schema("wave2d_evaluation_result.schema.json")
        Draft202012Validator(schema).validate(payload)
