from datetime import datetime

from reporting import (
    RunStats,
    format_run_report,
    maybe_prepare_weekly_digest,
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
