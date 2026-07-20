import json
import tempfile
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    StrictInt,
    StrictStr,
    ValidationError,
    field_validator,
    model_validator,
)

CONFIGURATION_VERSION = 0


class MailConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email_server: StrictStr
    email_user: StrictStr
    email_password: StrictStr
    imap_port: StrictInt
    smtp_port: StrictInt
    forward_to: StrictStr | None
    spam_forward_to: StrictStr | None
    inbox_folder: StrictStr
    non_spam_folder: StrictStr | None
    spam_folder: StrictStr | None
    min_non_spam_score: StrictInt = 8

    @field_validator("forward_to", "spam_forward_to", "non_spam_folder", "spam_folder", mode="before")
    @classmethod
    def _normalize_destinations(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("min_non_spam_score")
    @classmethod
    def _validate_min_non_spam_score(cls, value):
        if not 1 <= value <= 10:
            raise ValueError("min_non_spam_score must be between 1 and 10.")
        return value

    @model_validator(mode="after")
    def _validate_destinations(self):
        if not (self.forward_to or self.non_spam_folder):
            raise ValueError(
                "mail_config must define at least one non-spam destination: "
                "'forward_to' or 'non_spam_folder'."
            )
        if not (self.spam_forward_to or self.spam_folder):
            raise ValueError(
                "mail_config must define at least one spam destination: "
                "'spam_forward_to' or 'spam_folder'."
            )
        return self


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_key: StrictStr
    model: StrictStr
    instructions: StrictStr
    prompt_template: StrictStr


class ReportConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email_to: StrictStr | None = None
    report_frequency: Literal["none", "daily", "weekly", "both"] = "both"
    daily_digest_send_hour: StrictInt = 0
    daily_digest_state_file: StrictStr = "./assets/daily_digest_state.json"
    weekly_digest_weekday: StrictInt = 0
    weekly_digest_state_file: StrictStr = "./assets/weekly_digest_state.json"

    @field_validator("email_to", "daily_digest_state_file", "weekly_digest_state_file", mode="before")
    @classmethod
    def _normalize_report_fields(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("weekly_digest_weekday")
    @classmethod
    def _validate_weekday(cls, value):
        if not 0 <= value <= 6:
            raise ValueError("weekly_digest_weekday must be between 0 (Monday) and 6 (Sunday).")
        return value

    @field_validator("daily_digest_send_hour")
    @classmethod
    def _validate_daily_send_hour(cls, value):
        if not 0 <= value <= 23:
            raise ValueError("daily_digest_send_hour must be between 0 and 23.")
        return value

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_weekly_flag(cls, data):
        if not isinstance(data, dict):
            return data

        if "report_frequency" in data:
            return data

        # Backward-compatible mapping for legacy configs.
        legacy_weekly_enabled = data.pop("weekly_digest_enabled", None)
        if isinstance(legacy_weekly_enabled, bool):
            data["report_frequency"] = "both" if legacy_weekly_enabled else "daily"

        return data


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: StrictInt
    mail_config: MailConfig
    llm_config: LLMConfig
    report_config: ReportConfig = ReportConfig()


def load_configuration(config_file):
    """Attempt loading config from JSON and validate it"""
    with open(config_file, "rt", encoding="utf-8") as config_data:
        config_json = json.load(config_data)
        try:
            return AppConfig.model_validate(config_json)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc


def dir_exists(directory):
    """Check that directory exists and is writeable"""
    if directory.exists():
        if directory.is_dir():
            with tempfile.TemporaryFile(dir=directory) as write_check:
                write_check.write(b"Test")
        else:
            raise OSError(f"Cannot write to {directory.absolute()}")
    else:
        raise OSError(f"{directory.absolute()} does not exist!")
