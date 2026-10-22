import hashlib

from app.core.models import Finding, FindingKind, FindingSource, Impact, TemplateName
from app.knowledge.explanations import explanation_for


TEMPLATES: dict[str, TemplateName] = {
    "label": "T1",
    "image-alt": "T2",
    "color-contrast": "T3",
    "html-has-lang": "T4",
    "button-name": "T5",
}


def _bounded(value: str, limit: int = 300) -> str:
    return value[:limit]


def normalize_finding(
    *,
    finding_id: str,
    source: FindingSource,
    kind: FindingKind,
    rule_id: str,
    impact: Impact | None,
    help_text: str,
    help_url: str | None,
    tags: list[str],
    target: str,
    snippet: str,
) -> Finding:
    match_key = f"{rule_id}|{target}"
    fingerprint = hashlib.sha256(f"{rule_id}|{target}|{snippet}".encode()).hexdigest()
    template = TEMPLATES.get(rule_id)
    return Finding(
        id=finding_id,
        matchKey=match_key,
        fingerprint=fingerprint,
        source=source,
        kind=kind,
        ruleId=rule_id,
        impact=impact,
        help=help_text,
        helpUrl=help_url,
        tags=tags,
        wcag=[tag for tag in tags if tag.startswith("wcag")],
        target=target,
        snippet=_bounded(snippet),
        explanation=explanation_for(rule_id),
        template=template,
        needsHuman=kind == "incomplete" or template is None,
    )
