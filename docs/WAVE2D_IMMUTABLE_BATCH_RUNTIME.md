# Wave 2D Immutable Batch Runtime

The runtime creates a unique batch identity, builds requests from EMS applicability plus controlled repository identities, and evaluates an explicitly supplied scoped runtime registry. Versioned evaluator registries remain authoritative; `generated/wave2d/batch/active_runtime_registry.json` is ephemeral and is restored or removed even when execution fails.

Repository identity is controlled in `registry/wave2d_repository_map.json`. Local repository paths are supplied separately through an execution-local override file and are never repository authority. The wrapper resolves Python in this order: `-PythonPath`, an active environment, PATH, repository `.venv`, then fails closed after checking required imports.