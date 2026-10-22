from app.core.models import ScanRequest
from app.repair.templates import apply_t1, apply_t2, apply_t4, apply_t5


def test_request_uses_frontend_contract_aliases() -> None:
    request = ScanRequest.model_validate({"url": "https://example.com", "consent": True})
    assert request.model_dump(by_alias=True)["keyboardWalk"] is False


def test_t1_is_deterministic_and_escapes_text() -> None:
    source = '<input id="email">\n'
    first = apply_t1(source, "email", '<Email>', "index.html")
    second = apply_t1(source, "email", '<Email>', "index.html")
    assert first == second
    assert '&lt;Email&gt;' in first.source


def test_t2_t4_and_t5_update_only_the_target() -> None:
    image = apply_t2('<img id="photo">', "photo", 'A student', "index.html")
    language = apply_t4('<html><body></body></html>', "en", "index.html")
    button = apply_t5('<button id="submit">Save</button>', "submit", "Save form", "index.html")
    assert 'alt="A student"' in image.source
    assert '<html lang="en">' in language.source
    assert 'aria-label="Save form"' in button.source
