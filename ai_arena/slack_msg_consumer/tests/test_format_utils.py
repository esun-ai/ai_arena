import pytest
from src.format_utils import extract_email, email_format_match
from src.format_utils import extract_token, token_format_match
from src.format_utils import encrypt_email
from src.format_utils import check_url_valid, extract_url

email_match_cases = [
    ("<mailto:pe@gmail.com|pe@gmail.com>", True),
    ("[pe@gmail.com]", True),
    ("erwerwegsg", False),
]

email_cases = [
    ("<mailto:pe@gmail.com|pe@gmail.com>", "pe@gmail.com"),
    ("[pe@gmail.com]", "pe@gmail.com"),
    ("[pe@g-mail.com]", "pe@g-mail.com"),
]

token_match_cases = [("123455", True), ("2", False), ("", False), ("[123456]", True)]

token_cases = [("[123456]", "123456"), ("123456", "123456")]

encrypt_email_cases = [
    ("test1@gmail.com", "$2b$12$dFpIlRaZYleY/Ma.kM54du3Zbu8rFKIhkhFVu/81iPEopezWKyvwu")
]

url_valid_cases = [
    ("127.0.0.1", False),
    ("http://127.0.0.1", True),
    ("[http://127.0.0.1]", True),
]

extract_url_cases = [
    ("http://127.0.0.1", "http://127.0.0.1"),
    ("[http://127.0.0.1]", "http://127.0.0.1"),
]


@pytest.mark.parametrize("test_case, expected", email_match_cases)
def test_email_format_match(test_case, expected):
    assert email_format_match(test_case) == expected


@pytest.mark.parametrize("test_case, expected", email_cases)
def test_extract_email(test_case, expected):
    assert extract_email(test_case) == expected


@pytest.mark.parametrize("test_case, expected", token_match_cases)
def test_token_format_match(test_case, expected):
    assert token_format_match(test_case) == expected


@pytest.mark.parametrize("test_case, expected", token_cases)
def test_extract_token(test_case, expected):
    assert extract_token(test_case) == expected


# @pytest.mark.parametrize("test_case, expected", encrypt_email_cases)
# def test_encrypt_email(test_case, expected):
#     assert encrypt_email(test_case) == expected


@pytest.mark.parametrize("test_case, expected", url_valid_cases)
def test_check_url_valid(test_case, expected):
    assert check_url_valid(test_case) == expected


@pytest.mark.parametrize("test_case, expected", extract_url_cases)
def test_extract_url_cases(test_case, expected):
    assert extract_url(test_case) == expected
