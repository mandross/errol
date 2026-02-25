import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class RunStats:
    processed: int = 0
    spam: int = 0
    irrelevant: int = 0
    lead: int = 0
    errors: int = 0
    lead_scores: list[int] = field(default_factory=list)


def _empty_week_stats():
    return {
        "processed": 0,
        "spam": 0,
        "irrelevant": 0,
        "lead": 0,
        "errors": 0,
        "lead_scores_hist": {str(score): 0 for score in range(1, 11)},
    }


def _build_score_histogram(lead_scores):
    histogram = {score: 0 for score in range(1, 11)}
    for score in lead_scores:
        if 1 <= score <= 10:
            histogram[score] += 1
    return histogram


def _format_histogram_lines(histogram):
    lines = []
    for score in range(1, 11):
        count = histogram.get(score, 0)
        bar = "#" * min(count, 40)
        if count > 40:
            bar += "+"
        lines.append(f"{score:>2}: {bar} ({count})")
    return lines


def _average_score(lead_scores):
    if not lead_scores:
        return 0.0
    return sum(lead_scores) / len(lead_scores)


def format_run_report(stats):
    histogram = _build_score_histogram(stats.lead_scores)
    lines = [
        "ERROL RUN REPORT",
        "================",
        f"Processed emails : {stats.processed}",
        f"Spam             : {stats.spam}",
        f"Irrelevant       : {stats.irrelevant}",
        f"Leads            : {stats.lead}",
        f"Errors           : {stats.errors}",
        f"Avg lead score   : {_average_score(stats.lead_scores):.2f}",
        "",
        "Lead score histogram (1-10)",
    ]
    lines.extend(_format_histogram_lines(histogram))
    return "\n".join(lines)


def _iso_week_key(when):
    iso_year, iso_week, _ = when.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _iso_day_key(when):
    return when.strftime("%Y-%m-%d")


def _load_daily_state(state_file):
    state_path = Path(state_file)
    if not state_path.exists():
        return {"days": {}, "last_sent_day": None}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"days": {}, "last_sent_day": None}


def _save_daily_state(state_file, state):
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def record_run_in_daily_state(state_file, stats, now=None):
    now = now or datetime.now()
    day_key = _iso_day_key(now)
    state = _load_daily_state(state_file)
    days = state.setdefault("days", {})
    day_stats = days.setdefault(day_key, _empty_week_stats())

    day_stats["processed"] += stats.processed
    day_stats["spam"] += stats.spam
    day_stats["irrelevant"] += stats.irrelevant
    day_stats["lead"] += stats.lead
    day_stats["errors"] += stats.errors

    hist = day_stats.setdefault("lead_scores_hist", {str(score): 0 for score in range(1, 11)})
    for score in stats.lead_scores:
        if 1 <= score <= 10:
            hist[str(score)] += 1

    _save_daily_state(state_file, state)
    return state


def maybe_prepare_daily_digest(state_file, send_hour, now=None):
    now = now or datetime.now()
    if not 0 <= send_hour <= 23:
        return None
    if now.hour < send_hour:
        return None

    state = _load_daily_state(state_file)
    target_day_key = _iso_day_key(now - timedelta(days=1))
    if state.get("last_sent_day") == target_day_key:
        return None

    day_stats = state.get("days", {}).get(target_day_key, _empty_week_stats())
    subject = f"Errol daily digest ({target_day_key})"
    body = format_daily_digest(target_day_key, day_stats)
    return {
        "subject": subject,
        "body": body,
        "target_day_key": target_day_key,
    }


def mark_daily_digest_sent(state_file, day_key):
    state = _load_daily_state(state_file)
    state["last_sent_day"] = day_key
    _save_daily_state(state_file, state)


def format_daily_digest(day_key, day_stats):
    histogram = {score: 0 for score in range(1, 11)}
    raw_hist = day_stats.get("lead_scores_hist", {})
    for score in range(1, 11):
        histogram[score] = int(raw_hist.get(str(score), 0))

    lead_scores_count = sum(histogram.values())
    lead_score_sum = sum(score * count for score, count in histogram.items())
    avg_lead_score = (lead_score_sum / lead_scores_count) if lead_scores_count else 0.0

    lines = [
        "ERROL DAILY DIGEST",
        "==================",
        f"Day               : {day_key}",
        f"Processed emails  : {day_stats.get('processed', 0)}",
        f"Spam              : {day_stats.get('spam', 0)}",
        f"Irrelevant        : {day_stats.get('irrelevant', 0)}",
        f"Leads             : {day_stats.get('lead', 0)}",
        f"Errors            : {day_stats.get('errors', 0)}",
        f"Avg lead score    : {avg_lead_score:.2f}",
        "",
        "Lead score histogram (1-10)",
    ]
    lines.extend(_format_histogram_lines(histogram))
    return "\n".join(lines)


def _load_weekly_state(state_file):
    state_path = Path(state_file)
    if not state_path.exists():
        return {"weeks": {}, "last_sent_week": None}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"weeks": {}, "last_sent_week": None}


def _save_weekly_state(state_file, state):
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def record_run_in_weekly_state(state_file, stats, now=None):
    now = now or datetime.now()
    week_key = _iso_week_key(now)
    state = _load_weekly_state(state_file)
    weeks = state.setdefault("weeks", {})
    week_stats = weeks.setdefault(week_key, _empty_week_stats())

    week_stats["processed"] += stats.processed
    week_stats["spam"] += stats.spam
    week_stats["irrelevant"] += stats.irrelevant
    week_stats["lead"] += stats.lead
    week_stats["errors"] += stats.errors

    hist = week_stats.setdefault("lead_scores_hist", {str(score): 0 for score in range(1, 11)})
    for score in stats.lead_scores:
        if 1 <= score <= 10:
            hist[str(score)] += 1

    _save_weekly_state(state_file, state)
    return state


def maybe_prepare_weekly_digest(state_file, digest_weekday, now=None):
    now = now or datetime.now()
    if now.weekday() != digest_weekday:
        return None

    state = _load_weekly_state(state_file)
    target_week_key = _iso_week_key(now - timedelta(days=7))
    if state.get("last_sent_week") == target_week_key:
        return None

    week_stats = state.get("weeks", {}).get(target_week_key, _empty_week_stats())
    subject = f"Errol weekly digest ({target_week_key})"
    body = format_weekly_digest(target_week_key, week_stats)
    return {
        "subject": subject,
        "body": body,
        "target_week_key": target_week_key,
    }


def mark_weekly_digest_sent(state_file, week_key):
    state = _load_weekly_state(state_file)
    state["last_sent_week"] = week_key
    _save_weekly_state(state_file, state)


def format_weekly_digest(week_key, week_stats):
    histogram = {score: 0 for score in range(1, 11)}
    raw_hist = week_stats.get("lead_scores_hist", {})
    for score in range(1, 11):
        histogram[score] = int(raw_hist.get(str(score), 0))

    lead_scores_count = sum(histogram.values())
    lead_score_sum = sum(score * count for score, count in histogram.items())
    avg_lead_score = (lead_score_sum / lead_scores_count) if lead_scores_count else 0.0

    lines = [
        "ERROL WEEKLY DIGEST",
        "===================",
        f"Week              : {week_key}",
        f"Processed emails  : {week_stats.get('processed', 0)}",
        f"Spam              : {week_stats.get('spam', 0)}",
        f"Irrelevant        : {week_stats.get('irrelevant', 0)}",
        f"Leads             : {week_stats.get('lead', 0)}",
        f"Errors            : {week_stats.get('errors', 0)}",
        f"Avg lead score    : {avg_lead_score:.2f}",
        "",
        "Lead score histogram (1-10)",
    ]
    lines.extend(_format_histogram_lines(histogram))
    return "\n".join(lines)
