"""和"当前用户"有关的接口：GET /api/v1/me."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_principal
from app.domain.models import Principal, Role

router = APIRouter()


class MeResponse(BaseModel):
    """GET /api/v1/me 的响应：服务器认出当前用户
    只放前端需要显示的三个字段，project_ids 这类内部信息不返回"""

    user_id: str
    tenant_id: str
    role: Role


@router.get("/me")
def read_me(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> MeResponse:
    """返回服务器认出当前用户，前端可以用它显示当前登录的是谁"""
    return MeResponse(
        user_id=principal.user_id, tenant_id=principal.tenant_id, role=principal.role
    )
