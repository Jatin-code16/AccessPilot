from app.core.models import Status


def derive_status(target_resolved: bool, remaining: list[str], introduced: list[str], control_passed: bool) -> Status:
    if not control_passed or introduced or not target_resolved:
        return "failed"
    if remaining:
        return "partial"
    return "passed"