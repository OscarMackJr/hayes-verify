from hayes_verify.wave2d_targets import validate_target


def test_organization_target_has_no_repository_path():
    validate_target({"target_type": "ORGANIZATION", "evaluation_role": "AUTHORITATIVE_EVALUATION", "organization_id": "ORG-001"})


def test_projection_cannot_be_authoritative_pass():
    try:
        validate_target({"target_type": "REPOSITORY", "repository_path": "x", "evaluation_role": "PROJECTION", "authoritative_pass": True})
    except ValueError:
        return
    raise AssertionError("projection PASS accepted")