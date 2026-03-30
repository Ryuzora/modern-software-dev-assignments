from backend.app.services.extract import extract_action_items, extract_action_items_detailed


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - ACTION: review PR
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert "TODO: write tests" in items
    assert "ACTION: review PR" in items
    assert "Ship it!" in items


def test_extract_action_items_handles_noisy_input_and_dedup():
    text = """
    [ ] TODO:   write docs
    1) action item - Please review PR before 5pm
    FYI: this is just context
    - not actionable: discussion only
    * let's deploy to production tomorrow!
    [x] TODO: write docs
    """.strip()

    items = extract_action_items(text)
    assert "TODO: write docs" in items
    assert "action item - Please review PR before 5pm" in items
    assert "let's deploy to production tomorrow!" in items
    assert len(items) == 3


def test_extract_action_items_detailed_category_and_priority():
    text = """
    ACTION: fix regression bug ASAP
    TODO: update README
    Please review PR before 3pm
    """.strip()

    items = extract_action_items_detailed(text)
    by_text = {item.text: item for item in items}

    assert by_text["ACTION: fix regression bug ASAP"].category == "testing"
    assert by_text["ACTION: fix regression bug ASAP"].priority == "high"

    assert by_text["TODO: update README"].category == "documentation"
    assert by_text["TODO: update README"].priority in {"medium", "high"}

    assert by_text["Please review PR before 3pm"].category == "review"
    assert by_text["Please review PR before 3pm"].priority in {"medium", "high"}

