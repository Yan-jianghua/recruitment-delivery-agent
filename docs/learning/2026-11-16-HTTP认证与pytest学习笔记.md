# Git、HTTP、FastAPI 认证与 pytest 学习笔记

整理日期：2026-11-16。

范围：本聊天全部学习讨论，以及最开始粘贴的其他聊天记录。重复问题合并到对应主题，保留容易混淆的地方。本笔记结合整理时读取的项目代码说明；记录讲解内容，不代表已经独立掌握，也不代表本次执行过测试或完成项目验收。

所有示例 token 都是教学字符串或项目中的合成测试数据。本笔记没有读取本地真实令牌文件。

## 目录

1. [先看整个项目中的关系](#1-先看整个项目中的关系)
2. [git status -s](#2-git-status--s)
3. [HTTP 请求、响应及其组成](#3-http-请求响应及其组成)
4. [headers、请求头与响应头](#4-headers请求头与响应头)
5. [Uvicorn 和 FastAPI](#5-uvicorn-和-fastapi)
6. [环境变量与令牌文件路径](#6-环境变量与令牌文件路径)
7. [认证方案、认证凭据与身份](#7-认证方案认证凭据与身份)
8. [HTTPBearer 的输入和输出](#8-httpbearer-的输入和输出)
9. [Depends、Annotated 与自动传参](#9-dependsannotated-与自动传参)
10. [token_table 如何查找身份](#10-token_table-如何查找身份)
11. [TestClient 如何测试接口](#11-testclient-如何测试接口)
12. [响应对象与三条断言](#12-响应对象与三条断言)
13. [Iterator、iter、next 与 yield](#13-iteratoriternext-与-yield)
14. [pytest.fixture 与 yield 的交接过程](#14-pytestfixture-与-yield-的交接过程)
15. [dependency_overrides 与 lambda](#15-dependency_overrides-与-lambda)
16. [字典的 pop](#16-字典的-pop)
17. [parametrize 与 pytest.param](#17-parametrize-与-pytestparam)
18. [把认证测试完整串起来](#18-把认证测试完整串起来)
19. [易混淆问题速查](#19-易混淆问题速查)
20. [复习检查与参考资料](#20-复习检查与参考资料)
21. [monkeypatch：临时修改测试环境](#21-monkeypatch临时修改测试环境)

## 1. 先看整个项目中的关系

普通网络访问时：

```text
客户端，例如浏览器或前端程序
    ↓ 发送 HTTP 请求
Uvicorn 接收网络请求
    ↓
FastAPI 根据方法和路径匹配接口，解析参数和依赖
    ↓
认证依赖获取当前身份
    ↓
接口函数执行，返回业务结果
    ↓
FastAPI 生成 HTTP 响应
    ↓
Uvicorn 将响应发送回客户端
```

接口测试时：

```text
pytest 准备测试数据和 TestClient
    ↓
TestClient 直接向 FastAPI 应用发起测试请求
    ↓
应用执行路由、依赖和接口逻辑
    ↓
测试取得 response，通过 assert 检查结果
    ↓
pytest 执行 fixture 的收尾操作
```

TestClient 直接调用应用，不需要先通过 Uvicorn 启动监听端口的服务器。这类测试能检查应用行为；它不等于验证了公网部署或完整网络环境。

整理时，项目的 `app/main.py` 已经包含：

| 接口 | 作用 | 当前是否声明认证依赖 |
| --- | --- | --- |
| `GET /health` | 健康检查，返回 `{"status": "ok"}` | 没有 |
| `GET /api/v1/me` | 返回服务端认出的当前身份 | 有，依赖 `get_current_principal` |

聊天较早阶段曾读取到只有 `/health` 的代码；现在已经新增 `/api/v1/me`，以当前源文件为准。

## 2. git status -s

```powershell
git status -s
```

作用：简短显示 Git 文件状态。`-s` 是 `--short` 的缩写，只查看状态，不修改文件。

输出示例：

```text
 M app/auth.py
M  README.md
?? tests/test_auth.py
```

对普通已跟踪文件，前两列分别表示：

```text
第一列：暂存区相对于上次提交的状态
第二列：工作区相对于暂存区的状态
```

| 标记 | 含义 |
| --- | --- |
| ` M` | 修改尚未暂存 |
| `M ` | 修改已经暂存，等待提交 |
| `MM` | 已暂存一部分修改，暂存后文件又发生了修改 |
| `??` | 未跟踪文件 |
| `A ` | 新增文件已经暂存 |
| ` D` | 文件删除了，删除尚未暂存 |

空格位置有意义。没有输出，通常表示没有当前命令会显示的待处理改动；忽略文件、Git 显示配置等会影响展示范围，也不能据此判断本地提交是否已推送。

## 3. HTTP 请求、响应及其组成

### 3.1 请求与响应

- **请求（request）**：客户端发给服务端的消息，表达要访问什么资源、提交什么信息。
- **响应（response）**：服务端处理后发回的消息，说明处理结果，并可以携带数据。

下面使用 HTTP/1.1 的文本形式解释结构。HTTP/2、HTTP/3 的线上编码不同，不应把下面的文本布局当作所有版本的实际传输格式。

### 3.2 一条请求的结构

```text
请求行
请求头
空行
请求体（可选）
```

例如，请求当前身份接口，下面省略其他客户端可能自动添加的头：

```http
GET /api/v1/me HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer test-token-a
Accept: application/json

```

| 内容 | 含义 |
| --- | --- |
| `GET` | 请求方法，这里用于获取信息 |
| `/api/v1/me` | 请求路径，决定访问哪个接口 |
| `HTTP/1.1` | 协议版本 |
| `Host` | 目标主机及端口 |
| `Authorization` | 认证信息 |
| `Accept` | 客户端希望收到的数据格式，最终响应取决于接口能力和处理结果 |
| 空行 | 表示请求头结束 |

这个请求没有请求体。请求体可以携带要提交的业务数据，比如下面的职位信息 JSON；这是数据格式示例，不表示当前已有提交职位接口。

```json
{"title": "Python 开发工程师", "city": "上海"}
```

发送 JSON 请求体时，通常会设置：

```http
Content-Type: application/json
```

### 3.3 一条响应的结构

```text
状态行
响应头
空行
响应体（可选）
```

假设使用项目测试中的合成身份数据，成功响应可以示意为：

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"user_id":"user-a","tenant_id":"tenant-1","role":"recruiter"}
```

这里省略了 `Content-Length` 等可能出现的传输相关响应头。

| 内容 | 含义 |
| --- | --- |
| `200` | 响应状态码，表示请求成功 |
| `Content-Type: application/json` | 响应体采用 JSON 格式 |
| 空行 | 表示响应头结束 |
| 用户信息 JSON | 响应体，包含具体返回数据 |

“JSON”可以是消息体采用的格式，并不等于整个 HTTP 请求或整个响应。

## 4. headers、请求头与响应头

### 4.1 headers 是什么

`headers` 是 `header` 的复数，表示头部信息。HTTP 头通常是一组字段名和值：

```http
字段名: 字段值
```

Python 调用中，常用字典提供要设置的头：

```python
headers = {"Authorization": "Bearer test-token-a"}
```

`request.headers`、`response.headers` 是相应对象上访问头信息的入口，通常是支持类似字典操作的对象，不必把它们都理解成普通 `dict`。

### 4.2 两个方向

| 类型 | 发送方向 | 作用举例 |
| --- | --- | --- |
| 请求头 | 客户端 → 服务端 | 携带 token、说明请求体格式 |
| 响应头 | 服务端 → 客户端 | 说明响应体格式、告知认证要求 |

同名头可以出现在两个方向，例如：

```text
请求中的 Content-Type：说明请求体格式
响应中的 Content-Type：说明响应体格式
```

### 4.3 请求头由谁设置

有些请求头由浏览器或调用工具自动添加，有些由调用代码设置。标准字段按标准含义使用，也可以与后端约定自定义字段。

| 内容 | 来源 |
| --- | --- |
| `Authorization` | 标准认证请求头名称 |
| `Bearer` | 标准认证方案，本项目选择使用它 |
| `test-token-a` | 本项目测试中设置的合成 token 值 |
| `X-Client-Version` 等自定义头 | 需要调用方与后端约定含义，后端自行读取和处理 |

当前代码使用 `HTTPBearer`，按 `Authorization: Bearer <token>` 获取认证信息。

HTTP 头的字段名称不区分大小写。因此，响应里的 `WWW-Authenticate` 可以通过 `response.headers["www-authenticate"]` 读取。这个规则不意味着 token 字符串也忽略大小写；本项目仍按字典中的 token 键匹配。

### 4.4 Authorization 与 WWW-Authenticate

```text
Authorization: Bearer test-token-a
客户端 → 服务端：“这是我提交的令牌，请核验。”

WWW-Authenticate: Bearer
服务端 → 客户端：“这里要求使用 Bearer 认证。”
```

它们是两个不同的字段，方向和职责也不同。

特别容易混淆的用例：

```python
pytest.param({}, id="no_authorization_header")
```

它给测试传入空字典，在本例没有默认认证头的客户端配置下，请求不携带 `Authorization`。客户端仍可能自动添加 `Host` 等基础头。

服务端接到缺少认证信息的请求后，可以返回：

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer
Content-Type: application/json

{"detail":"Not authenticated"}
```

请求没有 `Authorization`，与响应包含 `WWW-Authenticate` 并不冲突。后者是在告知认证要求。

## 5. Uvicorn 和 FastAPI

Uvicorn 是运行在电脑或服务器上的一个程序，负责监听地址和端口、接收网络请求、调用应用、发送响应。官方称其为 ASGI Web 服务器；ASGI 是服务器与 Python 应用之间交互的一套约定。

FastAPI 用于组织应用：登记接口、匹配路径、处理参数与依赖、调用接口函数和生成响应。

```text
浏览器：“我要访问 /health。”
    ↓
Uvicorn：接到网络请求，交给应用
    ↓
FastAPI：匹配 /health，调用 health()
    ↓
health()：返回 {"status": "ok"}
    ↓
应用生成响应，Uvicorn 发回浏览器
```

项目根目录下的启动命令示例：

```powershell
uvicorn app.main:app --reload
```

| 部分 | 含义 |
| --- | --- |
| `uvicorn` | 启动服务器程序 |
| `app.main` | 导入 `app/main.py` 对应的模块 |
| `:app` | 使用模块中名为 `app` 的对象，即 `app = FastAPI(...)` |
| `--reload` | 开发时监测代码文件变化，自动重新加载服务 |

默认配置下地址为本机 `127.0.0.1`，端口为 `8000`。启动后程序会持续等待请求，终端保持运行是正常现象。`--reload` 用于开发，不作为生产部署方案。

## 6. 环境变量与令牌文件路径

```powershell
$env:RDA_DEMO_TOKENS_FILE = "local\demo_tokens.json"
```

意思是：在当前 PowerShell 进程中设置一个环境变量，告诉后续启动的程序演示令牌文件的位置。

| 部分 | 含义 |
| --- | --- |
| `$env:` | PowerShell 访问环境变量的语法 |
| `RDA_DEMO_TOKENS_FILE` | 项目约定的环境变量名称 |
| `=` | 赋值 |
| `"local\demo_tokens.json"` | 保存的值，是路径字符串 |

Python 中：

```python
path = os.environ.get("RDA_DEMO_TOKENS_FILE")
```

得到路径字符串后，项目再通过：

```python
return load_token_table(Path(path))
```

读取文件并建立 token 到身份的对照表。

需要区分三个东西：

```text
环境变量：保存文件位置这一配置
路径字符串：local\demo_tokens.json
JSON 文件内容：实际的令牌与身份数据
```

执行 PowerShell 赋值本身不创建、不读取、不校验 JSON 文件。

相对路径以程序读取文件时的工作目录为基准。从项目根目录启动时，上面的路径指向项目内的 `local/demo_tokens.json`，并不是自动相对于 `app/auth.py`。

这个设置影响当前 PowerShell 及之后从它启动的子进程，不会更新已经运行的服务进程。设置后需要从同一终端重新启动服务；在其他独立终端中使用时，也需要相应配置。

当前 `get_token_table` 在环境变量未设置或为空时返回空表；配置了路径后，才调用读取函数。文件不存在、JSON 格式错误等属于配置或读取问题，不应一概理解为“token 无效”。

## 7. 认证方案、认证凭据与身份

认证是服务端确认当前请求对应哪个身份的过程。认证之后，具体能否访问某个资源，还需要权限判断。

例如：

```http
Authorization: Bearer test-token-a
```

| 概念 | 本例内容 | 含义 |
| --- | --- | --- |
| 认证方案 `scheme` | `Bearer` | 采用哪种认证方式，指导服务端如何解释凭据 |
| 认证凭据 `credentials` | `test-token-a` | 提交给服务端核验的具体信息 |
| 身份 `Principal` | `user-a` 等身份字段组成的对象 | 服务端核验凭据后得到的业务身份 |

携带一个字符串并不证明认证已经成功。服务端仍需要核验它。

本项目目前的核验方式是查 token 对照表：找到就取得相应 `Principal`；找不到则拒绝。代码没有因为使用 `HTTPBearer` 就自动获得 JWT 验签、过期检查、令牌签发或资源授权能力。

## 8. HTTPBearer 的输入和输出

### 8.1 类、实例、结果对象

```python
bearer_scheme = HTTPBearer()
```

| 写法 | 是什么 |
| --- | --- |
| `HTTPBearer` | 类，定义提取 Bearer 认证信息的行为 |
| `HTTPBearer()` | 创建该类的实例 |
| `bearer_scheme` | 保存实例的变量 |
| 调用该实例得到的结果 | `HTTPAuthorizationCredentials` 对象 |

实例的类型与调用结果的类型可以不同，类似于函数本身与函数返回值的类型不同。

### 8.2 为什么实例可以被调用

`HTTPBearer` 定义了 `__call__` 方法，所以它的实例是可调用对象。

两种操作要区分：

```text
HTTPBearer()：创建并配置提取工具
调用 bearer_scheme：让这个工具处理某次请求
```

前者通常在加载模块时发生，后者由 FastAPI 在处理需要该依赖的请求时执行。

### 8.3 请求参数从哪里来

`Depends(bearer_scheme)` 只登记要使用哪个依赖。FastAPI 之后检查可调用对象的参数，并提供当前请求。

聊天中曾用 `request: Request` 简化示意。整理时项目环境中安装的实现，实际参数标注为：

```python
async def __call__(
    self, request: HTTPConnection
) -> HTTPAuthorizationCredentials | None:
    ...
```

普通 HTTP 请求中，框架传入的 `Request` 继承自 `HTTPConnection`，可以用于这个参数。无需在 `Depends(...)` 中手动写当前请求。

可以近似理解为框架在合适的时机执行下面这件事；这是说明调用关系的示意，不是要添加到接口里的代码：

```python
result = await bearer_scheme(request=current_request)
```

`self` 由 Python 实例调用机制提供；当前请求由 FastAPI 提供。`await` 等待这里的异步调用完成。

同一个 `bearer_scheme` 实例可以处理不同请求：

```text
请求 A 携带 Bearer token-a → 处理 A → 提取 token-a
请求 B 携带 Bearer token-b → 处理 B → 提取 token-b
```

### 8.4 返回的两个字段

对于：

```http
Authorization: Bearer test-token-a
```

成功提取的结果可以表示为：

```python
HTTPAuthorizationCredentials(
    scheme="Bearer",
    credentials="test-token-a",
)
```

因此：

```python
credentials.scheme       # "Bearer"
credentials.credentials  # "test-token-a"
```

外层 `credentials` 是变量名，后面的 `.credentials` 是结果对象的字段名。可以换变量名帮助理解：

```python
auth = HTTPAuthorizationCredentials(
    scheme="Bearer",
    credentials="test-token-a",
)
token = auth.credentials
```

字段里只包含 token，不包含前面的 `Bearer `。

### 8.5 auto_error

| 配置 | 缺少可用的 Bearer 认证信息时 |
| --- | --- |
| `HTTPBearer()`，默认 `auto_error=True` | 依赖自动报错，中止后续正常处理 |
| `HTTPBearer(auto_error=False)` | 返回 `None`，由调用方自行处理 |

使用 `False` 时，需要考虑空结果：

```python
auth: Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]
```

并先判断 `auth is None`，再访问字段。这只是可选配置的说明；当前项目使用默认配置。

`HTTPBearer` 检查认证头和 Bearer 方案并提取凭据；具体 token 是否存在于本项目的身份表，由后续业务代码检查。

## 9. Depends、Annotated 与自动传参

```python
credentials: Annotated[
    HTTPAuthorizationCredentials,
    Depends(bearer_scheme),
]
```

| 部分 | 作用 |
| --- | --- |
| `credentials` | 函数参数名 |
| `HTTPAuthorizationCredentials` | 描述这个参数预期接收的值的类型 |
| `Annotated[...]` | 将类型和附加说明放在一起 |
| `Depends(bearer_scheme)` | 告诉 FastAPI 通过这个依赖获取参数值 |

FastAPI 会调用依赖，把调用结果传入 `credentials`。这里没有把 `HTTPBearer` 实例转换成 `HTTPAuthorizationCredentials`；结果对象是调用依赖产生的。类型标注本身不完成这类转换。

相同机制也用于：

```python
token_table: Annotated[
    dict[str, Principal],
    Depends(get_token_table),
]
```

FastAPI 调用 `get_token_table`，把返回的字典传入参数 `token_table`。如果存在依赖替换规则，就调用相应替代函数。

这里是框架在请求处理时注入参数。若你在普通 Python 代码中直接调用 `get_current_principal(...)`，需要自己提供所需参数；单纯存在 `Depends` 标记不会让普通函数调用自动完成同样的注入。

## 10. token_table 如何查找身份

```python
token_table: dict[str, Principal]
```

描述的是：键为字符串，值为 `Principal` 对象的字典。

项目测试数据为：

```python
TEST_TOKEN_TABLE = {"test-token-a": EMPLOYEE_A}
```

`EMPLOYEE_A` 是一个合成的 `Principal` 身份对象。

当前认证逻辑的关键行：

```python
principal = token_table.get(credentials.credentials)
```

对于有效测试 token，等价于：

```python
principal = token_table.get("test-token-a")
```

使用字符串查找，是因为结果对象的 `.credentials` 字段就是字符串，而对照表以 token 字符串为键。

| 查找结果 | 当前认证代码的行为 |
| --- | --- |
| 找到 `Principal` | 返回这个身份对象 |
| 未找到，得到 `None` | 抛出 `HTTPException`，返回认证失败响应 |

注意：字典的 `.get(键)` 默认在找不到时返回 `None`；它本身不会自动抛出 HTTP 错误。抛出错误的是后面的 `if principal is None` 分支。

当前函数：

```python
def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    token_table: Annotated[dict[str, Principal], Depends(get_token_table)],
) -> Principal:
    principal = token_table.get(credentials.credentials)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal
```

这段是项目函数摘录，依赖该模块中的导入和类型定义。

在 `/api/v1/me` 中，FastAPI 再把返回的身份交给 `read_me` 的 `principal` 参数。接口返回 `MeResponse`，只包含 `user_id`、`tenant_id`、`role`。

## 11. TestClient 如何测试接口

`TestClient` 是测试 FastAPI 应用的客户端类。

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get("/health")
```

| 写法 | 含义 |
| --- | --- |
| `TestClient` | 类 |
| `TestClient(app)` | 创建针对这个应用的测试客户端对象 |
| `client` | 保存客户端对象的变量 |
| `client.get(...)` | 发起 GET 测试请求 |
| `response` | 应用返回的响应对象 |

TestClient 会运行应用的实际路由和依赖处理逻辑；在这个测试场景中，不用预先启动 Uvicorn。它不是用来渲染网页界面或执行前端 JavaScript 的浏览器。

### 11.1 headers=headers 是什么

```python
headers = {"Authorization": "Bearer test-token-a"}
response = client.get("/api/v1/me", headers=headers)
```

`headers=headers` 的两边职责不同：

```text
左边 headers：get 方法的参数名，说明要设置请求头
右边 headers：当前变量名，提供实际的请求头数据
```

变量可以换名，含义不变：

```python
auth_headers = {"Authorization": "Bearer test-token-a"}
response = client.get("/api/v1/me", headers=auth_headers)
```

这里要访问的接口路径是 `/api/v1/me`。客户端携带 token 后，服务端再提取和核验它。

## 12. 响应对象与三条断言

### 12.1 response 的三个入口

| 表达式 | 获取什么 |
| --- | --- |
| `response.status_code` | 响应状态码 |
| `response.headers` | 响应头 |
| `response.json()` | 将响应体中的 JSON 解析成 Python 数据 |

### 12.2 assert

```python
assert 条件
```

意思是要求条件成立。条件为假时抛出 `AssertionError`，pytest 将该测试记录为失败。

### 12.3 401 是什么

`401` 是 HTTP 响应状态码，表示请求缺少有效的身份认证信息。

| 状态码 | 本次学习中的含义 |
| --- | --- |
| `200` | 请求成功 |
| `401` | 没有通过身份认证 |

认证成功后是否具备资源访问权限，是另外一层判断。不能把所有拒绝访问的情况都归为 401。

测试可以故意发送无效请求。如果预期为 401，实际也为 401，就满足这条断言；错误请求得到预期错误响应，也可以是通过的测试。

### 12.4 检查状态码

```python
assert response.status_code == 401
```

要求服务端返回认证失败状态。

### 12.5 检查认证响应头

```python
assert response.headers["www-authenticate"] == "Bearer"
```

拆开读：

1. 访问 `response` 的响应头集合。
2. 按字段名 `www-authenticate` 取值。
3. 检查该值是否为字符串 `"Bearer"`。

检查的是“服务端有没有告知应采用 Bearer 认证”。这一行不读取客户端发出的 `Authorization`。

### 12.6 response.json 与 response.json()

`response.json` 是方法。方法可以理解为对象自带的函数。

`response.json()` 加上括号，表示调用这个方法，解析响应体。

假设响应体是 JSON：

```json
{"detail": "Not authenticated"}
```

则：

```python
data = response.json()
message = data["detail"]
# message 为 "Not authenticated"
```

在本例中结果是字典。一般来说，JSON 解析结果也可能是列表、字符串、数字等，取决于响应体内容；响应体不是合法 JSON 时，解析会失败。

### 12.7 检查错误响应体

```python
assert response.json() == {"detail": "Not authenticated"}
```

先解析 JSON，再比较实际 Python 数据与预期字典是否相等。

```text
实际为 {"detail": "Not authenticated"} → 满足这条断言
实际为 {"detail": "Token does not exist"} → 不满足这条断言
```

本项目这组三种无效认证场景要求相同的提示信息。这是本项目测试的具体约定，不能推断所有系统的 401 都必须具有完全相同的 JSON 正文。

## 13. Iterator、iter、next 与 yield

### 13.1 Iterator 是迭代器

迭代器是可以逐个提供数据、记录当前取值进度的对象。

```python
numbers = [10, 20, 30]
iterator = iter(numbers)

next(iterator)  # 10
next(iterator)  # 20
next(iterator)  # 30
# 再调用 next(iterator) 会抛出 StopIteration，表示取完了
```

`for` 循环会使用迭代机制，并自动处理正常的迭代结束。

| 概念 | 含义 | 示例 |
| --- | --- | --- |
| `Iterable`，可迭代对象 | 可以通过 `iter()` 获得迭代器 | 列表、字符串 |
| `Iterator`，迭代器 | 可以通过 `next()` 逐个取得值 | `iter([10, 20, 30])` 的结果 |

列表本身不是迭代器，直接 `next(numbers)` 会报 `TypeError`。

### 13.2 Iterator[int] 是类型标注

```python
from collections.abc import Iterator


def provide_numbers() -> Iterator[int]:
    yield 10
    yield 20
    yield 30
```

调用 `provide_numbers()` 得到生成器对象。生成器也是迭代器。

```python
iterator = provide_numbers()
first = next(iterator)   # 10
second = next(iterator)  # 20
```

`yield` 每次提供一个值并暂停执行，下次取值时从暂停处继续。

函数体中的 `yield` 使其成为生成器函数；类型标注只是描述它提供的值的类型。`Iterator[int]` 表示每次提供整数，不是表示每次返回一个整数列表。

### 13.3 普通 yield 与 pytest fixture

普通生成器中，`yield` 的值交给推动生成器执行的调用方，例如 `next(iterator)` 的调用方。

在本次 pytest fixture 中，推动生成器执行的是 pytest，因此交接过程是：

```text
fixture 中的 yield → pytest → 测试函数的参数
```

## 14. pytest.fixture 与 yield 的交接过程

### 14.1 @pytest.fixture 是什么

```python
@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app)
```

| 部分 | 含义 |
| --- | --- |
| `pytest` | 测试工具 |
| `fixture` | pytest 提供的测试准备与收尾机制 |
| `@pytest.fixture` | 用装饰器将下面的函数登记为 fixture |
| `client` | 这个 fixture 的名字 |
| `Iterator[TestClient]` | 描述生成器提供的值是 `TestClient` 对象 |

这里可以读成：“pytest，请把 `client` 登记为一个准备测试客户端的函数。”

登记时不会马上执行这个函数体。按本例默认写法，当测试通过同名参数请求这个 fixture 时，pytest 才安排执行。默认作用域是每个需要它的测试用例各自准备和收尾。

### 14.2 pytest 如何知道测试需要它

```python
def test_me(client: TestClient) -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 401
```

这里通过参数名 `client` 请求同名 fixture。这个例子没有提交认证头，预期为 401。

决定 pytest 找哪个 fixture 的是这里的参数名；`TestClient` 类型标注描述预期对象，不会单靠这个类型标注自动创建客户端。

### 14.3 yield TestClient(app) 到底做什么

```python
yield TestClient(app)
```

可以展开理解为：

```python
test_client = TestClient(app)
yield test_client
```

它依次完成：

1. 创建一个能向 `app` 发起测试请求的客户端对象。
2. 把这个对象提供给 pytest。
3. fixture 暂停在 `yield` 处。
4. pytest 把这个对象传给测试函数的 `client` 参数。
5. 测试函数用 `client.get(...)` 等方法发起请求。
6. 测试结束后，pytest 恢复 fixture，执行 `yield` 后面的清理代码。

```text
TestClient(app) 创建客户端对象
    ↓ yield
pytest 接收对象
    ↓ 作为参数传入
测试函数里的 client
```

因此，fixture 提供出去的是一个 `TestClient` 对象；测试参数接收的是这个对象，不是整个生成器。

### 14.4 @pytest.fixture 与 yield 的分工

- `@pytest.fixture`：让 pytest 识别并管理这个测试准备函数。
- `yield`：在函数中提供一个对象，暂停，等 pytest 后续恢复执行。

只有 `yield`，不会自动把普通生成器变成 pytest fixture；只有类型标注，也不会自动创建客户端。

### 14.5 为什么 yield 后面还能清理

pytest 负责在正常测试收尾阶段恢复生成器。因此，测试中的断言失败，也会进入已经成功提供对象的 fixture 的收尾阶段。

这个保证有前提：fixture 已经成功执行到 `yield`。如果 `yield` 前的准备代码就抛出异常，后面的清理代码不会因此自动获得执行机会；不能把这段示例理解为任何情况下都能完成清理。

## 15. dependency_overrides 与 lambda

### 15.1 app.dependency_overrides 是什么

`app` 是 FastAPI 应用对象，`dependency_overrides` 是它的一个字典属性，可以理解为依赖函数替换表。

```text
键：原来的依赖函数
值：替代它的函数
```

例如：

```python
def fake_get_token_table():
    return TEST_TOKEN_TABLE


app.dependency_overrides[get_token_table] = fake_get_token_table
```

FastAPI 后续解析 `Depends(get_token_table)` 时，会查到替换规则，调用 `fake_get_token_table`，用返回值提供依赖参数。

### 15.2 lambda 是什么

```python
lambda: TEST_TOKEN_TABLE
```

是一个没有参数、返回 `TEST_TOKEN_TABLE` 的匿名函数。它与上面的 `fake_get_token_table` 在这里承担相同职责。

因此：

```python
app.dependency_overrides[get_token_table] = lambda: TEST_TOKEN_TABLE
```

表示登记规则：“需要这个依赖时，调用临时小函数取得测试表。”

| 写法 | 这里的意义 |
| --- | --- |
| `get_token_table` | 函数对象，作为字典键 |
| `get_token_table()` | 立刻调用函数，取得返回值 |
| `lambda: TEST_TOKEN_TABLE` | 创建一个稍后可调用的小函数 |

该赋值登记替换关系，不会在这里执行原始函数，也不会立刻调用 lambda。

### 15.3 替换在什么范围生效

替换由 FastAPI 的依赖解析系统处理，对配置在该 `app` 上、需要该依赖的请求生效。

如果普通 Python 代码直接调用：

```python
get_token_table()
```

仍然执行原函数。替换表没有重写原函数本身。

### 15.4 为什么把替换语句放在 client fixture 里

这条规则是测试期间临时使用的。fixture 可以把开始和结束时机放在一起：

```text
测试发请求前 → 设置替换，使用测试令牌表
测试运行中   → 替换保持有效
测试结束后   → 移除替换，避免影响后续测试
```

所以 `client` fixture 同时准备客户端和它所需的测试环境。Python 没有要求这条赋值必须写在这个函数里；这是便于 pytest 管理测试生命周期的一种组织方式。

## 16. 字典的 pop

本例中的 `pop` 是字典方法：取出键对应的值，并删除这条键值对。

```python
scores = {"小明": 90, "小红": 95}
value = scores.pop("小明")
# value 为 90
# scores 变为 {"小红": 95}
```

语法：

```python
字典.pop(要删除的键, 找不到时的默认值)
```

| 情况 | 结果 |
| --- | --- |
| 键存在 | 删除该条目，返回被删除的值 |
| 键不存在，提供了默认值 | 返回默认值 |
| 键不存在，没有默认值 | 抛出 `KeyError` |

因此：

```python
app.dependency_overrides.pop(get_token_table, None)
```

表示删除 `get_token_table` 对应的替换记录；找不到时返回 `None`。存在时返回的是被移除的替代函数，只是这行没有保存返回值。

删除的是替换表中的记录，原函数和 `TEST_TOKEN_TABLE` 数据仍然存在。`pop` 不会调用被移除的函数。

本 fixture 假设开始时这个依赖没有其他需要保留的替换。`pop` 只负责删除当前条目，不会自动恢复更早被覆盖掉的配置。

## 17. parametrize 与 pytest.param

### 17.1 parametrize 做什么

```python
@pytest.mark.parametrize("headers", UNAUTHENTICATED_CASES)
def test_request_without_valid_token_is_401(
    client: TestClient, headers: dict[str, str]
) -> None:
    ...
```

意思是：把 `UNAUTHENTICATED_CASES` 里的各组数据，分别传给测试函数的 `headers` 参数，每组运行一次测试。

| 装饰器参数 | 作用 |
| --- | --- |
| `"headers"` | 测试函数中的参数名，是一个名称字符串 |
| `UNAUTHENTICATED_CASES` | 保存多组测试输入的变量 |

`"headers"` 不是具体的 HTTP 头字段名称。它指定要接收数据的 Python 函数参数；真正的 HTTP 头字段在传入的字典里，例如 `Authorization`。

### 17.2 pytest.param 做什么

`pytest.param(...)` 定义一组测试参数，还可以附带用例名称等信息。

```python
pytest.param({}, id="no_authorization_header")
```

这里：

- `{}` 是本组传给 `headers` 的值。
- `id` 是测试用例的名字，方便在输出里识别。
- `id` 不传给测试函数，也不发送给服务端。
- `pytest.param` 本身不发请求，实际请求由 `client.get(...)` 发起。

### 17.3 当前项目的三组数据

```python
UNAUTHENTICATED_CASES = [
    pytest.param({}, id="no_authorization_header"),
    pytest.param(
        {"Authorization": "Basic dXNlcjpwYXNz"},
        id="not_a_bearer_token",
    ),
    pytest.param(
        {"Authorization": "Bearer unknown-token"},
        id="unknown_token",
    ),
]
```

| 用例 | 本次 headers | 要检查的场景 |
| --- | --- | --- |
| `no_authorization_header` | `{}` | 没有提供认证请求头 |
| `not_a_bearer_token` | 使用 `Basic` 的认证头 | 认证方案不符合当前接口要求 |
| `unknown_token` | 使用 Bearer，但 token 不在测试表中 | token 查不到身份 |

三组数据各生成一个测试用例，分别检查状态码、响应头和错误正文。不是所有场景都会执行到同一个代码位置：缺少可用 Bearer 信息可由 `HTTPBearer` 直接拒绝；未知 token 在查身份表时拒绝。

### 17.4 多个参数时按位置对应

```python
@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        pytest.param(1, 2, 3, id="one-plus-two"),
        pytest.param(2, 3, 5, id="two-plus-three"),
    ],
)
def test_add(a, b, expected):
    assert a + b == expected
```

第一组把 `1`、`2`、`3` 分别交给 `a`、`b`、`expected`。`expected` 是自己取的参数名，意思是预期结果，不是特殊关键字。

只有普通数据时也能使用元组；`pytest.param` 方便添加名称和其他标记。

项目的权限测试中也采用这个方式：`principal`、`candidate`、`consent`、`acl_entries`、`expected` 按参数名和每行位置对应，分别验证不同权限场景。

### 17.5 client 与 headers 从哪里来

```python
def test_request_without_valid_token_is_401(
    client: TestClient, headers: dict[str, str]
) -> None:
    ...
```

| 参数 | 来源 |
| --- | --- |
| `client` | 同名 `@pytest.fixture` 提供的客户端对象 |
| `headers` | `@pytest.mark.parametrize` 提供的本组请求头数据 |

pytest 准备两者，再运行测试函数。类型标注 `dict[str, str]` 描述键和值都是字符串的字典，不负责生成这些数据。

## 18. 把认证测试完整串起来

### 18.1 核心代码汇总

下面将本次学习的认证测试要点放在一个代码块中。它与当前项目测试结构对应；最后的成功用例使用更直观的教学名称，不表示本次修改了项目测试函数。

```python
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.auth import get_token_table
from app.domain.models import Principal, Role
from app.main import app

EMPLOYEE_A = Principal(
    user_id="user-a",
    tenant_id="tenant-1",
    role=Role.RECRUITER,
    project_ids=frozenset(["project-1"]),
)

TEST_TOKEN_TABLE = {"test-token-a": EMPLOYEE_A}


@pytest.fixture
def client() -> Iterator[TestClient]:
    # 准备测试数据来源：登记依赖替换规则。
    app.dependency_overrides[get_token_table] = lambda: TEST_TOKEN_TABLE

    # 提供客户端。pytest 将它传给测试函数，然后运行测试。
    yield TestClient(app)

    # 测试结束后，pytest 恢复这里的执行，删除替换规则。
    app.dependency_overrides.pop(get_token_table, None)


UNAUTHENTICATED_CASES = [
    pytest.param({}, id="no_authorization_header"),
    pytest.param(
        {"Authorization": "Basic dXNlcjpwYXNz"},
        id="not_a_bearer_token",
    ),
    pytest.param(
        {"Authorization": "Bearer unknown-token"},
        id="unknown_token",
    ),
]


@pytest.mark.parametrize("headers", UNAUTHENTICATED_CASES)
def test_request_without_valid_token_is_401(
    client: TestClient, headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/me", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Not authenticated"}


def test_valid_token_returns_identity(client: TestClient) -> None:
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer test-token-a"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "user-a",
        "tenant_id": "tenant-1",
        "role": "recruiter",
    }
```

### 18.2 一次无效 token 用例的执行顺序

以 `unknown_token` 为例：

```text
1. pytest 发现参数化测试和各组用例数据。
2. 本次选择 headers = {"Authorization": "Bearer unknown-token"}。
3. 测试还需要 client，pytest 执行同名 fixture。
4. fixture 登记 get_token_table → 临时替代函数。
5. fixture 创建 TestClient，通过 yield 提供它，然后暂停。
6. pytest 把客户端和本组 headers 传入测试函数。
7. client.get 发起 GET /api/v1/me 测试请求。
8. FastAPI 匹配接口，解析 get_current_principal 的依赖。
9. HTTPBearer 从当前请求提取 unknown-token。
10. FastAPI 使用替代函数取得 TEST_TOKEN_TABLE。
11. get_current_principal 查表，找不到 unknown-token。
12. 抛出 HTTPException，应用生成 401 响应。
13. 测试取得 response，检查状态码、认证响应头和错误正文。
14. 测试结束，pytest 恢复 fixture。
15. fixture 执行 pop，删除替换规则。
```

这是帮助理解的依赖执行顺序说明，不要求手动编写这些框架步骤。

### 18.3 测试数据范围

这些接口测试使用合成身份和依赖替换，可以检查应用在指定输入下的行为。替换了 `get_token_table` 后，这部分用例不验证真实环境变量和本地文件是否配置正确。

本次只整理和核对笔记，没有运行上述测试；源文件存在、笔记写完、测试通过、用户独立掌握，是不同的状态。

## 19. 易混淆问题速查

| 问题 | 正确理解 |
| --- | --- |
| `bearer_scheme` 是 HTTPBearer，为什么能给 credentials？ | 传入的是调用结果，结果是 HTTPAuthorizationCredentials 对象 |
| `Depends(bearer_scheme)` 没写请求参数，从哪里来？ | FastAPI 在处理当前请求时提供相应请求对象 |
| 同一个实例是否只能处理同一个请求？ | 实例可以复用，每次调用接收当前请求 |
| token_table 的键为什么能用 credentials？ | 实际使用的是 `.credentials` 字段中的 token 字符串 |
| 请求头是自己随意起名吗？ | 标准字段按标准使用，自定义字段需双方约定并自行处理 |
| 请求头与响应头怎么分？ | 看消息方向：客户端发请求头，服务端发响应头 |
| 请求 headers 是空字典，为什么响应还有认证头？ | 请求没有提交凭据，响应仍可告知认证要求，两者不是同一个头集合 |
| `headers=headers` 为什么写两次？ | 左边是调用参数名，右边是提供值的变量名 |
| 401 是否表示测试失败？ | 预期为 401 且实际符合，相关断言就通过 |
| `response.json` 与 `response.json()` 一样吗？ | 前者是方法，后者调用方法，取得解析结果 |
| `response.json()` 读取响应头吗？ | 它解析响应体；响应头通过 `response.headers` 访问 |
| TestClient 是服务器吗？ | 它是调用应用的测试客户端；普通网络服务由 Uvicorn 等服务器接收请求 |
| `@pytest.fixture` 是否立刻运行函数体？ | 本例按测试对 fixture 的需要来执行，装饰器先登记管理关系 |
| yield TestClient(app) 给谁？ | 创建客户端对象，先给 pytest，再给测试函数的参数 |
| yield 后面的 pop 是否马上运行？ | fixture 暂停；pytest 在测试收尾时恢复它，才执行后面的代码 |
| 为什么替换语句写在 fixture 里？ | 让测试前设置、测试后删除的时机可以一起管理 |
| dependency_overrides 是否修改原函数？ | 它登记替换规则，供 FastAPI 解析 Depends 时使用 |
| lambda 什么时候返回表？ | FastAPI 后续调用这个临时函数时 |
| pop 删除了 get_token_table 函数吗？ | 删除的是替换字典中的条目 |
| param 与 parametrize 一样吗？ | param 定义一组参数；parametrize 将多组参数绑定到测试函数并生成用例 |
| id 会传给测试函数或服务器吗？ | 它是 pytest 用例名称，不是接口数据 |
| Iterator[TestClient] 是否让 pytest 创建对象？ | 类型标注描述提供的对象类型，创建对象的是 TestClient(app) |

## 20. 复习检查与参考资料

### 20.1 理解检查

尝试不看正文，自己解释以下问题。能复述与能独立修改、运行和排查问题，应分别确认。

1. `git status -s` 的 ` M` 与 `M ` 有什么区别？
2. `Authorization` 和 `WWW-Authenticate` 各是谁发送的？
3. `HTTPBearer()` 和处理请求时调用 `bearer_scheme` 有什么区别？
4. `credentials` 与 `credentials.credentials` 各是什么？
5. `headers=headers` 两边分别是什么？
6. fixture 的 yield 提供哪个对象，最终由谁使用？
7. 设置、使用和删除依赖替换分别发生在什么时候？
8. 空请求头场景为什么仍需要检查响应头中的 Bearer？
9. `pytest.param` 与 `parametrize` 分别负责什么？
10. 三条认证失败断言分别检查响应的哪一部分？

参考答案：

1. 前者修改未暂存，后者修改已暂存；两列位置不同。
2. Authorization 随客户端请求发送；WWW-Authenticate 随服务端响应发送，告知认证要求。
3. 前者创建工具实例，后者让这个实例处理当前请求。
4. 前者是结果对象，后者是该对象中的 token 字符串字段。
5. 左边是 get 方法参数名，右边是提供请求头数据的变量。
6. 提供 TestClient(app) 创建的客户端对象；pytest 接收后传给测试函数的 client 参数。
7. fixture 在 yield 前设置；测试发请求解析依赖时使用；测试结束后在 yield 后删除。
8. 请求未提供认证信息，响应可以告知应采用的认证方案；请求头与响应头方向不同。
9. param 定义一组输入并可附带名称；parametrize 将各组输入交给指定测试参数，生成多个用例。
10. status_code 检查状态码，response.headers 检查响应头，response.json() 检查解析后的响应体。

### 20.2 项目中的对应位置

以下路径以项目根目录为基准：

| 文件 | 本次内容 |
| --- | --- |
| `app/main.py` | FastAPI 应用、/health、/api/v1/me、MeResponse |
| `app/auth.py` | HTTPBearer、令牌文件加载、get_token_table、get_current_principal |
| `app/domain/models.py` | Principal、Role 等业务类型 |
| `tests/test_health.py` | TestClient 与基本响应断言 |
| `tests/test_auth.py` | 测试令牌表、fixture、依赖替换、参数化认证测试 |
| `tests/test_policy.py` | 多参数的权限场景测试 |
| `requirements.txt` | 项目记录的依赖版本 |

整理时 `requirements.txt` 记录 FastAPI 0.162.2、Uvicorn 0.54.0、pytest 9.2.0。版本行为应以项目实际安装环境为准，尤其不要把旧版认证错误码直接套用到当前版本。

### 20.3 官方参考资料

- [HTTP/1.1 消息结构：RFC 9112 第 2.1 节](https://www.rfc-editor.org/rfc/rfc9112.html#section-2.1)：请求与响应的组成。
- [FastAPI：HTTPBearer 与认证结果类型](https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPBearer)：提取方案、凭据及 auto_error。
- [FastAPI：可调用实例依赖](https://fastapi.tiangolo.com/advanced/advanced-dependencies/#a-callable-instance)：实例作为依赖及调用结果的注入。
- [FastAPI：直接使用 Request](https://fastapi.tiangolo.com/advanced/using-request-directly/) 与 [Request 类型参考](https://fastapi.tiangolo.com/reference/request/)：请求对象、HTTPConnection 关系。
- [Uvicorn 官方介绍](https://uvicorn.dev/) 与 [配置说明](https://uvicorn.dev/settings/)：服务器职责、应用路径、端口及 reload。
- [FastAPI：接口测试](https://fastapi.tiangolo.com/tutorial/testing/)：TestClient 的使用。
- [FastAPI：测试中的依赖替换](https://fastapi.tiangolo.com/advanced/testing-dependencies/)：dependency_overrides 的键和值。
- [FastAPI：错误响应与自定义响应头](https://fastapi.tiangolo.com/tutorial/handling-errors/#add-custom-headers)：HTTPException 的 headers 参数。
- [pytest：fixture 与 yield 清理](https://docs.pytest.org/en/stable/how-to/fixtures.html#yield-fixtures-recommended)：准备、提供对象和收尾的时机。
- [pytest：参数化测试](https://docs.pytest.org/en/stable/how-to/parametrize.html)：parametrize 的参数和多组用例。

官方文档可能随版本更新。笔记中的项目行为描述依据本次读取的源文件和此前对项目安装实现的核对；示例用于学习，不作为生产环境身份与权限设计已完成的证据。

## 21. monkeypatch：临时修改测试环境

这是整理笔记期间补充的知识点。下面是教学示例；本次搜索当前 `tests` 目录，没有发现已有的 monkeypatch 用法，也没有向业务测试文件添加这些示例。

### 21.1 是什么

`monkeypatch` 是 pytest 内置的 fixture，提供在测试期间临时修改环境变量、对象属性、字典条目等操作。pytest 在相应收尾阶段自动撤销通过它登记的修改。

```text
测试前：保留原来的状态
    ↓
测试中：临时改变配置或替换行为
    ↓
测试结束：pytest 撤销这些修改
```

### 21.2 环境变量示例

```python
import os


def test_config(monkeypatch):
    monkeypatch.setenv("RDA_DEMO_TOKENS_FILE", "test-data/tokens.json")

    path = os.environ.get("RDA_DEMO_TOKENS_FILE")
    assert path == "test-data/tokens.json"
```

1. 测试参数名 `monkeypatch` 请求 pytest 内置的同名 fixture。
2. pytest 提供一个能登记临时修改的工具对象。
3. `.setenv(名称, 值)` 在当前测试进程中设置环境变量。
4. 后面的代码读取到临时值。
5. pytest 收尾时恢复原值；如果原来不存在，就删除这次新增的变量。

这行只设置路径字符串，JSON 文件仍需要另行准备。它不修改已经在其他终端运行的服务进程，也不把配置永久写入系统设置。

### 21.3 测试没有环境变量的情况

项目当前的 `get_token_table` 在没有环境变量时返回空表，可以用下面的教学用例表达这个预期：

```python
from app.auth import get_token_table


def test_missing_tokens_config(monkeypatch):
    monkeypatch.delenv("RDA_DEMO_TOKENS_FILE", raising=False)
    assert get_token_table() == {}
```

`delenv` 临时删除环境变量；`raising=False` 表示原来没有这个变量时不报错。收尾时恢复之前的状态。

### 21.4 和 dependency_overrides 的关系

| 工具 | 作用 |
| --- | --- |
| `app.dependency_overrides` | FastAPI 的依赖替换表，指定解析某个 Depends 时调用哪个替代函数 |
| `monkeypatch` | pytest 的临时修改工具，记录并在收尾时撤销相应修改 |

例如，可以让 monkeypatch 管理替换字典中的一条记录：

```python
monkeypatch.setitem(
    app.dependency_overrides,
    get_token_table,
    lambda: TEST_TOKEN_TABLE,
)
```

`setitem` 临时设置字典条目。FastAPI 仍然通过 `dependency_overrides` 执行依赖替换；monkeypatch 负责登记字典改动并在收尾时恢复原状态。

这只是说明两者可以配合使用，不表示必须改写现有 fixture。本次笔记保留了原来的赋值、yield、pop 写法。

### 21.5 常见方法速查

| 方法 | 用途 |
| --- | --- |
| `setenv(名称, 值)` | 临时设置环境变量 |
| `delenv(名称, raising=False)` | 临时删除环境变量，原来没有也不报错 |
| `setitem(字典, 键, 值)` | 临时设置字典条目 |
| `setattr(对象, 属性名, 替代值)` | 临时替换指定位置的属性，也可用于替换函数引用 |

函数替换需要针对被测代码实际查找的引用位置。刚接触时，可以先理解环境变量的设置与恢复，再学习函数替换。

官方参考：[pytest monkeypatch 文档](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)。本次检查了笔记中 Python 示例的语法，没有执行这些测试用例。
