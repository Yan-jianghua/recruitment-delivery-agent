"""
查看简历接口(GET /api/v1/candidates/{candidate_id}/resume)的测试

用的是app/repository.py 里的演示数据; client 来自
tests/conftest.py
门卫给出的具体原因,test_policy.py 已经测过；这里只测“原因变成
了哪个状态码"。
"""

import pytest
from fastapi.testclient import TestClient

# 两个测试令牌对应的请求头:员工甲，管理员(令牌表在tests/conftest.py里)

EMPLOYEE_A_HEADERS = {"Authorization": "Bearer test-token-a"}
ADMIN_HEADERS = {"Authorization": "Bearer test-token-admin"}


def resume_url(candidate_id: str) -> str:
    """拼出查看某个候选人简历网址"""
    return f"/api/v1/candidates/{candidate_id}/resume"


def test_allowed_returns_only_authorized_fields(client: TestClient) -> None:
    response = client.get(resume_url("cand-1"), headers=EMPLOYEE_A_HEADERS)
    assert response.status_code == 200
    assert response.json() == {
        "candidate_id": "cand-1",
        "content": "小王：Python 开发，5 年经验",
    }


STATUS_CASES = [
    pytest.param(EMPLOYEE_A_HEADERS, "cand-1", 200, id="rda_001_allowed"),
    pytest.param(EMPLOYEE_A_HEADERS, "cand-9", 404, id="rda_002_other_tenant_is_404"),
    pytest.param(EMPLOYEE_A_HEADERS, "cand-3", 403, id="rda_003_other_project_is_403"),
    pytest.param(EMPLOYEE_A_HEADERS, "cand-2", 403, id="rda_004_no_consent_is_403"),
    pytest.param(
        EMPLOYEE_A_HEADERS, "cand-4", 403, id="rda_005_withdrawn_consent_is_403"
    ),
    pytest.param(ADMIN_HEADERS, "cand-1", 403, id="rda_006_admin_without_grant_is_403"),
    pytest.param(
        ADMIN_HEADERS, "cand-5", 200, id="rda_006_admin_with_grant_is_allowed"
    ),
    pytest.param(EMPLOYEE_A_HEADERS, "cand-5", 403, id="no_grant_is_403"),
    pytest.param(EMPLOYEE_A_HEADERS, "cand-404", 404, id="missing_candidate_is_404"),
]


@pytest.mark.parametrize(("headers", "candidate_id", "expected_status"), STATUS_CASES)
def test_status_code(
    client: TestClient,
    headers: dict[str, str],
    candidate_id: str,
    expected_status: int,
) -> None:
    response = client.get(resume_url(candidate_id), headers=headers)
    assert response.status_code == expected_status


def test_other_tenant_and_missing_candidate_get_identical_404(
    client: TestClient,
) -> None:
    # RDA-002：别家公司的候选人和根本不存在的候选人，响应必须一模一样，
    # 否则对方就能从差别里猜出"别家公司有这个人"。
    other_tenant = client.get(resume_url("cand-9"), headers=EMPLOYEE_A_HEADERS)
    missing = client.get(resume_url("cand-404"), headers=EMPLOYEE_A_HEADERS)
    assert other_tenant.status_code == missing.status_code == 404
    assert other_tenant.json() == missing.json()
    assert other_tenant.headers == missing.headers


# 和"同意书已撤回"（cand-4）比较的另外三种拒绝：
# cand-3 不在员工甲的项目里，cand-2 没签同意书，cand-5 没给员工甲授权。
# 参数只有一个时，可以直接写一个普通列表；场景名字会自动用列表里的值。
@pytest.mark.parametrize("candidate_id", ["cand-3", "cand-2", "cand-5"])
def test_denials_look_the_same_as_withdrawn_consent(
    client: TestClient, candidate_id: str
) -> None:
    # 四种拒绝的 403 必须一模一样：没有权限的人，不能从响应里看出
    # 候选人有没有签同意书、是不是撤回了同意。
    withdrawn = client.get(resume_url("cand-4"), headers=EMPLOYEE_A_HEADERS)
    other = client.get(resume_url(candidate_id), headers=EMPLOYEE_A_HEADERS)
    assert other.status_code == withdrawn.status_code == 403
    assert other.json() == withdrawn.json()
    assert other.headers == withdrawn.headers


def test_request_without_token_is_401(client: TestClient) -> None:
    # 不带令牌：还没轮到门卫，认证这一关就拦下了。
    response = client.get(resume_url("cand-1"))
    assert response.status_code == 401
