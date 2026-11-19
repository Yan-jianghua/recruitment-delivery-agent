import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict

from app.domain.models import Principal, Role

TOKENS_FILE_ENV = "RDA_DEMO_TOKENS_FILE"


class TokenIdentity(BaseModel):
    """令牌文件里，一个令牌对应的身份。Pydantic 会按这里写的类型检查文件内容"""

    model_config = ConfigDict(extra="forbid")

    user_id: str
    tenant_id: str
    role: Role
    project_ids: list[str]


class TokenFile(BaseModel):
    """整个令牌文件的格式:{"tokens":{"<令牌>":{身份},}"""

    model_config = ConfigDict(extra="forbid")
    tokens: dict[str, TokenIdentity]


def load_token_table(path: Path) -> dict[str, Principal]:
    """读取令牌文件并检查格式,转换成“令牌 -> 身份” 对照表。
    文件不是合法的 JSON 缺了字段,类型不对，都会抛出pydantic
    的 ValidationError"""
    token_file = TokenFile.model_validate_json(path.read_text(encoding="utf-8"))
    table: dict[str, Principal] = {}
    for token, identity in token_file.tokens.items():
        table[token] = Principal(
            user_id=identity.user_id,
            tenant_id=identity.tenant_id,
            role=identity.role,
            project_ids=frozenset(identity.project_ids),
        )
    return table


def get_token_table() -> dict[str, Principal]:
    path = os.environ.get(TOKENS_FILE_ENV)
    if not path:
        return {}
    return load_token_table(Path(path))


bearer_scheme = HTTPBearer()


def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    token_table: Annotated[dict[str, Principal], Depends(get_token_table)],
) -> Principal:
    """依赖：认出当前用户接口函数要知道"谁在请求"，就声明依赖这个函数。"""
    principal = token_table.get(credentials.credentials)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal
