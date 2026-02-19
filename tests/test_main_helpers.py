from email.message import EmailMessage


def test_parse_response_text_lead_score_clamped(main_module):
    response_text = "summary: Looks promising\ncategory: lead\nscore: 99"
    summary, category, score = main_module.parse_response_text(response_text)

    assert summary == "Looks promising"
    assert category == "lead"
    assert score == 10


def test_parse_response_text_non_lead_forces_zero(main_module):
    response_text = "summary: Probably spam\ncategory: spam\nscore: 7"
    summary, category, score = main_module.parse_response_text(response_text)

    assert summary == "Probably spam"
    assert category == "spam"
    assert score == 0


def test_parse_response_text_unknown_category_defaults_irrelevant(main_module):
    summary, category, score = main_module.parse_response_text("category: unknown\nscore: 3")

    assert summary == "No summary generated"
    assert category == "irrelevant"
    assert score == 0


def test_extract_text_prefers_plain_text(main_module):
    msg = EmailMessage()
    msg.set_content("Plain body")
    msg.add_alternative("<html><body><p>HTML body</p></body></html>", subtype="html")

    extracted = main_module.extract_text(msg)
    assert extracted == "Plain body"


def test_extract_text_uses_html_when_no_plain(main_module):
    msg = EmailMessage()
    msg.set_content("<html><body><b>Hello</b> world</body></html>", subtype="html")

    extracted = main_module.extract_text(msg)
    assert "Hello world" in extracted
