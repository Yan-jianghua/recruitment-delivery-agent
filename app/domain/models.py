"""门卫（权限检查）要用到的数据。

这个文件只定义"数据长什么样"，不写判断规则，规则在 policy.py 里。
- 枚举（StrEnum）：固定的几个选项，比如角色、动作、同意书状态、判断原因。
- 数据类（dataclass）：把几项相关的信息装在一起，比如一个员工、一个候选人。
"""

# dataclass 是标准库 dataclasses 里的装饰器。写在类上面，会自动生成
# __init__（创建对象）、__repr__（打印）、__eq__（比较相等）等方法，不用每个类都手写。
from dataclasses import dataclass

# StrEnum 是标准库 enum 里的"字符串枚举"（Python 3.11 起才有）。
# 每个成员本身就是字符串：能直接和字符串比较，也方便存进数据库、转成 JSON。
# 为什么不直接写字符串？字符串拼错（比如 "recruited"）不会报错，判断只会悄悄出错；
# 枚举拼错（比如 Role.RECRUTER）会立刻报 AttributeError。
from enum import StrEnum


class Role(StrEnum):
    """员工在系统里的角色。"""

    # 写法：成员名 = 值。代码里写 Role.RECRUITER，存储和传输时是 "recruiter"。
    RECRUITER = "recruiter"  # 招聘顾问
    PROJECT_ADMIN = "project_admin"  # 项目管理员


class Action(StrEnum):
    """授权记录里允许做的动作。以后需要新动作（比如下载简历），就在这里加一行。"""

    READ_RESUME = "read_resume"  # 查看简历


class ConsentStatus(StrEnum):  # 同意状态
    """候选人同意书的状态。只有 ACTIVE（有效）才允许查看简历。"""

    ACTIVE = "active"  # 有效
    WITHDRAWN = "withdrawn"  # 已撤回


class Reason(StrEnum):
    """门卫给出的判断原因。每种拒绝对应一条规则，方便接口返回、审计和调试。"""

    ALLOWED = "allowed"  # 允许
    # 跨公司时假装"查无此人"，不让对方知道别家公司有这个人（RDA-002）。
    NOT_FOUND = "not_found"  # 查无此人
    PROJECT_MISMATCH = "project_mismatch"  # 不在这个项目中
    NO_GRANT = "no_grant"  # 授权记录里找不到查看授权
    NO_CONSENT = "no_consent"  # 没有同意书
    CONSENT_WITHDRAWN = "consent_withdrawn"  # 同意书已撤回


# frozen=True：对象创建后不能再改字段，改了会报 FrozenInstanceError。
# 门卫用到的数据都是"事实"，判断过程中不允许任何代码偷偷修改（比如把员工的公司改掉）。
# 下面每个数据类都加了它，道理相同。
@dataclass(frozen=True)
class Principal:  # 当前用户
    """正在发请求的员工（Principal 意为"主体"）。

    身份由服务端在登录时认定，不能相信请求里自己填的身份（RDA-007）。
    """

    # 每一行是一个字段，写法是"字段名: 类型"。dataclass 靠冒号认出哪些是字段，
    # 但类型本身 Python 运行时不检查，传错类型也不会报错。
    user_id: str  # 用户编号
    tenant_id: str  # 所属租户
    role: Role  # 角色身份
    # frozenset 是"不可修改的集合"：查找快、不重复。光有 frozen=True 不够：
    # 如果这里用普通 set，别人仍然能往集合里加项目；frozenset 本身也改不了。
    project_ids: frozenset[str]  # 参与的客户项目


@dataclass(frozen=True)
class Candidate:  # 候选人
    """被查看的候选人。

    门卫只需要知道他属于哪家公司、哪个项目，所以这里只放编号，不放简历正文。
    """

    candidate_id: str  # 候选人编号
    tenant_id: str  # 所属租户
    project_id: str  # 所属客户项目


@dataclass(frozen=True)
class ConsentRecord:  # 同意记录
    """候选人签的同意书：同意公司查看、使用他的简历。"""

    candidate_id: str  # 候选人
    tenant_id: str  # 租户
    status: ConsentStatus  # 状态
    # 同意书的第几版。以后用它判断"重复提交的是不是同一版"
    # （RDA-008：重复提交同一版本，结果要一样）。
    version: int  # 版本


@dataclass(frozen=True)
class AclEntry:  # 授权记录
    """一条授权记录（ACL 是 Access Control List 的缩写，意为访问控制列表）。

    读法：在 tenant_id 这家公司里，subject_id 这个员工，
    可以对 resource_id 这个资源，做 action 这个动作。
    """

    tenant_id: str  # 租户
    subject_id: str  # 被授权的员工（填员工的 user_id）
    resource_id: str  # 被访问的资源（这里填候选人编号）
    action: Action  # 查看简历


@dataclass(frozen=True)
class Decision:
    """门卫的判断结果：是否放行 + 原因。

    为什么不只返回 True / False？接口要根据原因决定回答"查无此人"还是"无权查看"，
    审计要记下原因，调试时也能一眼看出卡在哪一关。
    """

    allowed: bool  # 是否允许
    reason: Reason  # 原因
