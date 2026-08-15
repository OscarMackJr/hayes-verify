import json
from pathlib import Path

import pytest

from hayes_verify.evaluator_registry import EvaluatorRegistry


def make_registry(tmp_path: Path) -> Path:
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(
            {
                "families": {
                    "demo": {
                        "implementation": "hayes_verify.evaluator_families.repository_filesystem",
                        "controls": {
                            "EMS-CTRL-999": {
                                "collector": "x",
                                "evaluator": "y",
                                "evidence_type": "DEMO",
                                "supported": False,
                            }
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_registry_returns_binding(tmp_path):
    registry = EvaluatorRegistry(make_registry(tmp_path))
    binding = registry.lookup("EMS-CTRL-999")
    assert binding is not None
    assert binding.family == "demo"
    assert binding.supported is False


def test_registry_fails_closed_for_unimplemented(tmp_path):
    registry = EvaluatorRegistry(make_registry(tmp_path))
    with pytest.raises(ValueError, match="not implemented"):
        registry.require_supported("EMS-CTRL-999")


def test_registry_fails_closed_for_unregistered(tmp_path):
    registry = EvaluatorRegistry(make_registry(tmp_path))
    with pytest.raises(ValueError, match="Unregistered"):
        registry.require_supported("EMS-CTRL-123")
