from app.core.models import Explanation


EXPLANATIONS: dict[str, Explanation] = {
    "label": Explanation(
        who="A screen-reader user",
        blockedFrom="knowing what to enter",
        why="The field has no associated label.",
    ),
    "image-alt": Explanation(
        who="A screen-reader user",
        blockedFrom="understanding the image",
        why="The image has no alternative text.",
    ),
    "color-contrast": Explanation(
        who="A person with low vision",
        blockedFrom="reading the helper text",
        why="The text does not contrast enough with its background.",
    ),
    "html-has-lang": Explanation(
        who="A screen-reader user",
        blockedFrom="hearing the page in the right language",
        why="The document does not declare its language.",
    ),
    "button-name": Explanation(
        who="A screen-reader user",
        blockedFrom="knowing what the button does",
        why="The button has no accessible name.",
    ),
}


def explanation_for(rule_id: str) -> Explanation:
    return EXPLANATIONS.get(
        rule_id,
        Explanation(
            who="A person using assistive technology",
            blockedFrom="using this part of the page",
            why="The automated check found a possible accessibility problem.",
        ),
    )
