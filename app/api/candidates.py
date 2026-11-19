"""候选人相关接口：查看简历GET /api/v1/candidates/{candidate_id}/resume
接口自己不做权限判断：先从仓库拿数据，再交给门卫check_resume_access 判断
最后把门卫的结论翻译成 HTTP状态码"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import get_current_principal
from app.domain.models import Principal, Reason
from app.domain.policy import check_resume_access
from app.repository import InMemoryRepository, get_repository

router = APIRouter()


class ResumeResponse(BaseModel):
    """查看简历的响应：只返回授权字段；公司、项目、同意书、授权记录这些内部信息不返回"""

    candidate_id: str
    content: str


def candidate_not_found() -> HTTPException:
    """查无此人的404

    别家公司的候选人和不存在的候选人，都用这一个404
    让人从响应里看不出区别。只在这里定义一次，就不会两处
    写得不一样"""

    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found"
    )


@router.get("/candidates/{candidate_id}/resume")
def read_resume(
    candidate_id: str,
    principal: Annotated[Principal, Depends(get_current_principal)],
    repo: Annotated[InMemoryRepository, Depends(get_repository)],
) -> ResumeResponse:
    """查看候选人简历的正文。身份只认令牌，不看请求里自己填的公司或用户"""
    candidate = repo.get_candidate(principal.tenant_id, candidate_id)
    if candidate is None:
        raise candidate_not_found()
    decision = check_resume_access(
        principal,
        candidate,
        repo.get_consent(principal.tenant_id, candidate_id),
        repo.list_acl_entries(principal.tenant_id, candidate_id),
    )
    if decision.reason == Reason.NOT_FOUND:
        raise candidate_not_found()
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to read this resume",
        )
    resume = repo.get_resume(principal.tenant_id, candidate_id)
    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
        )
    return ResumeResponse(candidate_id=candidate_id, content=resume.content)
