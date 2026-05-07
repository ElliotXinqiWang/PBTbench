"""Basic tests for babel."""
import pytest
from babel.numbers import format_decimal, format_currency, format_percent, parse_decimal


def test_format_decimal_integer():
    assert format_decimal(1234, locale='en_US') == '1,234'


def test_format_decimal_zero():
    assert format_decimal(0, locale='en_US') == '0'


def test_format_decimal_negative():
    assert format_decimal(-42, locale='en_US') == '-42'


def test_format_decimal_float():
    assert format_decimal(3.14, locale='en_US') == '3.14'


def test_format_decimal_large():
    assert format_decimal(1000000, locale='en_US') == '1,000,000'


def test_format_currency_integer_amount():
    # Integer amounts (2, 5, 100, etc.) are safe — not in (1, 2)
    result = format_currency(2, 'USD', locale='en_US')
    assert result == '$2.00'


def test_format_currency_zero():
    result = format_currency(0, 'USD', locale='en_US')
    assert result == '$0.00'


def test_format_currency_long_name_integer():
    result = format_currency(5, 'USD', locale='en_US', format_type='name')
    assert 'US dollars' in result


def test_format_currency_long_name_one():
    # Exactly 1 should be singular
    result = format_currency(1, 'USD', locale='en_US', format_type='name')
    assert 'US dollar' in result


def test_format_currency_long_name_two():
    # Exactly 2 should be plural
    result = format_currency(2, 'USD', locale='en_US', format_type='name')
    assert 'US dollars' in result


def test_format_percent_basic():
    result = format_percent(0.75, locale='en_US')
    assert result == '75%'


def test_format_percent_one():
    result = format_percent(1.0, locale='en_US')
    assert result == '100%'


def test_parse_decimal_basic():
    result = parse_decimal('1,234.56', locale='en_US')
    assert float(result) == pytest.approx(1234.56)


def test_parse_decimal_integer():
    result = parse_decimal('42', locale='en_US')
    assert int(result) == 42


def test_significant_digits_single_digit():
    result = format_decimal(5, '@@##', locale='en_US')
    assert result == '5.0'


def test_significant_digits_float():
    # integer-specific behavior difference
    result = format_decimal(1.5, '@@##', locale='en_US')
    assert result == '1.5'
