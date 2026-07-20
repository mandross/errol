import imaplib
import logging
import time
from openai import OpenAI

from args import parse_arguments
from config import load_configuration
from mailbox_handler import (
    ensure_mailbox_folder,
    fetch_email_by_id,
    fetch_email_ids,
    forward_email,
    move_email_to_folder,
    open_imap_connection,
    send_text_email,
)
from message_parsing import extract_text, parse_response_text
from reporting import (
    RunStats,
    format_run_report,
    mark_daily_digest_sent,
    mark_weekly_digest_sent,
    maybe_prepare_daily_digest,
    maybe_prepare_weekly_digest,
    record_run_in_daily_state,
    record_run_in_weekly_state,
)

LOG = logging.getLogger("errol")


def configure_logging(log_level):
    logging.basicConfig(level=log_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def analyze_email(client, content, config):
    prompt = config.llm_config.prompt_template.format(content=content)
    try:
        response = client.responses.create(
            model=config.llm_config.model,
            instructions=config.llm_config.instructions,
            input=prompt,
        )
    except Exception as exc:  # noqa: BLE001
        return "", "irrelevant", 0, f"LLM request failed: {exc}"

    response_text = getattr(response, "output_text", "") or ""
    if not response_text.strip():
        return "", "irrelevant", 0, "LLM response did not include output_text."

    summary, category, score = parse_response_text(response_text)
    return summary, category, score, None


def resolve_destinations(category, score, mail_config):
    """Return (target_email, target_folder) for a classified message."""
    if category != "spam" and score >= mail_config.min_non_spam_score:
        return mail_config.forward_to, mail_config.non_spam_folder
    return mail_config.spam_forward_to, mail_config.spam_folder


def send_digest_email(report_email, payload, config):
    send_error = send_text_email(
        target_email=report_email,
        subject=payload["subject"],
        body=payload["body"],
        config=config,
    )
    if send_error:
        LOG.error("%s", send_error)
        return False
    return True


def process_daily_digest(config, run_stats, report_email):
    daily_state_file = config.report_config.daily_digest_state_file
    record_run_in_daily_state(daily_state_file, run_stats)
    daily_digest_payload = maybe_prepare_daily_digest(
        state_file=daily_state_file,
        send_hour=config.report_config.daily_digest_send_hour,
    )
    if not daily_digest_payload:
        return

    if send_digest_email(report_email, daily_digest_payload, config):
        mark_daily_digest_sent(daily_state_file, daily_digest_payload["target_day_key"])


def process_weekly_digest(config, run_stats, report_email):
    state_file = config.report_config.weekly_digest_state_file
    record_run_in_weekly_state(state_file, run_stats)
    digest_payload = maybe_prepare_weekly_digest(
        state_file=state_file,
        digest_weekday=config.report_config.weekly_digest_weekday,
    )
    if not digest_payload:
        return

    if send_digest_email(report_email, digest_payload, config):
        mark_weekly_digest_sent(state_file, digest_payload["target_week_key"])


def setup():
    args = parse_arguments()
    configure_logging(args.log_level)
    config = load_configuration(args.config_path)
    client = OpenAI(api_key=config.llm_config.api_key)
    testing_limit = args.testing
    is_testing = testing_limit is not None
    return config, client, testing_limit, is_testing


if __name__ == "__main__":
    config, client, testing_limit, is_testing = setup()

    run_errors = []
    run_stats = RunStats()
    mailbox = None

    try:
        mailbox = open_imap_connection(config)
        email_ids, fetch_ids_error = fetch_email_ids(mailbox, config.mail_config.inbox_folder)
        if fetch_ids_error:
            run_errors.append(fetch_ids_error)
        else:
            if is_testing:
                email_ids = email_ids[:testing_limit]
                LOG.info("Testing mode enabled: processing up to %s email(s).", testing_limit)

            for folder in (config.mail_config.non_spam_folder, config.mail_config.spam_folder):
                if folder:
                    folder_error = ensure_mailbox_folder(mailbox, folder)
                    if folder_error:
                        run_errors.append(folder_error)

            for index, email_id in enumerate(email_ids, start=1):
                msg, raw_message, fetch_error = fetch_email_by_id(mailbox, email_id)
                if fetch_error:
                    run_errors.append(fetch_error)
                    run_stats.errors += 1
                    continue
                if msg is None or raw_message is None:
                    run_errors.append(f"Email {index}: missing parsed message after fetch.")
                    run_stats.errors += 1
                    continue

                content = extract_text(msg)
                if not content:
                    run_errors.append(f"Email {index}: empty extracted content.")
                    run_stats.errors += 1
                    continue

                summary, category, score, analysis_error = analyze_email(client, content, config)
                if analysis_error:
                    run_errors.append(f"Email {index}: {analysis_error}")
                    run_stats.errors += 1
                    continue

                if is_testing:
                    target_email = None
                    target_folder = None
                else:
                    target_email, target_folder = resolve_destinations(
                        category, score, config.mail_config
                    )

                if target_email:
                    forward_error = forward_email(
                        raw_message=raw_message,
                        original_message=msg,
                        target_email=target_email,
                        category=category,
                        config=config,
                    )
                    if forward_error:
                        run_errors.append(f"Email {index}: {forward_error}")
                        run_stats.errors += 1
                        continue

                if target_folder:
                    move_error = move_email_to_folder(mailbox, email_id, target_folder)
                    if move_error:
                        run_errors.append(f"Email {index}: {move_error}")
                        run_stats.errors += 1
                        continue

                run_stats.processed += 1
                if category == "spam":
                    run_stats.spam += 1
                elif category == "lead":
                    run_stats.lead += 1
                    run_stats.lead_scores.append(score)
                else:
                    run_stats.irrelevant += 1

                LOG.info(
                    "(%s) | Category: %s, Score: %s, Forwarded to: %s, Moved to: %s | Summary: %s",
                    index,
                    category,
                    score,
                    target_email,
                    target_folder,
                    summary,
                )
                time.sleep(10)
    except (imaplib.IMAP4.error, OSError) as exc:
        run_errors.append(f"IMAP: connection/login failed: {exc}")
    finally:
        if mailbox is not None:
            try:
                mailbox.logout()
            except imaplib.IMAP4.error:
                pass

    if run_errors:
        LOG.error("Run completed with errors:")
        for err in run_errors:
            LOG.error("- %s", err)

    report_email = config.report_config.email_to
    run_report_text = format_run_report(run_stats)
    LOG.info("\n%s", run_report_text)

    report_frequency = config.report_config.report_frequency
    wants_daily_report = report_frequency in ("daily", "both")
    wants_weekly_digest = report_frequency in ("weekly", "both")

    if wants_daily_report and report_email:
        process_daily_digest(config, run_stats, report_email)

    if wants_weekly_digest and report_email:
        process_weekly_digest(config, run_stats, report_email)
