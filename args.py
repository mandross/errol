import argparse


def _positive_int(value):
    parsed_value = int(value)
    if parsed_value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed_value


def parse_arguments(argv=None):
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "-c",
        "--config-path",
        help="Path to configuration file",
        default="./assets/config.json",
    )
    argument_parser.add_argument(
        "-t",
        "--testing",
        type=_positive_int,
        metavar="N",
        help=(
            "Testing mode: process at most N emails and log summary."
        ),
    )
    argument_parser.add_argument(
        "-l",
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Python logging level (default: INFO).",
    )
    return argument_parser.parse_args(argv)
