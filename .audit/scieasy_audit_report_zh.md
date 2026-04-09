# SciEasy 审计报告（中文版）

日期：2026-04-08
仓库：`C:\Users\jiazh\Desktop\workspace\SciEasy`
审计基线提交：`e14dcb5`（`fix(#401): bump core package version to 0.2.1 (#402)`）

## 执行摘要

这次审计发现的主线问题很明确：仓库中有多项 roadmap / spec 任务是以 skeleton 或半成品形式合入的，但仓库当前的文档、导出面和包结构已经在对外“表现得像已经完成”。风险最高的几项如下：

1. Stage 10.1 的 palette / API 分组重构仍然停留在 Part 1 skeleton，但代码和文档已经开始按“完成版”叙述。
2. `BlockTestHarness` 没有实现 ADR-026 / issue `#215` 里承诺的 SDK 契约。
3. `scieasy-blocks-srs` 目前不能作为标准插件包被发现。
4. `scieasy-blocks-lcms` 目前也不能作为标准插件包被发现，而且 T-LCMS-020/021 的收尾工作仍未完成。
5. Phase 11 的“全插件集成测试”策略在仓库根目录下无法执行。
6. `ARCHITECTURE.md` 承诺存在一整套 `docs/block-development/` 文档，但仓库中并没有该目录。

我没有修改任何现有代码或现有文档。本次只新增了英文和中文两份审计报告。

## 审计方法

- 阅读 `README.md`、`docs/architecture/ARCHITECTURE.md`、`docs/guides/block-sdk.md` 以及 Phase 11 相关 specs。
- 检查 `src/`、`frontend/`、`packages/` 下的关键实现。
- 运行定向验证：
  - `pytest --no-cov tests/testing/test_harness.py tests/api/test_blocks.py tests/blocks/test_registry.py tests/architecture -q`
  - `pytest --no-cov packages/scieasy-blocks-imaging/tests/test_packaging.py packages/scieasy-blocks-srs/tests/test_types.py packages/scieasy-blocks-lcms/tests/test_types.py -q`
- 使用 `git blame` / `git log` 追溯引入 PR。
- 使用 GitHub issue 查询确认问题是否已经被登记。

## 发现总览

| ID | 严重度 | 领域 | 摘要 | 现有 issue? |
|---|---|---|---|---|
| F1 | 高 | 文档 / API / 前端 | Stage 10.1 palette 分组仍是 skeleton，但仓库已经把它当成完成契约在暴露 | 是：`#250`、`#251` |
| F2 | 高 | SDK / Testing | `BlockTestHarness` 不符合文档宣称的 ADR-026 契约 | 部分相关：原始功能 issue `#215`；未找到单独缺陷 issue |
| F3 | 高 | SRS 插件 | `scieasy-blocks-srs` 缺少 entry-point wiring 和 `get_blocks()`，因此无法被发现 | 未找到匹配的缺陷 issue |
| F4 | 高 | LC-MS 插件 | `scieasy-blocks-lcms` 仍缺少 entry-point wiring、`get_blocks()` 以及 T-LCMS-020/021 的收尾交付 | 有相关延后 issue `#345`；未找到缺陷 issue |
| F5 | 中 | 测试架构 | Phase 11 全插件测试方案没有接到 repo root，且从 root 执行会失败 | 未找到匹配 issue |
| F6 | 中 | 文档完整性 | `ARCHITECTURE.md` 承诺的 `docs/block-development/` 文档集并不存在 | 未找到匹配 issue |

## 详细问题

### F1. Stage 10.1 的 palette/API 分组重构仍停留在 skeleton，但仓库已经按完成态描述它

严重度：高
分类：架构文档一致性、重构未完成、代码/设计不一致

要求 / 设计行：

- `docs/design/stage-10-1-palette.md:29-35` 定义了 Stage 10.1 的目标行为：显式 `category` override、暴露 `source`、Tier 1 归为 “Custom”、前端渲染 Package -> Category -> Block 三层树。
- `docs/design/stage-10-1-palette.md:44-49` 明确 Part 2 必须实现真实 `_infer_category`、API 字段暴露、以及 `BlockPalette.tsx` 重写。
- `docs/guides/block-sdk.md:244-270` 已经对外宣称 GUI palette 按 package 和 category 分组。

实际实现行：

- `src/scieasy/api/schemas.py:95-101` 已经定义了 `source` 和 `package_name` 字段。
- `src/scieasy/api/routes/blocks.py:42-58` 的 `_summary()` 仍然保留 TODO，实际上没有填充这两个字段。
- `src/scieasy/blocks/registry.py:555-583` 仍然没有实现 `category` ClassVar override，source 重命名也没有完成。
- `frontend/src/components/BlockPalette.tsx:5-27` 直接注明三层树仍是 TODO。
- `frontend/src/components/BlockPalette.tsx:39`、`frontend/src/components/BlockPalette.tsx:82-92`、`frontend/src/components/BlockPalette.tsx:146-149` 说明当前实现仍然只是按扁平 category 分组。
- `tests/api/test_blocks.py:89-105` 与 `tests/blocks/test_registry.py:439-480` 中与 Stage 10.1 对应的测试仍然是 skipped。

违反原因：

- 设计文档和 SDK guide 描述的是 package-aware 的完成态契约，但 backend 并没有真正输出对应元数据，frontend 也没有实现三层树。
- 这不是单纯“后续计划”，而是已经有 schema 字段、已有测试、已有 TODO 注释，但实现没有跟上。

影响：

- 插件 package 无法按文档所述在 UI 中被分层展示。
- API 消费方拿到的是空的 `source` / `package_name`，但模型又宣称这些字段存在。
- 文档对当前产品能力有明显高估。

引入 PR 来源：

- PR `#159` 建立了当前 Phase 7-8 的扁平 editor/API 基线。
- PR `#251`（`6441de9d`，Stage 10.1 Part 1）只合入了 skeleton/TODO 版本，把真正实现留给未合入的 Part 2。

是否已在 issue 中列出：

- 是。已有 issue `#250`（Stage 10.1 跟踪）和 `#251`（Part 1 skeleton）。

建议：

- 要么尽快补完 Stage 10.1 Part 2；
- 要么立即回调文档描述，使其只反映当前“按 flat category 分组”的真实状态。

### F2. `BlockTestHarness` 没有实现 ADR-026 / issue `#215` 宣称的 SDK 契约

严重度：高
分类：代码/设计不一致、实现不足

要求 / 设计行：

- issue `#215` 要求：
  - `run(inputs, params) -> dict`
  - 原始数据自动包装成 `DataObject` / `Collection`
  - 自动构造 `BlockConfig`
  - 输出 materialize helper
- `docs/architecture/ARCHITECTURE.md:2653-2678` 文档示例直接使用 `BlockTestHarness.run(...)`，并声明它会包装原始数据、创建临时 project 结构、校验输出、materialize 输出。
- `docs/guides/block-sdk.md:1290-1310` 再次重复了同样的 `harness.run(...)` 契约和职责。

实际实现行：

- `src/scieasy/testing/harness.py:48-120` 只做了浅层 class/port/name 检查。
- `src/scieasy/testing/harness.py:154-220` 只校验 entry-point callable 结构，并没有实现 richer block execution contract。
- `src/scieasy/testing/harness.py:226-267` 只实现了 `smoke_test(...)`，根本没有 `run(...)` 方法。
- `src/scieasy/testing/harness.py:261-267` 只是实例化 block，然后把 `inputs` 原样传给 `instance.run(inputs, config)`；没有 raw-data wrapping、没有 temp-project、没有输出类型校验、没有 materialization。

违反原因：

- 对外文档和架构文档暴露的公共 API 是 `run(...)`，而实际代码只有 `smoke_test(...)`。
- 文档承诺的主要职责大部分都没有落地。
- 外部 block 作者如果按 SDK guide 写测试，会直接撞到一个不存在的 API。

影响：

- SDK 文档具有误导性。
- 对外测试辅助工具的能力比文档宣称的弱很多。
- 外部 block package 可以通过“smoke test”，但并不具备文档承诺的输入包装 / 输出 materialize 保障。

引入 PR 来源：

- PR `#215`（`2f567799`）引入了当前这个最小版实现。
- PR `#217`（`056dda76`）以及后续架构文档更新，又把它描述成了更完整的 ADR-026 版本。

是否已在 issue 中列出：

- 原始目标已在 issue `#215` 中列出。
- 但我没有找到一个单独的 bug/regression issue 明确指出当前实现仍低于该契约。

建议：

- 两种方式二选一：
  - 真的把 `run()` / wrapping / materialization / output validation 补齐；
  - 或者立刻修正文档，只把 `smoke_test(...)` 作为真实 public surface 来描述。

### F3. `scieasy-blocks-srs` 目前不能作为标准插件包被发现

严重度：高
分类：Phase 11 未完成实现、打包缺陷

要求 / 设计行：

- `docs/specs/phase11-srs-block-spec.md:516-519` 要求 SRS 的 `pyproject.toml` 声明：
  - `scieasy.blocks`: `srs = "scieasy_blocks_srs:get_blocks"`
  - `scieasy.types`: `srs = "scieasy_blocks_srs.types:get_types"`
- `docs/specs/phase11-srs-block-spec.md:527-530` 要求顶层存在 `get_blocks()` / `get_types()`。
- `docs/specs/phase11-srs-block-spec.md:1600-1659` 定义了 T-SRS-013：`get_blocks()` 要返回全部 11 个 block，`get_types()` 返回 `[SRSImage]`，registry scan 和 entry-point tests 必须通过。
- `docs/specs/phase11-srs-block-spec.md:1675-1778` 让 T-SRS-014 的 cross-plugin E2E 依赖这一步 wiring。

实际实现行：

- `packages/scieasy-blocks-srs/pyproject.toml:5-23` 完全没有 `[project.entry-points."scieasy.blocks"]` 或 `[project.entry-points."scieasy.types"]`。
- `packages/scieasy-blocks-srs/src/scieasy_blocks_srs/__init__.py:5-8` 只 re-export 了 4 个 preprocess block 和 `SRSImage`，并没有定义 `get_blocks()`。
- `packages/scieasy-blocks-srs/src/scieasy_blocks_srs/types.py:98-104` 虽然提供了 `get_types()`，但由于 pyproject 没有注册 entry point，标准 packaging contract 下它仍然不可发现。
- `src/scieasy/blocks/registry.py:415-418` 表明 monorepo fallback 只识别 `get_block_package()` 或 `get_blocks()`；SRS 包两个都没有，所以连开发态 fallback 也无法发现其 blocks。

违反原因：

- T-SRS-013 明确是插件注册收尾任务；当前 `main` 上这一步并没有完成。
- 因为没有 `get_blocks()`，无论标准 entry-point scan 还是 monorepo fallback，都无法注册 SRS blocks。

影响：

- 安装 SRS 包并不会通过声明的插件机制把其 blocks 暴露出来。
- T-SRS-014 设计的 cross-plugin E2E 无法走正常 registry discovery 流程。

引入 PR 来源：

- PR `#309`（`6a068f85`）创建了没有 entry points 的 skeleton pyproject。
- PR `#367`（`2ccec1d8`）加入了 `SRSImage`。
- PR `#380`（`26aed247`）加入了 preprocess 导出，但仍未完成 T-SRS-013 所需的 packaging / registration。

是否已在 issue 中列出：

- 我找到了 SRS spec issue `#299`，它描述了预期行为。
- 但没有找到一个缺陷 issue 明确说明 `main` 仍未完成 T-SRS-013。
- 相关 skeleton issue `#308` 也只说明 skeleton 阶段 entry points 故意缺失，并不是当前缺陷的跟踪项。

建议：

- 在把 SRS 视为“已交付插件”之前，必须先完成 T-SRS-013：补 entry points、补 `get_blocks()`、补 entry-point tests，再接 T-SRS-014 集成测试。

### F4. `scieasy-blocks-lcms` 仍缺少 entry-point wiring、`get_blocks()`，且 T-LCMS-020/021 的收尾交付不存在

严重度：高
分类：Phase 11 未完成实现、打包缺陷

要求 / 设计行：

- `docs/specs/phase11-lcms-block-spec.md:806-810` 要求 LC-MS entry points：
  - `scieasy.blocks`: `lcms = "scieasy_blocks_lcms:get_blocks"`
  - `scieasy.types`: `lcms = "scieasy_blocks_lcms.types:get_types"`
- `docs/specs/phase11-lcms-block-spec.md:3326-3473` 定义 T-LCMS-020：补全 `get_blocks()`、校验 entry points、通过 8 个 smoke tests。
- `docs/specs/phase11-lcms-block-spec.md:3490-3536` 定义 T-LCMS-021：加入 isotope-tracing integration fixtures 和测试。
- `docs/specs/phase11-implementation-standards.md:3172-3173` 与 `docs/specs/phase11-lcms-block-spec.md:3544` 把 T-LCMS-021 设为最终依赖门槛。

实际实现行：

- `packages/scieasy-blocks-lcms/pyproject.toml:5-15` 没有任何 entry-point section。
- `packages/scieasy-blocks-lcms/src/scieasy_blocks_lcms/__init__.py:10-13` 明确写着 entry-point registration 还“交给 T-LCMS-021 impl agent”。
- `packages/scieasy-blocks-lcms/src/scieasy_blocks_lcms/__init__.py:24-30` 只导出了 types 和 `get_types`，没有 `get_blocks()`。
- 仓库文件清单中也没有 `packages/scieasy-blocks-lcms/tests/integration/`，而 T-LCMS-021 明确要求该目录下的 fixtures 和 `test_tracing_workflow.py`。

违反原因：

- spec 明确规定 T-LCMS-020 / T-LCMS-021 是 LC-MS plugin 的收尾 capstone。
- 当前 `main` 仍然是 deferred/skeleton 状态，而不是完成态的 packaging / discovery / integration test 状态。

影响：

- LC-MS 包不能通过 entry-point-based plugin loading 被发现。
- 承诺的 isotope-tracing 端到端验证不存在。
- 这个包在主分支上的状态更像 skeleton，而不是完成交付。

引入 PR 来源：

- PR `#309`（`6a068f85`）创建了最初 skeleton pyproject。
- PR `#348`（`0f9e6fdc`）在 LC-MS skeleton 中明确把 T-LCMS-020/021 标为 deferred。
- 之后没有 merged PR 在 `main` 上把这两项真正补完。

是否已在 issue 中列出：

- issue `#345` 明确写了 T-LCMS-020/021 被 deferred。
- 但我没有找到一个单独 issue 跟踪“这些 deferred 任务至今仍缺失在 main 上”。

建议：

- 在把 LC-MS 视为完成插件前，必须补完 T-LCMS-020 与 T-LCMS-021：加 `get_blocks()`、加 entry points、加 smoke tests、加 synthetic-fixture integration workflow。

### F5. Phase 11 的“全插件集成测试”方案在仓库根目录下无法执行

严重度：中
分类：测试架构、集成未完成

要求 / 设计行：

- `docs/specs/phase11-implementation-standards.md:3271-3279` 要求在 T-LCMS-021 之后，整个 monorepo 级别的 `pytest -x --no-cov` 必须通过。
- `docs/specs/phase11-lcms-block-spec.md:234-238` 与 `docs/specs/phase11-lcms-block-spec.md:283-287` 要求插件本地 pytest 作为 ticket acceptance 的一部分。
- `docs/specs/phase11-lcms-block-spec.md:3536` 要求 LC-MS integration test 能在 `pytest packages/scieasy-blocks-lcms/tests/integration/` 下通过。

实际实现行：

- `pyproject.toml:127-129` 把 root pytest 的 `testpaths` 限制为 `["tests"]`，这意味着默认 root pytest 根本不会跑 `packages/*/tests`。
- `packages/scieasy-blocks-imaging/tests/conftest.py:1-20`、`packages/scieasy-blocks-srs/tests/conftest.py:1-30`、`packages/scieasy-blocks-lcms/tests/conftest.py:1-29` 各自定义了插件本地 `tests.conftest` 模块。

实际观察到的失败：

- 从 repo root 运行
  `pytest --no-cov packages/scieasy-blocks-imaging/tests/test_packaging.py packages/scieasy-blocks-srs/tests/test_types.py packages/scieasy-blocks-lcms/tests/test_types.py -q`
  时，直接报：
  `ImportPathMismatchError: ('tests.conftest', ...imaging..., ...srs...)`

违反原因：

- root test 配置本身没有纳入插件包测试。
- 尝试从 root 手工拼接多个 plugin test 目录时，又会因为同名 `tests.conftest` 触发 Python 包冲突。
- 因此，standards 文档中描述的“full monorepo”测试策略，目前在主工作区并不可执行。

影响：

- CI / root 验证很容易漏掉 plugin regressions。
- 仓库没有一个清晰、权威的 full Phase 11 plugin test 入口。

引入 PR 来源：

- root pytest 范围来自 repo 级配置（`pyproject.toml`）。
- 造成冲突的 package-local test scaffold 来自 Phase 11 scaffold / plugin implementation PR，起点是 PR `#309`，随后被各 plugin PR 延续。

是否已在 issue 中列出：

- 没有找到与这个 repo-root 测试拓扑问题匹配的 GitHub issue。

建议：

- 必须明确一种受支持的策略并固化：
  - 要么把 package tests 纳入 root pytest，并确保 package 名称不冲突；
  - 要么明确规定 root suite 只测 core，插件测试必须隔离按 package 单独跑，并把这一点写入 CI 与文档。

### F6. `ARCHITECTURE.md` 承诺了一整套 `docs/block-development/` 文档，但仓库中并不存在

严重度：中
分类：文档完整性

要求 / 设计行：

- `docs/architecture/ARCHITECTURE.md:2682-2695` 明确承诺存在 `docs/block-development/` 文档集，包含 `quickstart.md`、`architecture-for-block-devs.md`、`block-contract.md`、`data-types.md`、`custom-types.md`、`memory-safety.md`、`collection-guide.md`、`testing.md`、`publishing.md` 和 `examples/`。

实际仓库状态：

- 仓库中存在 `docs/guides/block-sdk.md`，但并不存在 `docs/block-development/` 目录。

违反原因：

- 架构文档把读者指向了一组并不存在的文档树。
- 这是直接的文档完整性问题，也削弱了 Block SDK 的 onboarding 叙事。

影响：

- 新的 plugin 作者无法按架构文档的引用路径直接工作。
- 架构文档高估了开发者文档集的完备性。

引入 PR 来源：

- 该承诺出现在架构文档更新链路中；最近的相关合入是 PR `#330`（`81c821e`，T-TRK-010 架构文档更新）。

是否已在 issue 中列出：

- 没有找到专门跟踪 `docs/block-development/` 缺失的 issue。

建议：

- 要么补齐 `docs/block-development/` 目录和对应文档；
- 要么把 `ARCHITECTURE.md` 改成指向真实存在的 `docs/guides/block-sdk.md`。

## 验证说明

- 以下定向 core 测试在 `--no-cov` 下通过：
  - `tests/testing/test_harness.py`
  - `tests/api/test_blocks.py`
  - `tests/blocks/test_registry.py`
  - `tests/architecture`
- 这些测试同时也印证了 F1：Stage 10.1 对应测试仍然处于 skipped 状态。
- 不带 `--no-cov` 的子集测试会触发仓库级 `--cov-fail-under=85` 门槛，因此这里为了做问题定位，采用了 `--no-cov` 定向验证。

## 建议的后续动作

1. 尽快完成或回退 Stage 10.1 Part 2，让 API、前端、测试和文档重新一致。
2. 让 `BlockTestHarness` 对齐 ADR-026 / issue `#215`，或者立即回调文档描述。
3. 在把 SRS / LC-MS 视为“已交付插件”之前，先补完它们各自的 packaging / entry-point / integration capstone。
4. 统一 full-repo plugin test 策略，并接入 CI。
5. 删除或修正文档中所有与实际文件树不一致的承诺。
