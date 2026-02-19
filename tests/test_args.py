import pytest

from args import parse_arguments


def test_parse_arguments_accepts_testing_limit():
    parsed = parse_arguments(["--testing", "1"])
    assert parsed.testing == 1


def test_parse_arguments_rejects_zero_testing_limit():
    with pytest.raises(SystemExit):
        parse_arguments(["--testing", "0"])


def test_parse_arguments_rejects_negative_testing_limit():
    with pytest.raises(SystemExit):
        parse_arguments(["--testing", "-3"])
