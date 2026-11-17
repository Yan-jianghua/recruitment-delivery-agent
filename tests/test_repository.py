"""内存数据仓库(app/repository.py）的测试：查得到时返回对的记录，
查不到时返回 None.

这里直接用演示数据 DEMO_REPOSITORY,编号和 app/repository.py
里的表格一一对应
"""

import pytest

from app.domain.models import AclEntry, Action, Candidate
from app.repository import DEMO_REPOSITORY


def test_get_candidate_returns_the_one_in_the_given_tenant() -> None:
    assert DEMO_REPOSITORY.get_candidates("tenant-1", "cand-1") == Candidate(
        "cand-1", "tenant-1", "project-1"
    )


# 每一行是一种"查不到"的情况：pytest.param(公司, 候选人编号, id=场景名字)。
MISSING_CANDIDATES = [
    pytest.param("tenant-1", "cand-404", id="no_such_candidate"),
    pytest.param("tenant-1", "cand-9", id="candidate_only_in_other_tenant"),
]


@pytest.mark.parametrize(("tenant_id", "candidate_id"), MISSING_CANDIDATES)
def test_get_candidate_returns_none_when_not_found(tenant_id, candidate_id) -> None:
    assert DEMO_REPOSITORY.get_candidates(tenant_id, candidate_id) is None


def test_get_resume_returns_the_one_is_in_the_given_tenant() -> None:
    resume = DEMO_REPOSITORY.get_resume("tenant-1", "cand-1")
    assert resume is not None
    assert resume.tenant_id == "tenant-1"


def test_get_consent_returns_none_without_conset() -> None:
    assert DEMO_REPOSITORY.get_consent("tenant-1", "cand-2") is None


def test_list_acl_entries_filters_by_tenant_and_candidate() -> None:
    assert DEMO_REPOSITORY.list_acl_entries("tenant-1", "cand-1") == [
        AclEntry("tenant-1", "user-a", "cand-1", Action.READ_RESUME)
    ]


def test_list_acl_entries_returns_empty_list_when_none() -> None:
    assert DEMO_REPOSITORY.list_acl_entries("tenant-2", "cand-5") == []
