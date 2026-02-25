from datetime import datetime

from reporting import (
    RunStats,
    format_run_report,
    mark_daily_digest_sent,
    maybe_prepare_daily_digest,
    maybe_prepare_weekly_digest,
    record_run_in_daily_state,
    record_run_in_weekly_state,
)


def test_format_run_report_contains_ascii_sections():
    stats = RunStats(
        processed=3,
        spam=1,
        irrelevant=1,
        lead=1,
        errors=0,
        lead_scores=[8],
    )
    report = format_run_report(stats)
    assert "ERROL RUN REPORT" in report
    assert "Processed emails : 3" in report
    assert "Avg lead score   : 8.00" in report
    assert " 8: # (1)" in report


def test_weekly_digest_prepared_only_on_digest_day(tmp_path):
    state_file = str(tmp_path / "weekly_state.json")
    run_date = datetime(2026, 2, 16, 10, 0, 0)  # Monday
    stats = RunStats(processed=2, spam=1, irrelevant=0, lead=1, errors=0, lead_scores=[7])

    record_run_in_weekly_state(state_file, stats, now=run_date)

    # Tuesday should not produce the digest when digest weekday is Monday.
    no_digest = maybe_prepare_weekly_digest(
        state_file=state_file,
        digest_weekday=0,
        now=datetime(2026, 2, 17, 10, 0, 0),
    )
    assert no_digest is None


def test_weekly_digest_targets_previous_week(tmp_path):
    state_file = str(tmp_path / "weekly_state.json")
    previous_monday = datetime(2026, 2, 16, 10, 0, 0)
    stats = RunStats(processed=4, spam=1, irrelevant=1, lead=2, errors=0, lead_scores=[6, 9])
    record_run_in_weekly_state(state_file, stats, now=previous_monday)

    digest = maybe_prepare_weekly_digest(
        state_file=state_file,
        digest_weekday=0,
        now=datetime(2026, 2, 23, 9, 0, 0),
    )

    assert digest is not None
    assert "Errol weekly digest" in digest["subject"]
    assert "Processed emails  : 4" in digest["body"]


def test_daily_digest_aggregates_multiple_runs_and_targets_previous_day(tmp_path):
    state_file = str(tmp_path / "daily_state.json")
    day_run_1 = datetime(2026, 2, 24, 8, 0, 0)
    day_run_2 = datetime(2026, 2, 24, 16, 0, 0)

    record_run_in_daily_state(
        state_file,
        RunStats(processed=2, spam=1, irrelevant=0, lead=1, errors=0, lead_scores=[7]),
        now=day_run_1,
    )
    record_run_in_daily_state(
        state_file,
        RunStats(processed=3, spam=1, irrelevant=1, lead=1, errors=1, lead_scores=[9]),
        now=day_run_2,
    )

    digest = maybe_prepare_daily_digest(
        state_file=state_file,
        send_hour=8,
        now=datetime(2026, 2, 25, 8, 0, 0),
    )

    assert digest is not None
    assert "Errol daily digest (2026-02-24)" == digest["subject"]
    assert "Processed emails  : 5" in digest["body"]
    assert "Spam              : 2" in digest["body"]
    assert "Leads             : 2" in digest["body"]


def test_daily_digest_not_sent_twice_for_same_day(tmp_path):
    state_file = str(tmp_path / "daily_state.json")
    record_run_in_daily_state(
        state_file,
        RunStats(processed=1, spam=0, irrelevant=1, lead=0, errors=0, lead_scores=[]),
        now=datetime(2026, 2, 24, 12, 0, 0),
    )

    digest = maybe_prepare_daily_digest(
        state_file=state_file,
        send_hour=6,
        now=datetime(2026, 2, 25, 6, 0, 0),
    )
    assert digest is not None
    mark_daily_digest_sent(state_file, digest["target_day_key"])

    second_attempt = maybe_prepare_daily_digest(
        state_file=state_file,
        send_hour=6,
        now=datetime(2026, 2, 25, 10, 0, 0),
    )
    assert second_attempt is None


def test_daily_digest_waits_for_send_hour(tmp_path):
    state_file = str(tmp_path / "daily_state.json")
    record_run_in_daily_state(
        state_file,
        RunStats(processed=1, spam=0, irrelevant=1, lead=0, errors=0, lead_scores=[]),
        now=datetime(2026, 2, 24, 12, 0, 0),
    )

    digest = maybe_prepare_daily_digest(
        state_file=state_file,
        send_hour=8,
        now=datetime(2026, 2, 25, 7, 59, 0),
    )
    assert digest is None
