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
            "weekly_digest_weekday": 0,
            "weekly_digest_state_file": " ./state.json ",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.report_config.email_to == "reports@example.com"
    assert loaded.report_config.report_frequency == "both"
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
            "weekly_digest_weekday": 0,
            "weekly_digest_state_file": "./state.json",
        },
    }
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_configuration(str(config_path))
    assert loaded.report_config.report_frequency == "none"


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
