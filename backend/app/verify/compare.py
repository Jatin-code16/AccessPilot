from app.core.models import Scan


def compare(before: Scan, after: Scan) -> tuple[list[str], list[str], list[str]]:
    before_keys = {finding.match_key for finding in before.findings if finding.kind == "violation"}
    after_keys = {finding.match_key for finding in after.findings if finding.kind == "violation"}
    return sorted(before_keys - after_keys), sorted(before_keys & after_keys), sorted(after_keys - before_keys)