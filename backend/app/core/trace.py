from datetime import datetime, timezone
from time import perf_counter

from app.core.models import Actor, TraceEntry


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TraceTimer:
    def __init__(self, seq: int, actor: Actor, name: str, summary: str) -> None:
        self.seq = seq
        self.actor = actor
        self.name = name
        self.summary = summary
        self.started_at = utc_now()
        self.started = perf_counter()

    def finish(self, ok: bool = True, output_summary: str | None = None, error_code: str | None = None) -> TraceEntry:
        duration_ms = round((perf_counter() - self.started) * 1000)
        return TraceEntry(
            seq=self.seq,
            actor=self.actor,
            name=self.name,
            summary=self.summary,
            outputSummary=output_summary,
            durationMs=duration_ms,
            ok=ok,
            errorCode=error_code,
            startedAt=self.started_at,
        )
