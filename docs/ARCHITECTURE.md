# 架构

SkyForge 的部署分四层，从轻到重：核心引擎（不带 LLM、不带 Web）、LLM 抽象层、CLI、Web 工作室。哪层不要就剥哪层，比如只想要命令行可以不带 Studio 跑。

引擎内部又是六层（L0-L5），自底向上是协议、LLM 客户端、仿真验证、验证链、Agent 策略、编排。

## 部署的四层

```
Layer 3  Web 工作室      FastAPI + Vue 3 + WebSocket
Layer 2  CLI             skyforge-core
Layer 1  LLM 抽象层       skyforge-llm
Layer 0  核心引擎         skyforge-engine（零 LLM、零 Web）
```

## 引擎六层

| 层 | 名字 | 干什么 | 关键目录 |
|----|------|--------|----------|
| L0 | 基础设施协议 | 抽象基类、数据 schema、模式守卫、执行契约 | core/protocols.py |
| L1 | LLM 客户端 | 多模型统一接口、路由、Mock 降级 | core/strategies/ |
| L2 | 仿真验证 SIL/PIL/HIL | 纯软件仿真、QEMU 处理器仿真、真实硬件在环 | digital_twin/、core/adapters/ |
| L3 | 验证工具链 | Z3/CBMC/Cppcheck/GCC 可插拔 | core/verifiers/、tools/ |
| L4 | Agent 策略 | 多个 Agent 从需求一路做到代码 | agents/ |
| L5 | 编排 | PipelineOrchestrator 串起来，11 个 Stage 类（装 10 个实例） | core/orchestrator.py、core/stages/ |

## 核心引擎（skyforge_engine）

这层不依赖 LLM 和 Web 框架，能单独跑。目录大概长这样：

```
skyforge_engine/
├── core/                  编排
│   ├── orchestrator.py    PipelineOrchestrator
│   ├── stages/            各阶段：需求解析/LLR/架构/契约/代码/cppcheck/修复/形式化/仿真/HIL检查点/报告
│   ├── verifiers/         z3/cbmc/cppcheck/contract + chain
│   ├── strategies/       LLM/Mock 策略
│   ├── standards/         编码标准
│   ├── adapters/          HIL 适配
│   └── renderers/         HTML/Markdown/PDF
├── agents/                需求解析、LLR、架构、契约、代码生成（含多语言）、修复、misra_fixes、python_fixes
├── digital_twin/          虚拟传感器、虚拟 MCU、故障注入、hil/qemu/serial/arinc653 适配器、仿真引擎
├── composable/            compatibility_checker / component_combinator / composition_simulator
├── tools/                 cppcheck_scanner、z3/cbmc_verifier、contract_checker、tool_chain_validator
├── report/                do178_objectives、coverage_analyzer、traceability_matrix、psac_generator、evidence_collector
├── rag/                   misra_searcher、rag_enhancer、rule_parser、semantic_search
├── coding_standards/      misra_c / misra_cpp / python_safety（插件注册）
├── streaming/             task_stream_registry
├── dal/                   gcov_collector、mcdc_calculator
└── scade/                 G-Lustre 解析器
```

### 编码标准怎么插拔

DO-178C 那套过程标准是固定的，编码规范走注册机制，加新规范不用动主流程：

```python
from skyforge_engine.coding_standards import get_registry

registry = get_registry()
for std in registry.list_all():
    print(std.id, std.name, std.language)

cpp_standards = registry.get_by_language("cpp")
```

现在注册了三个：`misra_c_2012`（MISRA-C:2012，红线规则加一批修复器）、`jsf_av_cpp`（JSF AV C++）、`python_safety`（Python 安全子集）。各有多少条规则、多少个 fixer，看 `coding_standards/` 下各文件的表，别信这里手数的数。

### 流水线

PipelineOrchestrator 把这些 Stage 串起来：需求解析 → LLR → 架构 → 契约 → 代码 → cppcheck → 修复循环 → 形式化验证 → 仿真 → HIL 检查点 → 报告。中间产物在 Stage 之间传递，失败策略和并行组在 orchestrator 里配。

## LLM 抽象层（skyforge_llm）

```
skyforge_llm/
├── providers/   openai / anthropic / openai_responses
├── security/    sanitizer（输入清洗）、auditor（审计）、validator
├── client.py    统一客户端
├── router.py    多供应商路由
└── cache.py     响应缓存
```

## CLI（skyforge_core）

```bash
skyforge generate   # 代码生成
skyforge check      # 合规检查
skyforge simulate   # 数字孪生仿真
skyforge report     # 生成报告
```

## Web 工作室

后端在 `studio/app`，FastAPI。V1 任务协议是唯一入口，用 idempotency_key 防重复提交，事件走 WebSocket 续传：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/tasks` | 唯一创建入口，带 idempotency_key |
| GET | `/api/v1/tasks/{task_id}` | 读状态、产物、provenance |
| GET | `/api/v1/tasks` | 运行记录列表 |
| WS | `/api/v1/tasks/{task_id}/events?after_seq=N` | 事件订阅，支持断线续传 |
| GET | `/api/v1/execution-profiles` | Profile 列表 |
| GET | `/api/v1/preflight/{profile}` | 可用性预检 |
| GET | `/api/v1/recordings` | 离线运行包 |
| GET | `/api/v1/recordings/{id}` | 读离线运行包 |

前端 Vue 3，页面在 `studio/frontend/src/views` 和 `pages/` 下，路由大概十个：首页、架构、生成、记录、记录详情、能力实验室、设置、组件组合、MISRA 搜索、HITL。组件用 shadcn-vue，状态走 Pinia。

## 数据流

代码生成这条线：用户输入 → 需求解析（出 JSON）→ 契约（YAML）→ 代码生成（C/C++/Python）→ 合规检查 → 报告（HTML/PDF）。

HITL 那条线：Agent 决策 → 风险评估 → 高风险就停住等人审批 → 批了再往下走。

## 技术栈

后端 Python 3.12+、FastAPI、Pydantic、Ruff、Loguru；测试用 pytest。前端 Vue 3、TypeScript、Vite、Pinia、Tailwind、shadcn-vue、Vitest、Biome。基础设施 Docker、Redis、GitHub Actions。

## 执行 Profile

| Profile | 类型 | 说明 |
|---------|------|------|
| mock | simulated | 浏览器/后端纯模拟，完全离线 |
| cloud | live | 云模型，服务端真跑 |
| local | live / replay | 本地模型（Ollama/LM Studio），支持已验证回放 |

术语上 HITL 是人工审查（Human-in-the-Loop），HIL 专指硬件在环，别混。证据状态四种：observed / simulated / unavailable / failed。

## 性能上做过的几处

独立的 Agent 任务并行跑；LLM 响应和中间结果有缓存；非核心模块懒加载。前端那几个长轮询组件（顶部状态栏、Dashboard 状态、HITL 倒计时）用 `visibilitychange`，页面切后台就停，切回来立刻刷。generate / repair / generateReport 统一 180s 超时，本地模型推理慢也能扛。Windows 上 cppcheck 的 MISRA addon 用 `sys.executable` 调 venv 里的 Python，绕开 Microsoft Store 的 python stub。

## 怎么扩展

加自己的编码标准：

```python
from skyforge_engine.coding_standards.base import CodingStandard, get_registry

my_std = CodingStandard(
    id="my_custom_standard",
    name="My Custom Standard",
    language="c",
    version="1.0",
    red_line_rules=["R1", "R2"],
    fixers={"R1": my_fixer_func},
)
get_registry().register(my_std)
```

自定义 Agent 和工具分别继承 `agents/agent.py` 的 `BaseAgent` 和 `tools/base_scanner.py` 的基类，实现 `execute` / `run` 就行。

## 安全

用户输入走 Pydantic 校验，LLM 输出经过 sanitizer 清洗再用，API key 存配置不进日志，操作有审计。这块具体看 `skyforge_llm/security/`。

---

v1.0.0，2026-07-21。
