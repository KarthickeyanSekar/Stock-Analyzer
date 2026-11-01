from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from stock_analyzer.domain.users.invite import (
    CODE_ALPHABET,
    InvalidInviteError,
    InviteCode,
    generate_code,
    normalise,
)
from stock_analyzer.domain.users.user import Role

NOW = datetime(2026, 11, 1, tzinfo=UTC)


def invite(**changes: object) -> InviteCode:
    values: dict[str, object] = {
        "id": uuid4(),
        "code": "SA-ABCD-EFGH",
        "created_by": None,
        "role_granted": Role.USER,
        "max_uses": 1,
        "expires_at": NOW + timedelta(days=7),
    } | changes
    return InviteCode(**values)  # type: ignore[arg-type]


def test_code_format_and_alphabet() -> None:
    code = generate_code()

    assert len(code) == 12 and code.startswith("SA-") and code[7] == "-"
    assert set(code[3:7] + code[8:]) <= set(CODE_ALPHABET)
    assert "0" not in CODE_ALPHABET and "O" not in CODE_ALPHABET
    assert normalise("  sa-abcd-efgh ") == "SA-ABCD-EFGH"


def test_redeem_counts_uses() -> None:
    code = invite(max_uses=2)
    code.redeem(NOW)
    code.redeem(NOW)

    with pytest.raises(InvalidInviteError, match="already been used"):
        code.redeem(NOW)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"is_revoked": True}, "revoked"),
        ({"expires_at": NOW}, "expired"),
        ({"used_count": 1}, "already been used"),
    ],
)
def test_unusable_codes(changes: dict[str, object], message: str) -> None:
    with pytest.raises(InvalidInviteError, match=message):
        invite(**changes).check(NOW)
