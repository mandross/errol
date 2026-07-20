import json

import pytest

from config import CONFIGURATION_VERSION, load_configuration


def test_load_configuration_validates_and_loads(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.version == CONFIGURATION_VERSION
    assert loaded.mail_config.forward_to == "ops@example.com"
    assert loaded.mail_config.min_non_spam_score == 8


def test_load_configuration_accepts_min_non_spam_score_override(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
            "min_non_spam_score": 5,
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.mail_config.min_non_spam_score == 5


@pytest.mark.parametrize("invalid_score", [0, 11])
def test_load_configuration_rejects_invalid_min_non_spam_score(tmp_path, invalid_score):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
            "min_non_spam_score": invalid_score,
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(ValueError, match="min_non_spam_score"):
        load_configuration(str(config_path))


def test_load_configuration_accepts_folder_only_destinations(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "",
            "spam_forward_to": "",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.mail_config.non_spam_folder == "Processed/NonSpam"
    assert loaded.mail_config.spam_folder == "Processed/Spam"


def test_load_configuration_rejects_missing_non_spam_destinations(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(ValueError, match="non-spam destination"):
        load_configuration(str(config_path))


def test_load_configuration_rejects_missing_spam_destinations(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(ValueError, match="spam destination"):
        load_configuration(str(config_path))


def test_load_configuration_rejects_unknown_fields(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
            "unexpected_mail_field": "nope",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(ValueError, match="extra_forbidden"):
        load_configuration(str(config_path))


def test_load_configuration_rejects_non_integer_ports(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": "993",
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(ValueError, match="valid integer"):
        load_configuration(str(config_path))


def test_load_configuration_normalizes_whitespace_destinations(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "  ops@example.com  ",
            "spam_forward_to": "   ",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "  Processed/Spam  ",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.mail_config.forward_to == "ops@example.com"
    assert loaded.mail_config.spam_forward_to is None
    assert loaded.mail_config.spam_folder == "Processed/Spam"


def test_load_configuration_accepts_report_config(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
        "report_config": {
            "email_to": "  reports@example.com  ",
            "report_frequency": "both",
            "daily_digest_send_hour": 8,
            "daily_digest_state_file": " ./daily-state.json ",
            "weekly_digest_weekday": 0,
            "weekly_digest_state_file": " ./state.json ",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.report_config.email_to == "reports@example.com"
    assert loaded.report_config.report_frequency == "both"
    assert loaded.report_config.daily_digest_send_hour == 8
    assert loaded.report_config.daily_digest_state_file == "./daily-state.json"
    assert loaded.report_config.weekly_digest_state_file == "./state.json"


def test_load_configuration_rejects_invalid_report_weekday(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
        "report_config": {
            "email_to": "reports@example.com",
            "report_frequency": "both",
            "daily_digest_send_hour": 0,
            "weekly_digest_weekday": 7,
            "weekly_digest_state_file": "./state.json",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(ValueError, match="weekly_digest_weekday"):
        load_configuration(str(config_path))


def test_load_configuration_rejects_invalid_report_frequency(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
        "report_config": {
            "email_to": "reports@example.com",
            "report_frequency": "hourly",
            "daily_digest_send_hour": 0,
            "weekly_digest_weekday": 0,
            "weekly_digest_state_file": "./state.json",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(ValueError, match="report_frequency"):
        load_configuration(str(config_path))


def test_load_configuration_accepts_report_frequency_none(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
        "report_config": {
            "email_to": "reports@example.com",
            "report_frequency": "none",
            "daily_digest_send_hour": 0,
            "weekly_digest_weekday": 0,
            "weekly_digest_state_file": "./state.json",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.report_config.report_frequency == "none"


def test_load_configuration_rejects_invalid_daily_send_hour(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
        "report_config": {
            "email_to": "reports@example.com",
            "report_frequency": "daily",
            "daily_digest_send_hour": 24,
            "weekly_digest_weekday": 0,
            "weekly_digest_state_file": "./state.json",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(ValueError, match="daily_digest_send_hour"):
        load_configuration(str(config_path))


def test_load_configuration_accepts_legacy_weekly_digest_flag(tmp_path):
    config_path = tmp_path / "config.json"
    config_data = {
        "version": CONFIGURATION_VERSION,
        "mail_config": {
            "email_server": "imap.example.com",
            "email_user": "user@example.com",
            "email_password": "secret",
            "imap_port": 993,
            "smtp_port": 465,
            "forward_to": "ops@example.com",
            "spam_forward_to": "spam@example.com",
            "inbox_folder": "INBOX",
            "non_spam_folder": "Processed/NonSpam",
            "spam_folder": "Processed/Spam",
        },
        "llm_config": {
            "api_key": "dummy",
            "model": "gpt-4.1-mini",
            "instructions": "classify",
            "prompt_template": "Content: {content}",
        },
        "report_config": {
            "email_to": "reports@example.com",
            "weekly_digest_enabled": False,
            "weekly_digest_weekday": 0,
            "weekly_digest_state_file": "./state.json",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.report_config.report_frequency == "daily"
