from datetime import date, datetime, time
from uuid import UUID

import pytest
from pydantic import AnyUrl, HttpUrl

from grpcAPI.validators import (
    constrained_bytejson,
    constrained_date,
    constrained_datetime,
    constrained_json,
    constrained_time,
)
from grpcAPI.validators.inject_pydantic_validation import (
    constrained_any_url,
    constrained_dict,
    constrained_directory_path,
    constrained_email,
    constrained_file_path,
    constrained_http_url,
    constrained_ip_any,
    constrained_list,
    constrained_num,
    constrained_str,
    constrained_uuid,
)

# ———————————————————————————————————————————————————————————————————————
# STR
# ———————————————————————————————————————————————————————————————————————


def test_constrained_str_valid() -> None:
    assert (
        constrained_str("abc123", min_length=3, max_length=10, pattern=r"^[a-z0-9]+$")
        == "abc123"
    )


def test_constrained_str_invalid_min_length() -> None:
    with pytest.raises(ValueError):
        constrained_str("ab", min_length=3)


def test_constrained_str_invalid_max_length() -> None:
    with pytest.raises(ValueError):
        constrained_str("a" * 20, max_length=10)


def test_constrained_str_invalid_pattern() -> None:
    with pytest.raises(ValueError):
        constrained_str("ABC123", pattern=r"^[a-z0-9]+$")


# ———————————————————————————————————————————————————————————————————————
# NUM
# ———————————————————————————————————————————————————————————————————————


@pytest.mark.parametrize("value", [5, 5.0])
def test_constrained_num_valid(value):
    assert constrained_num(value, gt=1, lt=10, multiple_of=1) == value


def test_constrained_num_invalid_gt() -> None:
    with pytest.raises(ValueError):
        constrained_num(0, gt=1)


def test_constrained_num_invalid_lt() -> None:
    with pytest.raises(ValueError):
        constrained_num(20, lt=10)


def test_constrained_num_invalid_multiple_of() -> None:
    with pytest.raises(ValueError):
        constrained_num(7, multiple_of=2)


# ———————————————————————————————————————————————————————————————————————
# LIST
# ———————————————————————————————————————————————————————————————————————


def test_constrained_list_valid() -> None:
    assert constrained_list([1, 2, 3], min_length=1, max_length=5) == [1, 2, 3]


def test_constrained_list_too_short() -> None:
    with pytest.raises(ValueError):
        constrained_list([], min_length=1)


def test_constrained_list_too_long() -> None:
    with pytest.raises(ValueError):
        constrained_list([1, 2, 3, 4, 5, 6], max_length=5)


# ———————————————————————————————————————————————————————————————————————
# DICT
# ———————————————————————————————————————————————————————————————————————


def test_constrained_dict_valid() -> None:
    d = {"a": 1, "b": 2}
    assert constrained_dict(d, min_length=1, max_length=3) == d


def test_constrained_dict_too_short() -> None:
    with pytest.raises(ValueError):
        constrained_dict({}, min_length=1)


def test_constrained_dict_too_long() -> None:
    with pytest.raises(ValueError):
        constrained_dict({"a": 1, "b": 2, "c": 3, "d": 4}, max_length=3)


# ———————————————————————————————————————————————————————————————————————
# DATE / TIME / DATETIME
# ———————————————————————————————————————————————————————————————————————


def test_constrained_date_valid() -> None:
    assert constrained_date("2023-01-01") == date(2023, 1, 1)


def test_constrained_time_valid() -> None:
    assert constrained_time("12:34:56") == time(12, 34, 56)


def test_constrained_datetime_valid() -> None:
    assert constrained_datetime("2023-01-01T12:00:00") == datetime(2023, 1, 1, 12, 0)


def test_constrained_date_with_format() -> None:
    assert constrained_date("01/2023", fmt="%m/%Y") == date(2023, 1, 1)


# ———————————————————————————————————————————————————————————————————————
# UUID
# ———————————————————————————————————————————————————————————————————————


def test_constrained_uuid_valid() -> None:
    uuid_str = "12345678-1234-5678-1234-567812345678"
    assert constrained_uuid(uuid_str) == UUID(uuid_str)


def test_constrained_uuid_invalid() -> None:
    with pytest.raises(ValueError):
        constrained_uuid("not-a-uuid")


# ———————————————————————————————————————————————————————————————————————
# JSON / BYTEJSON
# ———————————————————————————————————————————————————————————————————————


def test_constrained_json_valid() -> None:
    json_str = '{"foo": "bar"}'
    assert constrained_json(json_str) == {"foo": "bar"}


def test_constrained_json_invalid() -> None:
    with pytest.raises(ValueError):
        constrained_json("{bad json}")


def test_constrained_bytejson_valid() -> None:
    json_bytes = b'{"foo": "bar"}'
    assert constrained_bytejson(json_bytes) == {"foo": "bar"}


def test_constrained_bytejson_invalid() -> None:
    with pytest.raises(ValueError):
        constrained_bytejson(b"{bad json}")


# ———————————————————————————————————————————————————————————————————————
# Email
# ———————————————————————————————————————————————————————————————————————


def test_constrained_email_valid() -> None:
    uuid_str = "test@tesmail.com"
    assert constrained_email(uuid_str) == uuid_str


def test_constrained_email_invalid() -> None:
    with pytest.raises(ValueError):
        constrained_email("not-a-email")


# ———————————————————————————————————————————————————————————————————————
# Url
# ———————————————————————————————————————————————————————————————————————


def test_constrained_http_url_valid() -> None:
    uuid_str = "http://teste.com"
    assert constrained_http_url(uuid_str) == HttpUrl(uuid_str)


def test_constrained_http_url_invalid() -> None:
    with pytest.raises(ValueError):
        constrained_http_url("not-a-url")


def test_constrained_any_url_valid() -> None:
    uuid_str = "file://teste.com"
    assert constrained_any_url(uuid_str) == AnyUrl(uuid_str)


def test_constrained_any_url_invalid() -> None:
    with pytest.raises(ValueError):
        constrained_any_url("not-a-url")


# IP tests


def test_constrained_ip_any_valid() -> None:
    assert str(constrained_ip_any("192.168.0.1")) == "192.168.0.1"
    assert str(constrained_ip_any("2001:db8::1")) == "2001:db8::1"


def test_constrained_ip_any_invalid() -> None:
    with pytest.raises(ValueError):
        constrained_ip_any("not-an-ip")


# DirectoryPath tests


def test_constrained_directory_path_valid(tmp_path) -> None:
    # tmp_path é um diretório criado temporariamente pelo pytest
    assert constrained_directory_path(str(tmp_path)) == tmp_path


def test_constrained_directory_path_invalid(tmp_path) -> None:
    # Criar um arquivo dentro tmp_path e passar para a validação (não é diretório)
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello")
    with pytest.raises(ValueError):
        constrained_directory_path(str(file_path))


# FilePath tests


def test_constrained_file_path_valid(tmp_path) -> None:
    file_path = tmp_path / "file.txt"
    file_path.write_text("hello")
    assert constrained_file_path(str(file_path)) == file_path


def test_constrained_file_path_invalid(tmp_path) -> None:
    with pytest.raises(ValueError):
        constrained_file_path(str(tmp_path))  # Passa um diretório, não arquivo
