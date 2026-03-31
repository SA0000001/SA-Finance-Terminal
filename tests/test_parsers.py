from domain.parsers import parse_number


def test_parse_number_handles_currency_and_sign():
    assert parse_number("+123.45M $") == 123.45


def test_parse_number_handles_european_decimal():
    assert parse_number("%7,25") == 7.25


def test_parse_number_handles_parentheses_as_negative():
    assert parse_number("(1,234.50)") == -1234.5


def test_parse_number_returns_none_for_invalid_values():
    assert parse_number("not-a-number") is None
    assert parse_number(None) is None
