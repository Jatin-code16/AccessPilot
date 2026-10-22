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


def normalize_axe_results(result: dict[str, object], maximum: int = 500) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    passed = len(result.get("passes", [])) if isinstance(result.get("passes"), list) else 0
    for kind, key in (("violation", "violations"), ("incomplete", "incomplete")):
        items = result.get(key, [])
        if not isinstance(items, list):
            continue
        for rule in items:
            if not isinstance(rule, dict):
                continue
            nodes = rule.get("nodes", [])
            if not isinstance(nodes, list):
                continue
            for node_index, node in enumerate(nodes):
                if len(findings) >= maximum:
                    return findings, passed
                if not isinstance(node, dict):
                    continue
                targets = node.get("target", [])
                target = str(targets[0]) if isinstance(targets, list) and targets else "unknown"
                findings.append(normalize_finding(
                    finding_id=f"{rule.get('id', 'unknown')}-{node_index}",
                    source="axe",
                    kind=kind,
                    rule_id=str(rule.get("id", "unknown")),
                    impact=rule.get("impact") if rule.get("impact") in {"critical", "serious", "moderate", "minor"} else None,
                    help_text=str(rule.get("help", "")),
                    help_url=str(rule["helpUrl"]) if rule.get("helpUrl") else None,
                    tags=[str(tag) for tag in rule.get("tags", []) if isinstance(tag, str)],
                    target=target,
                    snippet=str(node.get("html", "")),
                ))
    return findings, passed
