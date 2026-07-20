from email.message import EmailMessage
from types import SimpleNamespace

from message_parsing import extract_text, parse_response_text


def _mail_config(min_non_spam_score=8):
    return SimpleNamespace(
        forward_to="ops@example.com",
        spam_forward_to="spam@example.com",
        non_spam_folder="Processed/NonSpam",
        spam_folder="Processed/Spam",
        min_non_spam_score=min_non_spam_score,
    )


def test_parse_response_text_lead_score_clamped():
    response_text = "summary: Looks promising\ncategory: lead\nscore: 99"
    summary, category, score = parse_response_text(response_text)

    assert summary == "Looks promising"
    assert category == "lead"
    assert score == 10


def test_parse_response_text_non_lead_forces_zero():
    response_text = "summary: Probably spam\ncategory: spam\nscore: 7"
    summary, category, score = parse_response_text(response_text)

    assert summary == "Probably spam"
    assert category == "spam"
    assert score == 0


def test_parse_response_text_unknown_category_defaults_irrelevant():
    summary, category, score = parse_response_text("category: unknown\nscore: 3")

    assert summary == "No summary generated"
    assert category == "irrelevant"
    assert score == 0


def test_extract_text_prefers_plain_text():
    msg = EmailMessage()
    msg.set_content("Plain body")
    msg.add_alternative("<html><body><p>HTML body</p></body></html>", subtype="html")

    extracted = extract_text(msg)
    assert extracted == "Plain body"


def test_extract_text_uses_html_when_no_plain():
    msg = EmailMessage()
    msg.set_content("<html><body><b>Hello</b> world</body></html>", subtype="html")

    extracted = extract_text(msg)
    assert "Hello world" in extracted


def test_resolve_destinations_spam_always_uses_spam(main_module):
    target_email, target_folder = main_module.resolve_destinations("spam", 10, _mail_config())
    assert target_email == "spam@example.com"
    assert target_folder == "Processed/Spam"


def test_resolve_destinations_lead_below_threshold_uses_spam(main_module):
    target_email, target_folder = main_module.resolve_destinations("lead", 7, _mail_config())
    assert target_email == "spam@example.com"
    assert target_folder == "Processed/Spam"


def test_resolve_destinations_lead_at_threshold_uses_non_spam(main_module):
    target_email, target_folder = main_module.resolve_destinations("lead", 8, _mail_config())
    assert target_email == "ops@example.com"
    assert target_folder == "Processed/NonSpam"


def test_resolve_destinations_irrelevant_uses_spam(main_module):
    target_email, target_folder = main_module.resolve_destinations("irrelevant", 0, _mail_config())
    assert target_email == "spam@example.com"
    assert target_folder == "Processed/Spam"


def test_resolve_destinations_respects_custom_threshold(main_module):
    mail_config = _mail_config(min_non_spam_score=5)
    target_email, target_folder = main_module.resolve_destinations("lead", 5, mail_config)
    assert target_email == "ops@example.com"
    assert target_folder == "Processed/NonSpam"
