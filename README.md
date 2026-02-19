# Errol

Yet another plan for spam. My way of figting spam mentioned in the [speach during code::dive](https://mandross.dev/blog/spam-46-years/).

## Prerequisites

- Python 3.10+ installed
- Project dependencies installed in your environment
- A configuration file at `./assets/config.json` (or pass a custom path)

## Virtual Environment Setup

Create and activate a local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install top-level runtime dependencies (unpinned, no transitive freeze):

```bash
python3 -m pip install -r requirements.txt
```

For tests/dev tools, install:

```bash
python3 -m pip install -r requirements-dev.txt
```

## Run Once

From the project root:

```bash
python3 __main__.py -c ./assets/config.json
```

The `-c/--config-path` flag is optional and defaults to `./assets/config.json`.

Logging uses Python's standard default configuration. Use `-l/--log-level` to control verbosity:

```bash
python3 __main__.py -c ./assets/config.json --log-level INFO
python3 __main__.py -c ./assets/config.json --log-level DEBUG
```

For testing/scoring-only runs (no forwarding, no mailbox moves), use:

```bash
python3 __main__.py -c ./assets/config.json -testing=10
```

This processes at most `N` emails and logs each email's score with a short summary.

## Run Tests (pytest)

Install pytest in your active environment:

```bash
python3 -m pip install pytest
```

Run the test suite from project root:

```bash
python3 -m pytest -q
```

Current tests focus on pure logic (configuration migration/validation and email parsing helpers) so they run without live IMAP/SMTP/OpenAI access.

## Run on a Cron Schedule

Cron format is:

```text
minute hour day_of_month month day_of_week command
```

To run every `X` hours, use:

```cron
0 */X * * * cd /path/to/errol && python3 __main__.py -c ./assets/config.json >> /var/log/errol.log 2>&1
```

Example for every 6 hours:

```cron
0 */6 * * * cd /path/to/errol && python3 __main__.py -c ./assets/config.json >> /var/log/errol.log 2>&1
```

Notes:

- Use an absolute project path in `cd` so cron runs from the correct working directory.
- Redirect stdout/stderr to a log file for troubleshooting.
- `mail_config.inbox_folder` is the source mailbox folder that errol processes.
- Spam is forwarded to `mail_config.spam_forward_to` or/and moved to `mail_config.spam_folder`.
- Non-spam (`lead` and `irrelevant`) is forwarded to `mail_config.forward_to` or/and moved to `mail_config.non_spam_folder`.
