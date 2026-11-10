"""门卫：判断一个员工能不能查看某个候选人的简历正文。

这里的函数都是"纯函数"：只根据传进来的参数做判断，不查数据库、不访问网络，
同样地输入永远得到同样的结果，所以测试时造几个对象就能测。
数据从哪来（查数据库）是以后接口层的事，查好了再交给门卫。
"""

# 从 app/domain/models.py 导入要用到的数据类型（点号对应目录层级）。
from app.domain.models import AclEntry, Candidate, ConsentRecord, Decision, Principal, Reason, Action, ConsentStatus

# -> bool：返回 True（有授权）或 False（没有授权）。
def has_grant(principal: Principal,#当前用户
    candidate: Candidate,#候选人
    acl_entries: list[AclEntry]) -> bool:
    """在授权记录里找：有没有一条允许 principal 查看 candidate 简历的记录。"""
    # 依次检查每一条授权记录。列表里可能有很多条（员工可能被授权看很多候选人），
    # 只要有一条四项全部对上，就算有授权。
    for entry in acl_entries:
        # 四个条件必须同时满足：同一家公司、授权给的就是这个员工、
        # 授权的对象就是这个候选人、允许的动作是"查看简历"。圆括号让条件可以分行写。
        if (entry.tenant_id == principal.tenant_id
                and entry.subject_id == principal.user_id
                and entry.resource_id == candidate.candidate_id
                and entry.action == Action.READ_RESUME):
            # 找到了就立刻返回 True，后面的记录不用再看。
            return True
    # 注意缩进：这一行和 for 对齐，在循环外面。只有所有记录都看完、一条都没对上，
    # 才会走到这里。如果缩进到循环里面，就会只看第一条记录就下结论。
    return False
# 这个函数检查"数据本身对不对"，和后面的业务规则分开处理：
# - 业务情况：正常运行就会发生（比如没有同意书），
#   交给 check_resume_access 的规则处理，返回 Decision。
# - 程序错误：正常运行不该发生（比如递进来的是别人的同意书），
#   在这里抛异常，让问题立刻暴露，而不是悄悄返回一个看起来很正常地拒绝结果。
# -> None：这个函数不返回结果，任务只是"检查，不对就报错"。
def ensure_consent_belongs_to(consent: ConsentRecord | None,candidate: Candidate) -> None:
    """判断同意书必须属于这个候选人，对不上说明调用代码有 bug,抛出异常"""
    # 没有同意书是正常的业务情况，交给后面的规则处理。
    # return 后面什么都不写，就是直接结束函数。
    if consent is None:
        return
    # 同意书上的候选人或公司，有一个对不上，就说明上游代码递错了数据。
    # 公司也要比：两家公司可能各有一个编号叫 cand-1 的候选人。
    if consent.candidate_id != candidate.candidate_id or consent.tenant_id != candidate.tenant_id:
        # raise 抛出异常：这个函数和调用它的 check_resume_access 都会立刻停止，
        # 谁也拿不到判断结果。ValueError 表示"参数类型没问题，但值不对"。
        # f 字符串的花括号里写变量，运行时会换成变量的值，
        # 这样报错信息里就带上了编号，方便定位问题。
        raise ValueError(f"同意书与候选人对不上，同意书属于:{consent.candidate_id},{consent.tenant_id},候选人是{candidate.candidate_id},{candidate.tenant_id}")

# 参数和返回值的类型：
#   consent: ConsentRecord | None —— 竖线表示"或者"：
#       可能是一份同意书，也可能是 None（候选人没签）。
#   acl_entries: list[AclEntry] —— 一个列表，里面每个元素都是 AclEntry。
#   -> Decision —— 返回一个 Decision（是否放行 + 原因）。
def check_resume_access(
    principal: Principal,#当前用户
    candidate: Candidate,#候选人
    consent: ConsentRecord | None,#同意记录
    acl_entries: list[AclEntry]#授权记录
) -> Decision:
    """判断 principal 能否查看 candidate 的简历正文. 默认为拒绝"""
    # 第 0 步：先检查数据本身对不对（同意书是不是这个候选人的），不对就抛异常。
    ensure_consent_belongs_to(consent, candidate)

    # 下面按顺序检查 4 条规则，顺序本身就是安全设计：
    # 任何一条不满足就立刻 return 拒绝（提前返回），后面的规则不再执行；
    # 只有全部通过，才会走到最后的 else 放行。这就是"默认拒绝"。
    # Decision(False, ...) 按字段顺序传值：第一个是 allowed，第二个是 reason。

    # 规则 1：不是同一家公司 → 假装查无此人（RDA-002）。
    # 必须排第一：对别家公司的候选人，"在不在项目里""有没有同意书"都不能透露。
    if principal.tenant_id != candidate.tenant_id:
        return Decision(False,Reason.NOT_FOUND)
    # 规则 2：候选人不在这个员工参与的项目里 → 拒绝（RDA-003）。
    # not in 的意思是"不在……里面"。
    elif candidate.project_id not in principal.project_ids:
        return Decision(False,Reason.PROJECT_MISMATCH)
    # 规则 3：没有查看授权 → 拒绝。管理员也要有自己的授权，没有例外（RDA-006）。
    # not 把结果取反：has_grant 返回 False（没有授权）时，这个条件才成立。
    elif not has_grant(principal,candidate,acl_entries):
        return Decision(False,Reason.NO_GRANT)
    # 规则 4a：没有同意书 → 拒绝（RDA-004）。
    # 同意书是不是这个候选人的，开头的 ensure_consent_belongs_to 已经查过
    # （对不上会直接抛异常），所以这里只需要看"有没有"。
    elif consent is None:
        return Decision(False,Reason.NO_CONSENT)
    # 规则 4b：同意书不是"有效"状态 → 拒绝（RDA-005）。
    # 走到这里，consent 一定不是 None（上一条已经处理），可以放心读 consent.status。
    # 要比较的是同意书的状态 consent.status，不是整份同意书 consent。
    # 写成"不是 ACTIVE 就拒绝"（白名单）：以后新加的状态（比如已过期）也会默认被拒绝，
    # 到时再给它加一个专门的原因。
    elif consent.status != ConsentStatus.ACTIVE:
        return Decision(False,Reason.CONSENT_WITHDRAWN)
    # 前面的规则都没拦住，才放行。放行只有这一个出口。
    else:
        return Decision(True,Reason.ALLOWED)
