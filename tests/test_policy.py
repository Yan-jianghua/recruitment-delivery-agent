"""门卫（check_resume_access）的测试。

分三组：需求文档里的验收用例（函数名带 rda_00x）、授权记录的细节、同意书归属。
每个测试都分三步：准备数据 → 调用门卫 → 用 assert 检查结果。
"""

# 导入测试数据要用到的类型。名字太多时，用圆括号把导入分成多行写。
# pytest 是测试工具，这里要用它的 pytest.raises（检查代码有没有抛出指定的异常）。
import pytest

from app.domain.models import (
    AclEntry,
    Action,
    Candidate,
    ConsentRecord,
    ConsentStatus,
    Principal,
    Reason,
    Role,
)

# 测试只需要通过门卫的入口 check_resume_access 来测。
from app.domain.policy import check_resume_access

# 下面是几个测试共用的数据。名字全大写是 Python 里"常量"的写法习惯：定义以后不再修改。
# 对应故事里的人物：员工甲 = EMPLOYEE_A，候选人小王 = CANDIDATE_1。

# 员工甲：在 tenant-1 公司当招聘顾问，只参与 project-1。
EMPLOYEE_A = Principal(
    user_id="user-a",
    tenant_id="tenant-1",
    role=Role.RECRUITER,
    project_ids=frozenset(["project-1"]),
)
# 候选人小王：在 tenant-1 公司的 project-1 里。
CANDIDATE_1 = Candidate(
    candidate_id="cand-1",
    tenant_id="tenant-1",
    project_id="project-1",
)

# 小王签的同意书：状态有效，第 1 版。
CONSENT_1 = ConsentRecord(
    candidate_id="cand-1", tenant_id="tenant-1", status=ConsentStatus.ACTIVE, version=1
)
# 授权记录：在 tenant-1 公司里，员工甲（user-a）可以查看小王（cand-1）的简历。
A_CAN_READ = AclEntry(
    tenant_id="tenant-1",
    subject_id="user-a",
    resource_id="cand-1",
    action=Action.READ_RESUME,
)


# ===== 第一组：需求文档里的验收用例（RDA-001 ~ RDA-006）=====


# RDA-001：同公司、同项目、有授权、同意书有效 → 应该放行。
def test_rda_001_same_tenant_same_project_is_allowed() -> None:
    decision = check_resume_access(EMPLOYEE_A, CANDIDATE_1, CONSENT_1, [A_CAN_READ])
    # is True：结果必须正好是布尔值 True。
    assert decision.allowed is True
    # 只看 allowed 还不够，还要确认原因是 ALLOWED。
    assert decision.reason == Reason.ALLOWED


# RDA-002：候选人在别的公司 → 拒绝，而且原因必须是"查无此人"，不能暴露对方存在。
# 同意书传 None、授权传空列表：如果门卫没有先查公司，就会返回别的原因，测试会失败。
def test_rda_002_other_tenant_is_hidden_as_not_found() -> None:
    other_tenant_candidate = Candidate(
        candidate_id="cand-9", tenant_id="tenant-2", project_id="project-9"
    )
    decision = check_resume_access(EMPLOYEE_A, other_tenant_candidate, None, [])
    assert decision.allowed is False
    assert decision.reason == Reason.NOT_FOUND


# RDA-003：同公司，但候选人在员工甲没参与的项目里 → 拒绝。
# 同意书、授权都不给：如果门卫没有先查项目，就会返回 NO_GRANT，测试会失败。
def test_rda_003_same_tenant_other_project_is_not_allowed() -> None:
    # 另一个同公司的候选人（cand-2），在员工甲没参与的 project-2。
    other_project_candidate = Candidate(
        candidate_id="cand-2", tenant_id="tenant-1", project_id="project-2"
    )
    decision = check_resume_access(EMPLOYEE_A, other_project_candidate, None, [])
    assert decision.allowed is False
    assert decision.reason == Reason.PROJECT_MISMATCH


# RDA-004：小王没有同意书 → 拒绝。
# 授权要给对（A_CAN_READ），门卫才能走到"同意书"这一关。
def test_rda_004_no_consent_is_denied() -> None:
    decision = check_resume_access(EMPLOYEE_A, CANDIDATE_1, None, [A_CAN_READ])
    assert decision.allowed is False
    assert decision.reason == Reason.NO_CONSENT


# RDA-005：小王撤回了同意书 → 拒绝。
# 撤回的同意书也是一条记录："有同意书"不等于"同意书有效"，门卫必须看状态。
def test_rda_005_withdrawn_consent_is_denied() -> None:
    consent_withdrawn = ConsentRecord(
        candidate_id="cand-1",
        tenant_id="tenant-1",
        status=ConsentStatus.WITHDRAWN,
        version=1,
    )
    decision = check_resume_access(
        EMPLOYEE_A, CANDIDATE_1, consent_withdrawn, [A_CAN_READ]
    )
    assert decision.allowed is False
    assert decision.reason == Reason.CONSENT_WITHDRAWN


# RDA-006：项目管理员也要有自己的授权记录，不能因为是管理员就自动放行。
def test_rda_006_admin_without_own_grant_is_denied() -> None:
    # 同公司、也在 project-1 的项目管理员。
    admin = Principal(
        user_id="admin-1",
        tenant_id="tenant-1",
        role=Role.PROJECT_ADMIN,
        project_ids=frozenset(["project-1"]),
    )
    # 授权列表里只有给员工甲的那一条，没有给管理员本人的。
    decision = check_resume_access(admin, CANDIDATE_1, CONSENT_1, [A_CAN_READ])
    assert decision.allowed is False
    assert decision.reason == Reason.NO_GRANT


# ===== 第二组：授权记录的细节 =====
# 只有"公司、员工、候选人、动作"四项全部对上的那一条才算授权。
# 除了第一个，这组测试都给有效地同意书 CONSENT_1，只让授权这一项出问题。


# 授权列表是空的 → 拒绝。
# 同意书传 None：如果门卫没有先查授权，就会返回 NO_CONSENT，测试会失败。
def test_no_grant_is_denied() -> None:
    decision = check_resume_access(EMPLOYEE_A, CANDIDATE_1, None, [])
    assert decision.allowed is False
    assert decision.reason == Reason.NO_GRANT


# 甲的授权排在列表第二条，前面是别人的：门卫必须把列表看完，不能只看第一条就下结论。
def test_grant_in_second_entry_is_allowed() -> None:
    # 给另一个员工（user-b）的授权，排在前面。
    grant_for_someone_else = AclEntry(
        tenant_id="tenant-1",
        subject_id="user-b",
        resource_id="cand-1",
        action=Action.READ_RESUME,
    )
    decision = check_resume_access(
        EMPLOYEE_A, CANDIDATE_1, CONSENT_1, [grant_for_someone_else, A_CAN_READ]
    )
    assert decision.allowed is True
    assert decision.reason == Reason.ALLOWED


# 授权记录属于另一家公司：员工、候选人、动作都对得上也不算数
# （两家公司可能各有一个编号叫 user-a 的员工）。
def test_grant_from_other_tenant_is_denied() -> None:
    grant_in_other_tenant = AclEntry(
        tenant_id="tenant-2",
        subject_id="user-a",
        resource_id="cand-1",
        action=Action.READ_RESUME,
    )
    decision = check_resume_access(
        EMPLOYEE_A, CANDIDATE_1, CONSENT_1, [grant_in_other_tenant]
    )
    assert decision.allowed is False
    assert decision.reason == Reason.NO_GRANT


# 授权是给别的候选人（cand-2）的：甲能看别人，不代表能看小王。
def test_grant_for_other_candidate_is_denied() -> None:
    grant_for_candidate_2 = AclEntry(
        tenant_id="tenant-1",
        subject_id="user-a",
        resource_id="cand-2",
        action=Action.READ_RESUME,
    )
    decision = check_resume_access(
        EMPLOYEE_A, CANDIDATE_1, CONSENT_1, [grant_for_candidate_2]
    )
    assert decision.allowed is False
    assert decision.reason == Reason.NO_GRANT


# ===== 第三组：同意书归属 =====
# 递进来的同意书不属于这个候选人，说明调用门卫的代码有 bug，门卫必须直接报错。


# 递进来的是别的候选人的同意书（要看小李，递进来的却是小王的）
# → 这是调用方的 bug，门卫必须抛 ValueError。
def test_consent_of_another_candidate_raises_error() -> None:
    # 小李：和小王同公司、同项目。
    candidate_2 = Candidate(
        candidate_id="cand-2", tenant_id="tenant-1", project_id="project-1"
    )
    # 小王的有效同意书。
    consent_of_candidate_1 = ConsentRecord(
        candidate_id="cand-1",
        tenant_id="tenant-1",
        status=ConsentStatus.ACTIVE,
        version=1,
    )
    # with pytest.raises(ValueError)：缩进里的代码必须抛出 ValueError，抛了测试才通过；
    # 没抛就失败，报 DID NOT RAISE ValueError。
    # 不用把结果存进 decision，因为我们期望它根本不会返回。
    with pytest.raises(ValueError):
        check_resume_access(EMPLOYEE_A, candidate_2, consent_of_candidate_1, [])


# 同意书编号对得上，但属于另一家公司（两家公司可能各有一个 cand-1）
# → 同样是调用方的 bug，必须抛 ValueError。
def test_consent_from_other_tenant_raises_error() -> None:
    other_tenant_consent = ConsentRecord(
        candidate_id="cand-1",
        tenant_id="tenant-2",
        status=ConsentStatus.ACTIVE,
        version=1,
    )
    with pytest.raises(ValueError):
        check_resume_access(EMPLOYEE_A, CANDIDATE_1, other_tenant_consent, [])
