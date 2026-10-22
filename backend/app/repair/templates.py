import html
import re
from dataclasses import dataclass

from app.core.errors import AccessPilotError


@dataclass(frozen=True)
class TemplateResult:
    source: str
    diff: str


def _single(source: str, pattern: str) -> re.Match[str]:
    matches = list(re.finditer(pattern, source, flags=re.IGNORECASE | re.DOTALL))
    if len(matches) != 1:
        raise AccessPilotError("template_mismatch", "The repair target was not found exactly once.", 409)
    return matches[0]


def _diff(original: str, updated: str, path: str) -> str:
    import difflib

    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=path,
        tofile=path,
    ))


def apply_t1(source: str, target_id: str, label_text: str, path: str) -> TemplateResult:
    escaped_id = re.escape(target_id)
    if re.search(rf"<label\b[^>]*\bfor\s*=\s*['\"]{escaped_id}['\"]", source, re.I):
        raise AccessPilotError("template_mismatch", "The input already has a label.", 409)
    match = _single(source, rf"<input\b[^>]*\bid\s*=\s*['\"]{escaped_id}['\"][^>]*>")
    label = f'<label for="{html.escape(target_id, quote=True)}">{html.escape(label_text)}</label>\n'
    updated = source[: match.start()] + label + source[match.start():]
    return TemplateResult(updated, _diff(source, updated, path))


def apply_t2(source: str, target_id: str, alt_text: str, path: str) -> TemplateResult:
    escaped_id = re.escape(target_id)
    match = _single(source, rf"<img\b[^>]*\bid\s*=\s*['\"]{escaped_id}['\"][^>]*>")
    tag = match.group(0)
    if re.search(r"\balt\s*=", tag, re.I):
        updated_tag = re.sub(r"\balt\s*=\s*(['\"]).*?\1", f'alt="{html.escape(alt_text, quote=True)}"', tag, count=1, flags=re.I)
    else:
        updated_tag = tag[:-1] + f' alt="{html.escape(alt_text, quote=True)}">'
    updated = source[: match.start()] + updated_tag + source[match.end():]
    return TemplateResult(updated, _diff(source, updated, path))


def apply_t4(source: str, language: str, path: str) -> TemplateResult:
    match = _single(source, r"<html\b[^>]*>")
    tag = match.group(0)
    if re.search(r"\blang\s*=", tag, re.I):
        raise AccessPilotError("template_mismatch", "The document already has a language.", 409)
    updated_tag = tag[:-1] + f' lang="{html.escape(language, quote=True)}">'
    updated = source[: match.start()] + updated_tag + source[match.end():]
    return TemplateResult(updated, _diff(source, updated, path))


def apply_t5(source: str, target_id: str, label_text: str, path: str) -> TemplateResult:
    escaped_id = re.escape(target_id)
    match = _single(source, rf"<button\b[^>]*\bid\s*=\s*['\"]{escaped_id}['\"][^>]*>")
    tag = match.group(0)
    label = html.escape(label_text, quote=True)
    if re.search(r"\baria-label\s*=", tag, re.I):
        updated_tag = re.sub(r"\baria-label\s*=\s*(['\"]).*?\1", f'aria-label="{label}"', tag, count=1, flags=re.I)
    else:
        updated_tag = tag[:-1] + f' aria-label="{label}">'
    updated = source[: match.start()] + updated_tag + source[match.end():]
    return TemplateResult(updated, _diff(source, updated, path))
