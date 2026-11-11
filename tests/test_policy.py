"""门卫（check_resume_access）的测试。

分两组：门卫的判断结果（参数化写成一张表，名字带 rda_00x 的对应需求文档里的验收用例），
以及同意书归属（递错同意书时必须报错）。
每个测试都分三步：准备数据 → 调用门卫 → 用 assert 检查结果。
"""

# pytest 是测试工具，这里要用它的 pytest.raises（检查代码有没有抛出指定的异常）
# 和 pytest.mark.parametrize（同一个测试用多组数据各跑一次）。
import pytest

# 导入测试数据要用到的类型。名字太多时，用圆括号把导入分成多行写。
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

# ===== 测试数据 =====
# 名字全大写是 Python 里"常量"的写法习惯：定义以后不再修改。
# 同一个编号在整个文件里只代表一个人，读下面的表格时才不会搞混。

# 员工甲：在 tenant-1 公司当招聘顾问，只参与 project-1。
EMPLOYEE_A = Principal(
    user_id="user-a",
    tenant_id="tenant-1",
    role=Role.RECRUITER,
    project_ids=frozenset(["project-1"]),
)
# 项目管理员：同公司，也在 project-1。
ADMIN = Principal(
    user_id="admin-1",
    tenant_id="tenant-1",
    role=Role.PROJECT_ADMIN,
    project_ids=frozenset(["project-1"]),
)

# 候选人小王：在 tenant-1 公司的 project-1 里。
CANDIDATE_1 = Candidate(
    candidate_id="cand-1", tenant_id="tenant-1", project_id="project-1"
)
# 候选人小李：和小王同公司、同项目。
CANDIDATE_2 = Candidate(
    candidate_id="cand-2", tenant_id="tenant-1", project_id="project-1"
)
# 候选人小张：同公司，但在员工甲没参与的 project-2。
OTHER_PROJECT_CANDIDATE = Candidate(
    candidate_id="cand-3", tenant_id="tenant-1", project_id="project-2"
)
# 别家公司（tenant-2）的候选人。
OTHER_TENANT_CANDIDATE = Candidate(
    candidate_id="cand-9", tenant_id="tenant-2", project_id="project-9"
)

# 小王签的同意书：状态有效，第 1 版。
CONSENT_1 = ConsentRecord(
    candidate_id="cand-1", tenant_id="tenant-1", status=ConsentStatus.ACTIVE, version=1
)
# 小王撤回了同意书。
CONSENT_WITHDRAWN = ConsentRecord(
    candidate_id="cand-1",
    tenant_id="tenant-1",
    status=ConsentStatus.WITHDRAWN,
    version=1,
)
# 编号也是 cand-1，但属于另一家公司（两家公司可能各有一个 cand-1）。
OTHER_TENANT_CONSENT = ConsentRecord(
    candidate_id="cand-1", tenant_id="tenant-2", status=ConsentStatus.ACTIVE, version=1
)

# 授权记录：在 tenant-1 公司里，员工甲（user-a）可以查看小王（cand-1）的简历。
A_CAN_READ = AclEntry(
    tenant_id="tenant-1",
    subject_id="user-a",
    resource_id="cand-1",
    action=Action.READ_RESUME,
)
# 给另一个员工（user-b）的授权。
B_CAN_READ = AclEntry(
    tenant_id="tenant-1",
    subject_id="user-b",
    resource_id="cand-1",
    action=Action.READ_RESUME,
)
# 属于另一家公司的授权：员工、候选人、动作都对得上（两家公司可能各有一个 user-a）。
A_CAN_READ_IN_TENANT_2 = AclEntry(
    tenant_id="tenant-2",
    subject_id="user-a",
    resource_id="cand-1",
    action=Action.READ_RESUME,
)
# 员工甲查看小李（cand-2）的授权：能看小李，不代表能看小王。
A_CAN_READ_CANDIDATE_2 = AclEntry(
    tenant_id="tenant-1",
    subject_id="user-a",
    resource_id="cand-2",
    action=Action.READ_RESUME,
)


# ===== 第一组：门卫的判断结果 =====
# 每一行是一个场景：pytest.param(谁来看, 看谁, 同意书, 授权记录, 期望的原因, id=场景名字)。
# fmt: off 和 fmt: on 告诉 Ruff：这一段是手工排好的表格，格式化时不要改动，保持一行一个场景。
# fmt: off
DECISION_CASES = [
    # RDA-001：同公司、同项目、有授权、同意书有效 → 放行。
    pytest.param(EMPLOYEE_A, CANDIDATE_1, CONSENT_1, [A_CAN_READ], Reason.ALLOWED, id="rda_001_same_tenant_same_project_is_allowed"),
    # RDA-002：候选人在别的公司 → 必须是"查无此人"，不能暴露对方存在。
    # 同意书传 None、授权传空列表：如果门卫没有先查公司，就会返回别的原因。
    pytest.param(EMPLOYEE_A, OTHER_TENANT_CANDIDATE, None, [], Reason.NOT_FOUND, id="rda_002_other_tenant_is_hidden_as_not_found"),
    # RDA-003：同公司，但不在员工甲的项目里 → 拒绝。
    # 同意书、授权都不给：如果门卫没有先查项目，就会返回 NO_GRANT。
    pytest.param(EMPLOYEE_A, OTHER_PROJECT_CANDIDATE, None, [], Reason.PROJECT_MISMATCH, id="rda_003_same_tenant_other_project_is_not_allowed"),
    # RDA-004：没有同意书 → 拒绝。授权要给对，门卫才能走到同意书这一关。
    pytest.param(EMPLOYEE_A, CANDIDATE_1, None, [A_CAN_READ], Reason.NO_CONSENT, id="rda_004_no_consent_is_denied"),
    # RDA-005：同意书已撤回 → 拒绝。"有同意书"不等于"同意书有效"。
    pytest.param(EMPLOYEE_A, CANDIDATE_1, CONSENT_WITHDRAWN, [A_CAN_READ], Reason.CONSENT_WITHDRAWN, id="rda_005_withdrawn_consent_is_denied"),
    # RDA-006：管理员没有自己的授权 → 拒绝，管理员没有例外。
    pytest.param(ADMIN, CANDIDATE_1, CONSENT_1, [A_CAN_READ], Reason.NO_GRANT, id="rda_006_admin_without_own_grant_is_denied"),
    # 授权列表是空的 → 拒绝。同意书传 None：如果门卫没有先查授权，就会返回 NO_CONSENT。
    pytest.param(EMPLOYEE_A, CANDIDATE_1, None, [], Reason.NO_GRANT, id="no_grant_is_denied"),
    # 甲的授权排在第二条：门卫必须把列表看完，不能只看第一条就下结论。
    pytest.param(EMPLOYEE_A, CANDIDATE_1, CONSENT_1, [B_CAN_READ, A_CAN_READ], Reason.ALLOWED, id="grant_in_second_entry_is_allowed"),
    # 授权属于另一家公司 → 不算数。
    pytest.param(EMPLOYEE_A, CANDIDATE_1, CONSENT_1, [A_CAN_READ_IN_TENANT_2], Reason.NO_GRANT, id="grant_from_other_tenant_is_denied"),
    # 授权是给别的候选人的 → 不算数。
    pytest.param(EMPLOYEE_A, CANDIDATE_1, CONSENT_1, [A_CAN_READ_CANDIDATE_2], Reason.NO_GRANT, id="grant_for_other_candidate_is_denied"),
]
# fmt: on


# parametrize 的第一个参数：测试函数要接收的参数名；
# 第二个参数：上面那张表，pytest 会用表里的每一行各跑一次测试。
@pytest.mark.parametrize(
    ("principal", "candidate", "consent", "acl_entries", "expected"), DECISION_CASES
)
def test_check_resume_access(
    principal: Principal,
    candidate: Candidate,
    consent: ConsentRecord | None,
    acl_entries: list[AclEntry],
    expected: Reason,
) -> None:
    decision = check_resume_access(principal, candidate, consent, acl_entries)
    # 先查原因：失败时能直接看出卡在了哪一关。
    assert decision.reason == expected
    # 只有原因是 ALLOWED 才放行。括号里比较的结果是 True 或 False，
    # 再用 is 要求 allowed 正好是这个布尔值。
    assert decision.allowed is (expected == Reason.ALLOWED)


# ===== 第二组：同意书归属 =====
# 递进来的同意书不属于这个候选人，说明调用门卫的代码有 bug，门卫必须直接报错。
# 每一行：pytest.param(看谁, 同意书, id=场景名字)。
OWNERSHIP_CASES = [
    # 要看小李，递进来的却是小王的同意书。
    pytest.param(CANDIDATE_2, CONSENT_1, id="consent_of_another_candidate"),
    # 编号对得上，但同意书属于另一家公司。
    pytest.param(CANDIDATE_1, OTHER_TENANT_CONSENT, id="consent_from_other_tenant"),
]


@pytest.mark.parametrize(("candidate", "consent"), OWNERSHIP_CASES)
def test_consent_not_belonging_to_candidate_raises_error(
    candidate: Candidate, consent: ConsentRecord
) -> None:
    # with pytest.raises(ValueError)：缩进里的代码必须抛出 ValueError，抛了测试才通过；
    # 没抛就失败，报 DID NOT RAISE ValueError。
    with pytest.raises(ValueError):
        check_resume_access(EMPLOYEE_A, candidate, consent, [])
