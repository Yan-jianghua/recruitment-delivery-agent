"""内存数据仓库：把“查数据”的代码包在一个类里。
接口只调用仓库的方法拿数据，不关心数据存在哪里。现在
数据放在内存里的列表中；
后面换成数据库，只要新参何苦提供同样的方法，接口代码一行都不用改。
每个查询都要带上呢个tenant_id ：两家公司可能各有一个编号叫cand-1的候选人
"""

from dataclasses import dataclass

from app.domain.models import (
    AclEntry,
    Action,
    Candidate,
    ConsentRecord,
    ConsentStatus,
    Resume,
)


@dataclass
class InMemoryRepository:
    """把数据放在内存列表里的仓库。服务重启后，数据回恢复成下面
    的演示数据"""

    candidates: list[Candidate]
    resumes: list[Resume]
    consents: list[ConsentRecord]
    acl_entries: list[AclEntry]

    def get_candidates(self, tenant_id: str, candidate_id: str) -> Candidate | None:
        """按公司和编号找候选人。找不到就返回None"""
        for candidate in self.candidates:
            if (
                candidate.tenant_id == tenant_id
                and candidate.candidate_id == candidate_id
            ):
                return candidate
        return None

    def get_resume(self, tenant_id: str, candidate_id: str) -> Resume | None:
        """按公司和候选人编号找简历。找不到就返回 None。"""
        for resume in self.resumes:
            if resume.tenant_id == tenant_id and resume.candidate_id == candidate_id:
                return resume
        return None

    def get_consent(self, tenant_id: str, candidate_id: str) -> ConsentRecord | None:
        """按公司和候选人编号找同意书。候选人没签过，就返回None"""
        for consent in self.consents:
            if consent.tenant_id == tenant_id and consent.candidate_id == candidate_id:
                return consent
        return None

    def list_acl_entries(
        self, tenant_id: str, candidate_id: str
    ) -> list[AclEntry] | None:
        """找出这家公司里、和这个候选人有关的全部授权记录。一条都没有就返回空列表。"""
        result: list[AclEntry] = []
        for entry in self.acl_entries:
            if entry.tenant_id == tenant_id and entry.resource_id == candidate_id:
                result.append(entry)
        return result


# ===== 演示数据（全部是编出来的）=====
# 这些数据同时也是接口测试用的数据：改动这里时，要同步检查 tests 里的测试。
# tenant-1 的员工甲（user-a）和管理员（admin-1）都只参与 project-1，
# 和 local/demo_tokens.json 里的两个演示令牌对应。

# 候选人：Candidate(候选人编号, 公司, 项目)
DEMO_CANDIDATES = [
    Candidate("cand-1", "tenant-2", "project-9"),  # 别家公司也有一个 cand-1
    Candidate("cand-9", "tenant-2", "project-9"),  # 只有别家公司有（RDA-002）
    Candidate("cand-1", "tenant-1", "project-1"),  # 员工甲能看（RDA-001）
    Candidate("cand-2", "tenant-1", "project-1"),  # 没签同意书（RDA-004）
    Candidate("cand-3", "tenant-1", "project-2"),  # 员工甲没参与这个项目（RDA-003）
    Candidate("cand-4", "tenant-1", "project-1"),  # 同意书已撤回（RDA-005）
    Candidate("cand-5", "tenant-1", "project-1"),  # 只有管理员有授权（RDA-006）
]

# 简历：Resume(候选人编号, 公司, 简历正文)
DEMO_RESUMES = [
    Resume("cand-1", "tenant-2", "别家公司的 cand-1：Java 开发，3 年经验"),
    Resume("cand-9", "tenant-2", "别家公司的 cand-9：测试工程师，2 年经验"),
    Resume("cand-1", "tenant-1", "小王：Python 开发，5 年经验"),
    Resume("cand-2", "tenant-1", "小李：前端开发，4 年经验"),
    Resume("cand-3", "tenant-1", "小张：数据分析，3 年经验"),
    Resume("cand-4", "tenant-1", "小赵：运维工程师，6 年经验"),
    Resume("cand-5", "tenant-1", "小孙：产品经理，7 年经验"),
]

# 同意书：ConsentRecord(候选人编号, 公司, 状态, 版本)。cand-2 没签，所以没有它的记录。
DEMO_CONSENTS = [
    ConsentRecord("cand-9", "tenant-2", ConsentStatus.ACTIVE, 1),
    ConsentRecord("cand-1", "tenant-1", ConsentStatus.ACTIVE, 1),
    ConsentRecord("cand-3", "tenant-1", ConsentStatus.ACTIVE, 1),
    ConsentRecord("cand-4", "tenant-1", ConsentStatus.WITHDRAWN, 1),
    ConsentRecord("cand-5", "tenant-1", ConsentStatus.ACTIVE, 1),
]

# 授权记录：AclEntry(公司, 被授权的员工, 候选人编号, 动作)
DEMO_ACL_ENTRIES = [
    AclEntry("tenant-2", "user-a", "cand-9", Action.READ_RESUME),  # 别家公司也有 user-a
    AclEntry("tenant-1", "user-a", "cand-1", Action.READ_RESUME),
    AclEntry("tenant-1", "user-a", "cand-2", Action.READ_RESUME),
    AclEntry("tenant-1", "user-a", "cand-3", Action.READ_RESUME),
    AclEntry("tenant-1", "user-a", "cand-4", Action.READ_RESUME),
    AclEntry("tenant-1", "admin-1", "cand-5", Action.READ_RESUME),
]

# 演示用的仓库：程序启动时创建一次，所有请求共用这一个。
DEMO_REPOSITORY = InMemoryRepository(
    candidates=DEMO_CANDIDATES,
    resumes=DEMO_RESUMES,
    consents=DEMO_CONSENTS,
    acl_entries=DEMO_ACL_ENTRIES,
)


def get_repository() -> InMemoryRepository:
    """依赖:接口要查数据时，就声明依赖它
    测试时可以用 dependency_overrides 换成别的仓库；W8
    换成数据仓库时，也只改这里"""
    return DEMO_REPOSITORY
