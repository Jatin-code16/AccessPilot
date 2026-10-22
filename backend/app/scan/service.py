from hashlib import sha256
from uuid import uuid4

from app.core.config import Settings
from app.core.models import Coverage, Engine, Scan, TraceEntry
from app.core.trace import TraceTimer, utc_now
from app.scan.browser import scan_url_sync
from app.scan.normalize import normalize_axe_results


def run_scan(url: str, settings: Settings) -> Scan:
    started = TraceTimer(1, "scanner", "load_page", "Loaded page")
    raw = scan_url_sync(url, settings.axe_path, settings.browser_timeout_ms)
    trace: list[TraceEntry] = [started.finish(output_summary="Page loaded")]
    findings, pass_count = normalize_axe_results(raw["axe"])
    trace.append(TraceTimer(2, "scanner", "run_checks", "Checks run").finish(output_summary=f"Found {len(findings)} findings"))
    trace.append(TraceTimer(3, "system", "coverage", "Limits recorded").finish(output_summary="Captions and reading order not checked"))
    return Scan(
        id=str(uuid4()),
        url=url,
        workingCopyId=None,
        startedAt=utc_now(),
        durationMs=sum(entry.duration_ms or 0 for entry in trace),
        title=str(raw["title"]),
        engine=Engine(name="axe-core", version="4.14.0"),
        findings=findings,
        passCount=pass_count,
        coverage=Coverage(
            ran=["axe-core 4.14.0", "WCAG A, AA, best-practice"],
            didNotRun=["captions", "reading order", "content meaning", "real screen readers"],
            needsPerson=[finding.rule_id for finding in findings if finding.needs_human],
        ),
        trace=trace,
    )


def finding_fingerprint(scan: Scan) -> str:
    return sha256("|".join(finding.match_key for finding in scan.findings).encode()).hexdigest()