"""认证(app/auth.py)的测试: 接口怎样凭令牌认出当前用户"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.auth import TOKENS_FILE_ENV, get_token_table, load_token_table
from app.domain.models import Principal, Role
from app.main import app

EMPLOYEE_A = Principal(
    user_id="user-a",
    tenant_id="tenant-1",
    role=Role.RECRUITER,
    project_ids=frozenset(["project-1"]),
)

TEST_TOKEN_TABLE = {"test-token-a": EMPLOYEE_A}


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_token_table] = lambda: TEST_TOKEN_TABLE
    yield TestClient(app)
    app.dependency_overrides.pop(get_token_table, None)


UNAUTHENTICATED_CASES = [
    pytest.param({}, id="no_authorization_header"),
    pytest.param({"Authorization": "Basic dXNlcjpwYXNz"}, id="not_a_bearer_token"),
    pytest.param({"Authorization": "Bearer unknown-token"}, id="unknown_token"),
]


@pytest.mark.parametrize("headers", UNAUTHENTICATED_CASES)
def test_request_without_valid_token_is_401(
    client: TestClient, headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Not authenticated"}


def test_valid_token_returns_its_identity(client: TestClient) -> None:
    response = client.get(
        "/api/v1/me", headers={"Authorization": "Bearer test-token-a"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "user_id": "user-a",
        "tenant_id": "tenant-1",
        "role": "recruiter",
    }


def test_demo_auth_is_off_without_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKENS_FILE_ENV, raising=False)
    assert get_token_table() == {}


def test_load_token_table_reads_identities(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    path.write_text(
        """{"tokens":{"tok-1":{
        "user_id": "user-a",
        "tenant_id": "tenant-1",
        "role": "recruiter",
        "project_ids": ["project-1"]
        }}}""",
        encoding="utf-8",
    )
    assert load_token_table(path) == {"tok-1": EMPLOYEE_A}


def test_token_file_with_unknown_role_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    path.write_text(
        """{"tokens":{"tok-1":{
        "user_id": "user-a",
        "tenant_id": "tenant-1",
        "role": "boss",
        "project_ids": []
        }}}""",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_token_table(path)
