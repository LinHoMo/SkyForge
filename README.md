# SkyForge (天锻)

面向 DO-178C 的机载软件工具链。把需求解析、LLR、代码生成、MISRA 修复、形式化验证、仿真和报告串成一条流水线，中间产物之间留追溯。先说清楚：工具本身没过适航鉴定，出来的是工程辅助证据，不能直接当审定材料用。

支持 C / C++ / Python，编码规范走 MISRA-C、MISRA C++、JSF AV C++，外加一套 Python 安全子集。

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Vue 3](https://img.shields.io/badge/Vue-3-42B883.svg?logo=vue.js&logoColor=white)](https://vuejs.org/)

## 现在的状态

后端 pytest 281 个用例通过（5 个 warning），全仓 pytest 加 vitest 大约八百多项。主源码 9 万多行（src + studio/app + 前端 src，不含 node_modules 和 .venv）。MISRA 自动修复规则 130 条左右，配置表驱动那套重构方案还躺在 `docs/REFACTORING_MISRA_FIXES.md` 里，没动手。

DAL-A 这边几个目标只是部分满足：OBJ-2 契约验证、OBJ-10 独立性、OBJ-17 独立验证都缺真实人工审查和硬件平台，OBJ-12 跟着 OBJ-2 走；OBJ-20 数据耦合、OBJ-21 控制耦合各有一两个全局变量的警告。OBJ-13/14/15 这三项（语句、判定、MC/DC 覆盖率）目前是静态估算，没接上真 GCC + gcov/lcov 之前不算实测，别拿这个数字去充数。

## 架构

引擎分六层，自底向上：

- **L0 协议层**：抽象基类、数据 schema、模式守卫，Provider 靠依赖注进去
- **L1 LLM 客户端**：云 API / 本地 / 离线三档，多供应商路由、响应缓存、输入输出清洗和审计
- **L2 仿真验证**：SIL 用虚拟传感器、虚拟 MCU 和故障注入；PIL 走 QEMU（STM32F103 / F407）；HIL 支持串口 UART、JTAG-SWD 和 ARINC 653 分区调度
- **L3 验证链**：Z3 / CBMC / Cppcheck / GCC 可插拔，VerifierChain 负责编排和结果聚合
- **L4 Agent 策略层**：需求解析、LLR 生成、架构设计、契约生成、代码生成、代码修复，外加 MISRA 适配和 Python 适配
- **L5 编排层**：PipelineOrchestrator 调度，11 个 Stage 类（装配 10 个实例，含 3 个人工审查检查点），支持串行、并行组和失败重试

细节看 [ARCHITECTURE.md](./docs/ARCHITECTURE.md)，怎么扩插件看 [PLUGIN_DEVELOPMENT.md](./docs/PLUGIN_DEVELOPMENT.md)。

## 跑起来

```bash
sh start.sh
```

手动装：

```bash
cd SkyForge
uv sync                 # 也可以 pip install -e ".[dev]"
make dev                # FastAPI 在 8000，Vite 在 5173
```

起来之后前端 http://localhost:5173 ，Swagger http://localhost:8000/docs 。

macOS 先 `brew install uv node@18`，Cppcheck 和 CBMC 也是 brew 装。缺工具不会报错，自动退到 mock 模式。

Docker：

```bash
docker compose up --build
# 开发模式热重载
docker compose -f docker-compose.dev.yml up
```

### 工具链（可选）

离线模式什么外部工具都不用装，要做真验证才需要这几个。`start.sh` 启动时会自己检测，缺了就打安装提示，新用户首次启动会自动 `pip install z3-solver`。

| 工具 | 干什么 | Linux / macOS | Windows |
|------|--------|---------------|---------|
| z3-solver | 契约 SMT | pip install（自动） | 同左 |
| cbmc | C 有界模型检查 | apt / brew install cbmc | 双击 `tools/cbmc-6.9.0-win64.msi` |
| cppcheck | MISRA-C 静态扫描 | apt install cppcheck | choco install cppcheck |
| gcc | 编译、覆盖率插桩 | 系统自带 | MinGW / MSYS2 |

Windows 上 cbmc 默认装到 `C:\Program Files\cbmc\bin\`，检测会额外看这个路径。cppcheck 的 MISRA addon 用 venv 里的 `sys.executable` 跑，不靠 `which python`。

### 离线模式

没接外部依赖时的行为：LLM 走关键词匹配加模板拼接（`src/skyforge_llm/local.py`）；GCC 不可用就标 `simulated` 或 `unavailable`，不记编译通过；Cppcheck 没有扫描器就标 `unavailable`；Z3 / CBMC 直接跳过；Redis 没装就退回内存队列。日志里带 `[Mock]` 的就是这一步没用真工具。

报告和界面上每个结果都会标数据来源：`observed`（真工具跑的）、`simulated`（离线模拟的）、`unavailable`（工具缺了跳过）、`failed`（验证没过）。

### HITL 人工审查

HITL（Human-in-the-Loop）在需求、契约、代码这几个检查点停住等人拍板。默认关，免得卡自动化流程；`HIL_ENABLED=true` 或者调 `POST /api/hil/toggle` 打开，运行时切不用重启。页面上 Generate 那栏也有个开关。注意 HIL 三个字这里只指硬件在环，跟 HITL 是两码事，旧的 `/api/hil/*` 路径留了一版兼容。

## 目录

```
src/
  skyforge_engine/        核心引擎，L0-L5 都在这
    agents/               代码生成、修复、契约、MISRA 这些 Agent
    core/stages/          流水线各 Stage
    tools/                cppcheck / z3 / cbmc / contract 扫描器
    digital_twin/         虚拟 MCU、虚拟传感器、故障注入、仿真引擎
    report/               DO-178C 报告和合规目标
    rag/                  MISRA 规则语义检索
    composable/           组件组合验证
    scade/                SCADE G-Lustre 解析器（递归下降，没用 ANTLR 运行时）
  skyforge_llm/           LLM 客户端、路由、缓存、安全清洗
  skyforge_core/          CLI 入口
studio/
  app/                    FastAPI 后端
  frontend/               Vue 3 前端
docs/                     文档，compliance/ 下是 8 份 DO-178C 草案
examples/                 示例工程
```

前端主要页面：

| 路径 | 页面 |
|------|------|
| `/` | 首页 |
| `/architecture` | 六层架构 |
| `/generate` | 代码生成 |
| `/records` | 运行记录 |
| `/records/:taskId` | 记录详情 |
| `/lab` | 能力实验室 |
| `/settings` | 系统设置 |
| `/compose` | 组件组合验证 |
| `/misra` | MISRA 规则搜索 |
| `/hitl` | 人工审查 |

三种执行 Profile：`mock` 纯离线模拟；`cloud` 接云模型真跑；`local` 本地模型，支持已验证回放。

## API

完整接口在 Swagger，这里列主要几块：

| 模块 | 路由文件 | 代表接口 |
|------|----------|----------|
| 健康检查 | routes/common.py | `GET /api/health` |
| V1 任务 | routes/tasks_v1.py | `POST /api/v1/tasks`，`WS /api/v1/tasks/{id}/events` |
| 生成/修复/仿真 | routes/pipeline.py | `POST /api/generate`，`/api/repair`，`/api/simulate` |
| 报告 | routes/reports.py | `POST /api/report` |
| 组件组合 | routes/composition.py | `POST /api/compose` |
| HITL | routes/hitl.py | `GET /api/hil/pending` |
| 模型 / MISRA 检索 | routes/models.py | `GET /api/models`，`/api/misra/rules` |

## DO-178C

合规草案在 `docs/compliance/`，一共 8 份：PSAC、SDP、SVP、SCMP、SQAP、TQP、TOR、TAS。DO-178C 那 21 个可判定目标（OBJ-1~21，OBJ-20/21 是数据耦合和控制耦合）的实现在 `src/skyforge_engine/report/do178_objectives.py`。

计划、开发、验证、配置管理、质量保证这五大过程都有对应文档兜底，但都是工程草案，真上项目还得过人工审查。DAL-A 的 MC/DC 覆盖率必须靠真 GCC + gcov/lcov 才有数，模拟和静态估算不算。工具鉴定那块，Agent Pipeline 和 LLM 引擎定 TQL-1，Contract Checker 定 TQL-2，Cppcheck / GCC 直接引用现成工业工具。

```bash
make do178c-check
```

## 文档

- [USER_GUIDE.md](./docs/USER_GUIDE.md) — 部署和功能说明
- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) — 架构细节
- [ROADMAP.md](./docs/ROADMAP.md) — 后续计划
- [PLUGIN_DEVELOPMENT.md](./docs/PLUGIN_DEVELOPMENT.md) — 二次开发、编码标准插件
- [MULTI_LANGUAGE_GUIDE.md](./docs/MULTI_LANGUAGE_GUIDE.md) — C/C++/Python 多语言
- [COMPLIANCE_MATRIX.csv](./docs/COMPLIANCE_MATRIX.csv) — 合规矩阵

## 第三方

后端 FastAPI、Pydantic、Redis、Z3、httpx、loguru、click、numpy、uvicorn、websockets；前端 Vue 3、Vite、Pinia、Vue Router、shadcn-vue、Tailwind、Biome；外部可选 Cppcheck、GCC、CBMC、LM Studio。带许可证的完整清单见 [ThirdParty.md](./ThirdParty.md)。

## License

MIT，Copyright (c) 2026 SkyForge Contributors。仓库：github.com/linskadi/SkyForge。
