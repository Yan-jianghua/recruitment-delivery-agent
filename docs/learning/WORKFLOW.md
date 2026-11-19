# 开发流程与进度
## 当前活动任务

- 编号：RDA-B0-001。
- 目标：建立招聘职位交付 Agent 的安全底座：身份、租户、候选人同意、资源 ACL 和最小数据模型。
- 状态：DOING。
- 当前岗位：产品与技术负责人。
- 操作者：开发者亲手操作，导师讲解和核验。
- 起点：main，提交 d8c58ba。
- 任务分支：feat/rda-b0-001-persistence（用于第三次合并，从 main 88c873a 创建）。前两次合并用的 feat/rda-b0-001-security-foundation 和 feat/rda-b0-001-resume-api 都已在合并后删除。
- 任务卡：docs/09_今日任务-2026-11-08.md。
- 前项完成证据：RDA-B0-000 规划基线已通过 PR #2 合并。
- 当前交付：第一次合并已完成（3 号 PR，main 9d7fad5，14 passed）。第二次合并已完成（4 号 PR，main 88c873a，46 passed，CI 通过），RDA-001~007 已有测试输出。第三次合并进行中：Docker 与 PostgreSQL、数据持久化、数据库迁移和 RDA-008。
- 合并计划（2026-11-11 决定）：本任务分三次合并到 main，每次单独验收。
  1. 门卫规则、测试与代码检查工具（RDA-001~006）：已完成。3 号 PR 于 2026-11-11 以 squash 方式合并，main 提交为 9d7fad5。
  2. 查看简历接口、RDA-007 与 CI：已完成。4 号 PR 于 2026-11-19 以 squash 方式合并，main 提交为 88c873a。  3. 数据持久化、数据库迁移与 RDA-008：再从 main 新开分支。
  3. 数据持久化、数据库迁移与 RDA-008：进行中，分支 feat/rda-b0-001-persistence。
- 完成条件：三次合并全部完成后，8 个安全用例都有实际测试输出，代码和迁移可运行。

## 项目启动时的检查快照

- Git 已初始化，当前分支为 main。
- 启动快照记录于项目基线建立前，后续已建立提交和远程仓库。
- 项目虚拟环境为 .venv，Python 3.12.10，可正常运行。
- 尚无业务代码和应用测试。
- PyCharm 是否选择项目解释器仍待核验。

## 本任务范围

明确模块调用关系、身份与权限校验位置、
数据结构、处理状态以及接口正常和异常响应。

## 提交计划

- 编号：C01。
- 分支：main，仅本次初始基线使用。
- 文件：.gitignore、README.md、docs/learning/WORKFLOW.md。
- 检查：文件内容正确；环境与缓存被忽略；提交清单准确。
- 提交说明：chore(project): 建立企业RAG项目基线。
- 实际提交哈希：8769cd3。
- 核验结果：三个文件正文已提交，main 工作区干净。
- 完成范围：项目基线已提交，并上传 GitHub 的 main 分支。
- 远程核验：origin/main 对应提交 8769cd3。

## 后续开发规则

首次提交后，每项任务从已核验的 main 创建短期分支。
明确需求与验收，再设计和实现。
检查通过并审查差异后提交。
配置远程后，通过 PR、CI 和审查推进合并。
发布时分别核验版本、部署和实际业务路径。

## 学习验证

按指导完成与能够独立完成分别记录。
具体分工见各任务进度记录中的"开发者亲手完成"和"导师应要求完成"两项。

## RAG-B0-001提交记录

- 编号：C02。
- 目的：形成可审查的 B0 需求与验收草案。
- 文件：docs/01_B0需求与验收.md、docs/learning/WORKFLOW.md。
- 提交前检查：场景明确、权限无歧义、验收可观察、差异符合范围。
- 提交说明：docs(requirements): 明确B0场景与权限验收。
- 前置提交：8769cd3。
- 实际提交哈希：1da96d6。
- 推送结果：需求任务分支已上传 GitHub，并建立远程跟踪关系。
- 检查结果：已核对需求范围、权限规则和 9 项验收条件；业务功能尚未实现，验收尚未执行。
## 下一动作

核验检索接口的请求与响应约定。
继续确定具体检索规则、引用接口和通用错误响应。
提交前统一整理重复说明，并检查设计与验收条件的对应关系。


## RAG-B0-001 完成记录

PR #1 已合并，main 提交为 263591a。
本地主分支已同步，核验时工作区干净。
完成范围为需求文档交付，业务功能及业务验收尚未完成。

## 2026-11-07 规划基线更新

仓库审计已确认当前分支为 docs/RAG-B0-002-design，HEAD 为 2e009e1，main 与 origin/main 为 263591a。工作区存在本任务的未提交设计修改，当前没有业务源代码、数据库迁移、接口测试、前端应用、CI、部署或真实企业接入。

本轮前置工作已新增并纳入追踪：

- docs/00_项目总体规划.md
- docs/03_招聘市场与Agent机会研究.md
- docs/04_企业级定制Agent架构与安全边界.md
- docs/05_企业接入与安全基线.md
- docs/06_业务验收场景与交付包.md
- docs/07_前置工作包与对接清单.md
- docs/REPO-AUDIT-2026-11-07.md

当前规划结论是先做招聘职位交付与候选人证据的垂直切片。B0 仍以权限治理 RAG、引用和动作预览为开发入口。真实身份、真实系统连接器、企业试点和甲方签收仍为待验证项。


## 证据规则

规划文档只能证明设计已经写下。代码、测试、推送、合并、部署、真实连接器和企业认可分别需要自己的证据。没有实际输出的项目状态保持为待验证。
## 2026-11-08 今日任务

- 任务编号：RDA-B0-001。
- 任务目标：启动招聘职位交付 Agent 的身份、租户、候选人同意、资源 ACL 和最小数据模型。
- 任务卡：docs/09_今日任务-2026-11-08.md。
- 当前状态：准备开始。
- 目标分支：feat/rda-b0-001-security-foundation。
- 进入条件：先核验当前未提交规划改动，再由用户从已核验的 main 创建实现分支。
- 完成条件：8 个安全用例有实际测试输出，代码和迁移可运行，提交哈希和工作区状态已记录。

## RDA-B0-000 完成记录（2026-11-09）

- 原规划分支 docs/RAG-B0-002-design（提交 2e009e1、7c350bf）含开发工具生成的 .dsh-ops/ 运行记录，未推送，只在本地保留。
- 新建分支 docs/rda-b0-002-design，从 main 263591a 带入 README 和 docs，不带 .dsh-ops/。
- 提交 469f6e1：建立招聘交付 Agent 规划基线，去除仓库地址、外部来源链接和可识别地区的统计数字。
- 提交 36d680b：在 02、03 标注订单履约内容属于第二领域包，修正 00 中 B2 阶段描述。
- 提交前检查：暂存文件清单、与原规划分支的差异、外部链接、本机路径、邮箱和密钥类字符串。
- PR #2 以 squash 方式合并，main 提交为 d8c58ba；远程分支 docs/rda-b0-002-design 已删除。
- 本地已删除 docs/rda-b0-002-design 和命名有误的 feat/reat/rda-b0-001-security-foundation，并从 main d8c58ba 创建 feat/rda-b0-001-security-foundation。
- 未处理：01 正文的场景和验收矩阵仍以订单履约为主，B0 以开头说明、08 和 09 为准；部分文件有行尾空格等排版问题；文档内相对链接未逐一复核。

## RDA-B0-001 进度记录（2026-11-10）

- 提交 2ef82f7：新增 app/domain/models.py（数据模型）、app/domain/policy.py（门卫规则）和 tests/test_policy.py，并为已有代码补充中文注释，共 8 个文件。
- 推送：分支已推送到 GitHub 同名分支，并建立了跟踪关系。推送时分支头为 745cca9（进度记录提交）。已用 gh 核对，远程分支头与本地一致；旧分支 docs/RAG-B0-002-design 不在远程。
- 清理：PR #1 已于 2026-11-06 合并。远程分支 docs/RAG-B0-001-scope 的分支头 f89e7cf 与合并时一致，没有之后的新提交，已删除；本地同名分支保留。
- 门卫检查顺序：同意书归属 → 公司 → 项目 → 授权记录 → 同意书有无 → 同意书状态。任何一条不满足立即拒绝，全部通过才放行。
- 设计决定：
  - 跨公司访问返回 NOT_FOUND，不抛异常，避免泄露候选人是否存在。
  - 同意书不属于该候选人或该公司，视为调用方 bug，抛出 ValueError。
  - 同意书状态只认 ACTIVE，其他状态一律拒绝。
  - 项目管理员同样需要自己的授权记录，没有例外。
- 测试结果：13 passed（test_health 1 个，test_policy 12 个）。1 个 warning 是 Starlette 测试客户端对 httpx 的弃用提示。
- 覆盖范围：RDA-001~006 各 1 个测试；授权记录细节 4 个；同意书归属 2 个。
- 变异测试：在临时副本中逐一改坏 policy.py 的 12 处，测试发现了 11 处。"授权不核对动作"暂时无法测试，因为 Action 只有 READ_RESUME 一个值。
- 开发者亲手完成：
  - models.py。
  - policy.py 的提前返回结构、has_grant 和 ensure_consent_belongs_to。
  - RDA-001~005 与"没有授权"的测试初稿，以及按示范写入的同意书归属 2 个测试。
  - 删除误导入，清理无用导入和残留注释。
- 导师应要求完成：
  - policy.py 最后两处修正：同意书状态比较，以及简化"没有同意书"的条件。
  - RDA-006 与 3 个授权细节测试。
  - 按需求文档更正测试编号与名字。
  - 为全部代码补充中文注释，保留了开发者自己写的行尾注释。
- 未完成：
  - RDA-007（接口层）：请求里的 tenant_id、user_id 不能改变服务端认定的身份。
  - RDA-008（数据库阶段）：重复提交同一同意版本，结果相同。
  - 数据库迁移尚未开始。

## RDA-B0-001 进度记录（2026-11-11，第 2 课）

- 第 2 课内容：import 的查找顺序（sys.path）、Ruff、mypy、pytest 参数化测试。
- 提交（均已推送，已用 gh 核对远程分支头）：
  - d0d0657：加入代码检查工具 Ruff 0.17.4。
  - 83db2a6：用 Ruff 整理导入顺序和代码格式。
  - 0314f61：加入 mypy 2.4.1，在 pyproject.toml 开启 strict_equality。
  - a18d809：把测试文件的导入注释挪回原位。
  - 85a8288：用参数化合并结构相同的门卫测试。
  - bd70f62：补充"管理员有自己的授权时放行"的用例（RDA-006 的另一半）。
- 检查结果（bd70f62）：
  - pytest：14 passed（test_health 1 个，test_policy 13 个）。1 个 warning 同前，是 Starlette 测试客户端对 httpx 的弃用提示。
  - ruff check：All checks passed!
  - ruff format --check：24 files already formatted。
  - mypy app tests：Success: no issues found in 8 source files。
- 测试结构：test_policy.py 原来的 12 个测试函数结构相同，合并为两个参数化测试。判断结果表 11 行，同意书归属表 2 行。判断结果表用 `# fmt: off` 和 `# fmt: on` 保持一行一个场景。
- 变异测试（在临时副本中进行）：
  - 参数化改造后重做，12 处改坏仍发现 11 处，与改造前相同。"授权不核对动作"仍无法测试。
  - 新增用例能发现"管理员一律被拒绝"的错误，改造前的测试发现不了。
- 开发者亲手完成：
  - 安装 Ruff 和 mypy，修改 requirements.txt、pyproject.toml 和 .gitignore。
  - 用 Ruff 整理代码，替换参数化后的测试，并运行四项检查。
  - 以上 6 个提交和推送。
  - 课后练习：新增"管理员有授权时放行"的用例，并按核验意见改正注释编号和缩进。
- 导师应要求完成：
  - 讲解中的示范代码，以及参数化后的 test_policy.py 全文。都先在临时副本中验证，再交给开发者替换。
  - 核验每次提交、推送和检查输出。
- 第一次合并：3 号 PR 已合并，见下方的第一次合并记录。

## RDA-B0-001 第一次合并记录（2026-11-11）

- 3 号 PR：feat/rda-b0-001-security-foundation → main，共 13 个提交，以 squash 方式合并。main 提交为 9d7fad5，它的父提交是 d8c58ba。
- 核验：
  - main 新提交的 tree（ac47b92）和审查过的分支最后一个提交 c06946f 的 tree 相同，内容一致。
  - 在合并后的 main 上运行四项检查：14 passed；ruff check、ruff format --check、mypy 都通过。
  - 仓库没有 CI，以上都是本地运行结果。
- 选择 squash 的理由：
  - 和 1、2 号 PR 的做法一致。
  - 默认标题里没有账号名。
  - 分支上的提交仍可在 3 号 PR 的 Commits 页查到，本文件里引用的 d0d0657 到 c06946f 等哈希都在那里。
- 合并后误点了 Revert 按钮，GitHub 因此生成了撤销分支 revert-3-feat/rda-b0-001-security-foundation。这个分支没有开 PR，main 没受影响，分支已删除。
- 清理：
  - GitHub 上的功能分支和撤销分支都已删除。
  - 本地功能分支已删除。squash 合并后要用 `git branch -D` 删除，删除前先确认 `git diff main <功能分支>` 没有输出。
  - `git fetch --prune` 清掉了 origin/docs/RAG-B0-001-scope 这条旧记录。
- 清理后核验：本地 main、origin/main 和 GitHub 上的 main 都是 9d7fad5，GitHub 上只剩 main 一个分支。
- 第二次合并：2026-11-12 从 main 9d7fad5 创建分支 feat/rda-b0-001-resume-api。

## RDA-B0-001 进度记录（2026-11-19，第 3 课）

- 第 3 课内容（W1～W4）：HTTP 的 Bearer 令牌认证和 401；FastAPI 的依赖注入（Depends、dependency_overrides）和 APIRouter；pytest 的 fixture、monkeypatch、tmp_path 和 conftest.py；仓库模式；200、403、404 的状态码设计；伪造身份测试；GitHub Actions 持续集成和 YAML。
- 提交（分支 feat/rda-b0-001-resume-api，共 13 个，均已推送，已用 gh 核对远程分支头）：
  - de4844f：记录第一次合并结果，开始第二次合并。
  - 85863ee：逐日计划，元旦前完成，留 7 天空档。
  - 47fd95d：演示令牌认证和 /api/v1/me。只提交了 app/auth.py 和一个空的 tests/test_auth.py，其余文件漏了。
  - ed88fd9：11-16 的学习笔记。
  - b43ce21：补上 47fd95d 漏掉的 /api/v1/me、认证测试和配置。没有改写历史，用新提交补上。
  - adf07ad：删除 11-16 的学习笔记，开发者有意删除。
  - a328631：改正两个测试函数名，在 .gitignore 里忽略 pytest 临时文件夹。同时带进了空的 app/api/__init__.py 和 app/api/me.py。
  - 9a8551c：用 APIRouter 把 /api/v1/me 拆到 app/api/me.py。
  - 6a8ae96：内存数据仓库和演示数据。
  - 69b6caf：查看简历接口 GET /api/v1/candidates/{candidate_id}/resume。
  - 7381407：RDA-007 伪造身份测试。
  - 8c2e27e：GitHub Actions 持续集成。提交进去的 ci.yml 是空文件，GitHub 运行 44443043878 失败（workflow file issue，没有运行任何任务）。
  - 5533bb0：补上 ci.yml 的内容，GitHub 运行 44444791053 全部通过。
- 检查结果：
  - CI（5533bb0，GitHub 运行 44444791053，Ubuntu，Python 3.12.16）：pytest 46 passed，1 个 warning 同前；ruff check：All checks passed!；ruff format --check：34 files already formatted；mypy app tests：Success: no issues found in 17 source files。
  - 本地（7381407，之后只改了 ci.yml）：结果相同。在只按 requirements.txt 新建的虚拟环境里也全部通过，说明依赖写全了。
- 测试结构（46 个）：
  - test_health.py 1 个，test_policy.py 13 个，test_auth.py 7 个，test_repository.py 7 个，test_candidates_api.py 18 个。
  - 接口测试：只返回授权字段 1 个；STATUS_CASES 9 个场景（RDA-001～006、没有授权、查无此人）；别家公司与不存在的候选人的 404 完全相同 1 个；四种拒绝的 403 完全相同 3 个；不带令牌返回 401 1 个；RDA-007 的三种伪造方式（查询参数、请求头、请求体）3 个。
  - client fixture 和测试令牌表放在 tests/conftest.py，多个测试文件共用。
- 变异测试（在临时副本中进行，46 个测试）：
  - 接口相信查询参数里的 tenant_id、请求头 X-Tenant-Id、请求体里的 tenant_id、查询参数里的 user_id：每种只有对应的 RDA-007 场景失败（assert 403 == 200）。
  - 403 改成 404：8 个失败。跳过放行检查：8 个失败。响应多一个字段：1 个失败。403 的提示里写进具体原因：3 个失败，只有"四种拒绝完全相同"的测试能发现。
  - 去掉接口里的 NOT_FOUND 分支：现有测试发现不了。仓库查询已经按公司过滤，这个分支是安全兜底，以后用故意出错的仓库来测。
- 开发者亲手完成：
  - 照讲解写出认证、路由拆分、内存仓库、查看简历接口和 RDA-007 测试，运行四项检查，完成以上 13 个提交和推送。
  - 新建 ci.yml，在 GitHub 的 Actions 页面查看运行结果。
- 导师应要求完成：
  - 讲解中的示范代码和测试代码，都先在临时副本中验证，再交给开发者。
  - 块 3 中按开发者的要求直接修改了 4 个文件：改正打错的令牌名、状态码名和方法名，补回被误删的一行，改用 fastapi 的 Depends 导入，改正注释错字，并加上"四种拒绝完全相同"的测试。
  - 核验每次提交、推送、检查输出和 CI 运行。
- 教训：
  - PyCharm 新建文件时会自动把空文件加入暂存区，47fd95d、a328631、8c2e27e 都因此带进了空文件。提交前看 `git status -s` 的第二列是否为空，新文件再用 `git diff --cached --stat` 看行数。
  - 手打的字符串和名字容易出错（例如 test-token-admain、HTTP_404_NOT_FOUN），每次提交前先跑测试。
  - 第二次合并：4 号 PR 已合并，见下方的第二次合并记录。

## RDA-B0-001 第二次合并记录（2026-11-19）

- 4 号 PR：feat/rda-b0-001-resume-api → main，共 14 个提交，以 squash 方式合并。main 提交为 88c873a，它的父提交是 9d7fad5。
- 核验：
  - main 新提交的 tree（1c6278f）和审查过的分支最后一个提交 d42b779 的 tree 相同，内容一致。
  - 4 号 PR 页面上的 CI 检查通过。
  - 合并后 main 上的 CI（GitHub 运行 44447134060）通过：pytest 46 passed；ruff check、ruff format --check（34 files）、mypy（17 source files）都通过。第一次合并时仓库还没有 CI，这是第一次用 CI 的结果核验合并。
  - 工作流文件进入 main 之后，GitHub 显示的工作流名字才从文件路径变成 CI。
- 选择 squash 的理由：
  - 和 1～3 号 PR 一致，main 上一次合并只留一个提交。
  - 分支上的 14 个提交仍可在 4 号 PR 的 Commits 页查到，本文件里引用的 de4844f 到 d42b779 等哈希都在那里。
- 清理：
  - GitHub 上的功能分支已删除。
  - 本地功能分支已删除。squash 合并后用 `git branch -D` 删除；内容一致已由上面的 tree 比较证明。
  - origin/feat/rda-b0-001-resume-api 这条本地记录已清掉。
  - 已清掉一条失效的工作树记录，并删除了对应的本地分支 claude/compare-rank-four-projects-c19d02，它和 9d7fad5 是同一个提交。
- 清理后核验：本地 main、origin/main 和 GitHub 上的 main 都是 88c873a，GitHub 上只剩 main 一个分支。
- 第三次合并：2026-11-19 从 main 88c873a 创建分支 feat/rda-b0-001-persistence。

## 教学说明规则

用户要求每行代码、每条命令以及关键词组合都得到解释。后续操作必须同时给出命令结构、参数含义、组合效果、预期结果和失败处理。用户执行后再依据实际输出进入下一步。
用户要求导师给出的每段代码都带中文注释，说明作用、设计理由和不直观的语法，注释必须准确。
