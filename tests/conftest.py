"""多个测试文件共用的 fixture。

pytest 会自动读取 tests 文件夹里的 conftest.py：这里定义的 fixture，
这个文件夹里的所有测试文件都能直接用，不需要 import。
"""

# 标准库 collections.abc 的 Iterator：给"用 yield 交出值的函数"标注返回类型。
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

# 我们自己的代码：要被替换的依赖、用来造假用户的类型，以及要测试的应用。
from app.auth import get_token_table
from app.domain.models import Principal, Role
from app.main import app

# 测试专用的假用户和假令牌表，只在测试里用，不是演示令牌。
EMPLOYEE_A = Principal(
    user_id="user-a",
    tenant_id="tenant-1",
    role=Role.RECRUITER,
    project_ids=frozenset(["project-1"]),
)
ADMIN = Principal(
    user_id="admin-1",
    tenant_id="tenant-1",
    role=Role.PROJECT_ADMIN,
    project_ids=frozenset(["project-1"]),
)
TEST_TOKEN_TABLE = {"test-token-a": EMPLOYEE_A, "test-token-admin": ADMIN}


@pytest.fixture
def client() -> Iterator[TestClient]:
    # 替换依赖：接口原本要读本地令牌文件，测试时改用上面的假令牌表。
    app.dependency_overrides[get_token_table] = lambda: TEST_TOKEN_TABLE
    yield TestClient(app)
    # 收尾：去掉替换，免得影响别的测试。
    app.dependency_overrides.pop(get_token_table, None)
