from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvaluatorBinding:
    control_id: str
    family: str
    module_name: str
    collector: str
    evaluator: str
    evidence_type: str
    supported: bool
    metadata: dict[str, Any]


class EvaluatorRegistry:
    def __init__(self, path: Path):
        self.path = path
        self.document = json.loads(path.read_text(encoding="utf-8-sig"))
        self._bindings = self._build_bindings()

    def _build_bindings(self) -> dict[str, EvaluatorBinding]:
        bindings: dict[str, EvaluatorBinding] = {}
        for family_name, family in self.document["families"].items():
            module_name = family["implementation"]
            for control_id, metadata in family.get("controls", {}).items():
                bindings[control_id] = EvaluatorBinding(
                    control_id=control_id,
                    family=family_name,
                    module_name=module_name,
                    collector=metadata["collector"],
                    evaluator=metadata["evaluator"],
                    evidence_type=metadata["evidence_type"],
                    supported=bool(metadata.get("supported", False)),
                    metadata=metadata,
                )
        return bindings

    def lookup(self, control_id: str) -> EvaluatorBinding | None:
        return self._bindings.get(control_id)

    def require_supported(self, control_id: str) -> EvaluatorBinding:
        binding = self.lookup(control_id)
        if binding is None:
            raise ValueError(f"Unregistered Wave 2D control: {control_id}")
        if not binding.supported:
            raise ValueError(f"Evaluator not implemented for control: {control_id}")
        return binding

    def load_callable(self, control_id: str):
        binding = self.require_supported(control_id)
        module = importlib.import_module(binding.module_name)
        runner = getattr(module, "run", None)
        if runner is None:
            raise RuntimeError(f"Evaluator family has no run() function: {binding.module_name}")
        return binding, runner
