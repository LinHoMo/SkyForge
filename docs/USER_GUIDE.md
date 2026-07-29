# 用户指南

## 跑起来

环境要求：

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.12+ | 后端 |
| Node.js | 18+ | 前端 |
| pnpm | 10+ | 前端包管理 |
| uv | 最新 | 后端包管理 |
| Redis | 6+ | 可选，任务队列 |
| LM Studio / Ollama | 最新 | 可选，本地 LLM |

最简单的方式：

```bash
git clone https://atomgit.com/gcw_TTqe9ALQ/SkyForge.git
cd SkyForge
sh start.sh
```

脚本会装依赖、拉 z3-solver、配默认环境变量，然后把前后端都起起来。想手动来：

```bash
uv sync
make dev

cd studio/frontend
pnpm install
pnpm dev
```

Docker：`docker compose up --build`。

起来之后前端 http://localhost:5173 ，后端 http://localhost:8000 ，Swagger 在 http://localhost:8000/docs 。

前端主要页面：

| 路径 | 页面 |
|------|------|
| `/` | 首页，三栏：任务输入 / 流水线 / 实时结论 |
| `/architecture` | 六层架构展示 |
| `/generate` | 代码生成 |
| `/records`、`/records/:taskId` | 运行记录、单任务回放 |
| `/lab` | 能力实验室（组件组合 / MISRA 搜索 / HITL 入口） |
| `/settings` | 执行 Profile 和 LLM 配置 |
| `/compose` | 组件组合验证 |
| `/misra` | MISRA-C 规则查询 |
| `/hitl` | 人工审查工作台 |

顶部导航就这六个：首页、六层架构、代码生成、运行记录、能力实验室、系统设置。

## 三种执行 Profile

在「系统设置」里切：

- **mock**：完全离线，浏览器和后端都走内置 Mock 数据，零配置，开箱即用。
- **cloud**：接云 LLM，服务端真跑完整流水线，得配 API 地址和 key。
- **local**：接本地 Ollama / LM Studio，数据不出内网，已经验证过的任务可以回放。

## 功能怎么用

### 首页和代码生成

首页是三栏布局，左边输需求或挑预设任务，中间实时跑流水线（需求解析 → 契约 → 代码 → 修复 → 仿真 → 报告），右边出合规结论和风险等级。

「代码生成」页从自然语言一路出 C 代码。举个例子，需求里写"实现一个飞行器高度传感器滤波模块，输入原始高度数据，输出卡尔曼滤波后的平滑值，符合 MISRA-C"，点开始生成就行。生成过程中页面下方会推四个 Agent 的实时输出：REQ-Parser 解析需求、CON-Gen 出契约、CODE-Gen 出代码、REPAIR 修 MISRA 违规。

HITL 开关在「开始生成」左边，灰色是关，琥珀色是开，mock 模式下藏起来。打开之后流水线在需求、契约、代码三个检查点停下来等人批。注意 HITL 是人工审查，HIL 是硬件在环，不是一回事。

出来的东西：结构化需求 JSON、DO-178C 契约 YAML、带追溯注释的 C 代码、cppcheck 扫描和修复记录。

### SCADE 导入

准备 `.lus` 的 G-Lustre 文件，在代码生成页点「上传 SCADE」，解析器在 `src/skyforge_engine/scade/lustre_parser.py`，转成需求 JSON 和契约 YAML，可以跟手写需求合并。示例看 `studio/app/tests/data/example.lus`。

### 组件组合验证

「组件组合」页（`/compose`）传两个组件，选连接方式（顺序组合就是 A 的输出喂给 B），点验证兼容性，检查信号量程、类型、采样率对不对。想偷懒可以用模板库，模板按 filter / controller / sampler / limiter 分类，挑一个自动填契约和代码，再改。

### 数字孪生仿真

代码生成完进「仿真」标签，默认会先无故障跑一遍（200 步）。可以选故障类型注入：传感器漂移、信号噪声、数据丢包、硬件故障、时序异常，跑出来对比正常和故障波形。仿真会实时校验契约的前置/后置条件和不变式，违反了就判失败。

### HITL 人工审查

默认关（`HITL_ENABLED=false`），免得卡自动化。开的方式两种：页面上那个开关，或者 `POST /api/hitl/toggle`，运行时切不用重启。每个检查点等 5 分钟，超时自动批。批了往下走，拒了整个流水线 `aborted=true`。

### 运行记录和回放

`/records` 列表按时间倒序，在跑的实时显示进度，跑完且验证过的能一键回放。点进去逐步看每个 Stage 的输入输出和证据，能下载产物包。回放数据带完整执行轨迹，用来审计、培训、查问题都行。

### 系统设置和报告

「设置」里选 Profile、填 LLM 的 base URL、模型名、key、max tokens。代码生成完点「生成报告」出 HTML，浏览器能直接打印成 PDF，里面有项目概览、需求-代码追溯矩阵、MISRA 合规统计、仿真和契约覆盖率、DO-178C 目标逐项评估。

## 端到端走一遍

用 `examples/filter_requirements.txt` 那个一阶低通滤波器当例子。

先 `bash start.sh`，等后端日志出现 LLM 预热完成（本地模型没起来就按 mock 跑，照样能走完）。浏览器开 http://localhost:5173 ，把需求文本粘到「需求描述」框，点「一键全流程」。

页面下方四个 Agent 依次推：

REQ-Parser 把自然语言抠成结构化 JSON，大概长这样：

```json
{
  "req_id": "REQ-001",
  "desc": "实现一个一阶低通滤波器...",
  "type": "filter",
  "module_name": "lowpass_filter",
  "safety_level": "DAL-A",
  "params": {"cutoff_hz": 1.6, "sample_rate_hz": 16.0, "alpha": 0.1},
  "constraints": ["WCET <= 1ms", "禁止动态内存（MISRA Rule-21.3）"]
}
```

`req_id` 是流水线内自增的追溯号；`type` 只能是 filter / control / comms；`safety_level` 按危害等级推断成 DAL-A 到 DAL-E。

CON-Gen 接着出契约 YAML：

```yaml
component: lowpass_filter
version: 1.0.0
safety_level: DAL-A
traceability: [REQ-001]
interface:
  inputs:
    - {name: raw_input, type: double, range: [-1000.0, 1000.0]}
  outputs:
    - {name: filtered_output, type: double, range: [-1000.0, 1000.0]}
contracts:
  preconditions:
    - "raw_input != NULL"
  postconditions:
    - "filtered_output >= -1000.0 && filtered_output <= 1000.0"
  invariants:
    - "sample_rate == 16Hz"
  fault_handling:
    - "if raw_input == 0: set fault_detected = true"
```

前置条件调用前必须成立，后置条件调用后必须成立，不变式运行期间恒成立，fault_handling 那段机载软件不能省。

CODE-Gen 出 MISRA-C 风格代码，每个函数和变量都带追溯注释：

```c
/* [REQ-001] [MISRA-Rule-8.13] 机载信号滤波器实现
 * Traceability: REQ-001
 */
#include "lowpass_filter.h"

static double s_prev_output = 0.0;
static int    s_initialized = 0;

double lowpass_filter_apply(double raw_input)
{
    double filtered_output;
    if (0 == s_initialized) {
        lowpass_filter_init();
    }
    filtered_output = 0.100000 * raw_input + (1.0 - 0.100000) * s_prev_output;
    s_prev_output = filtered_output;
    return filtered_output;
}
```

`[REQ-001]` 是正向追溯，`[MISRA-Rule-x.x]` 标用了哪条规则，方便审查。

REPAIR 那步循环最多三轮：cppcheck 扫出违规 → 没有就跳出 → 修 → contract_checker 验契约还在不在 → 再扫。每轮的违规数变化在「修复历史」里看时间线。

之后切到「数字孪生」跑仿真，再到「故障注入」面板选 `sensor_drift`、漂移 10%，正常曲线和故障曲线叠在一张图上对比。输出超量程的话仿真判失败。

最后「DO-178C 报告」Tab 下载 HTML。想测组件组合就去 `/compose`，左栏 LowPassFilter、右栏 HighPassFilter，顺序组合，验证兼容性再跑组合仿真。

## 产物字段

需求 JSON、契约 YAML、生成的 C 代码、HTML 报告、仿真波形，这几样的字段和上面 walkthrough 里看到的一致。补几个容易忽略的：

- 代码里的追溯 tag 有四种：`[REQ-xxx]`、`[CON-xxx]`、`[MISRA-Rule x.x]`、`[TST-xxx]`，缺了 CODE-Gen 会自动补。
- 生成代码的函数命名：初始化 `<module>_init(void)`，滤波类是 `<module>_apply(double)`，控制类是 `<module>_compute(setpoint, feedback)`。
- 强制遵守的 MISRA 规则：内部状态用 static（8.9）、只读指针加 const（8.13）、首次调用前 init（10.1）、浮点显式类型（10.4）、if/else 全加花括号（15.7）、检查返回值（17.7）、禁 malloc/free（21.3）。
- 报告里 tag 着色：REQ 蓝、CON 绿、TST 紫、MISRA 橙。
- 仿真波形横轴是步数，纵轴是信号值，故障注入时刻打一条竖线。

## LLM 和环境变量

本地跑 LM Studio 的话，装完模型（推荐 Qwen2.5-Coder-7B 或更高），起服务（默认 1234），配：

```env
USE_LLM=true
LMSTUDIO_BASE_URL=http://localhost:1234/v1
```

不配就走 Mock，自动生成格式正确的模板代码，演示和测试够用。

所有变量在 `src/skyforge_engine/config.py` 里，pydantic-settings 从环境变量和 `.env` 读。根目录放 `.env`，或者 `config/.env.dev` / `.env.prod`，进程环境变量优先级最高。

常用变量：

| 变量 | 默认 | 说明 |
|------|------|------|
| `USE_LLM` | false | 开真 LLM，否则 Mock |
| `LMSTUDIO_BASE_URL` | http://localhost:1234/v1 | 本地服务地址 |
| `LLM_MODEL` | LM Studio 默认 | 模型名 |
| `LLM_API_KEY` | 空 | 本地可留空 |
| `LLM_MAX_TOKENS` | 8192 | 单次最大 token |
| `LLM_CACHE_ENABLED` | true | 相同 prompt 的非流式调用做缓存 |
| `LLM_CACHE_TTL` | 3600 | 缓存秒数 |
| `HIL_ENABLED` | false | HITL 开关（历史兼容名，实际指人工审查） |
| `HIL_TIMEOUT` | 300 | 审批超时秒数，超时算拒绝 |
| `USE_REAL_CPPCHECK` | false | true 调真 cppcheck，否则模式匹配 Mock |
| `USE_REAL_GCC` | false | true 数字孪生真编译，否则虚拟 MCU 解释执行 |
| `REDIS_URL` | redis://localhost:6379/0 | 可选 |
| `LOG_LEVEL` | INFO | DEBUG/INFO/WARNING/ERROR |
| `MAX_RETRIES` | 3 | LLM 调用重试 |
| `CORS_ALLOW_ORIGINS` | * | 逗号分隔或 JSON 数组也行 |

每个 Agent 还能单独配，比如 `REQ_PARSER_BASE_URL`、`CON_GEN_MODEL`、`CODE_GEN_API_TYPE`、`REPAIR_MAX_TOKENS`，不设就回退全局。`API_TYPE` 支持 `openai-chat` / `openai-responses` / `anthropic`。

## 部署

一键、手动、Docker 三种：

| 方式 | 场景 | 命令 |
|------|------|------|
| 一键 | 体验、开发 | `sh start.sh` |
| 手动 | 定制 | `uv sync` + `make dev` |
| Docker | 生产 | `docker compose up --build` |

手动起后端：`cp config/.env.example config/.env`，改完 `make dev`。前端 `cd studio/frontend && pnpm install && pnpm dev`。Redis 可选，`docker run -d -p 6379:6379 redis:6-alpine` 或 apt 装。

形式化验证工具链（离线模式不用装）：

| 工具 | 干什么 | Linux/macOS | Windows |
|------|--------|-------------|---------|
| z3-solver | 契约 SMT | pip（start.sh 自动） | 同左 |
| cbmc | C 有界模型检查 | apt/brew install cbmc | `tools/cbmc-6.9.0-win64.msi` |
| cppcheck | MISRA-C 扫描 | apt install cppcheck | choco install cppcheck |
| gcc | 编译、覆盖率 | 系统自带 | MinGW / MSYS2 |

Windows 上注意：cbmc 装在 `C:\Program Files\cbmc\bin\`，后端会自动找；cppcheck 的 MISRA addon 用 `sys.executable` 调 venv 里的 Python，绕开 Microsoft Store 那个 stub（exitcode 9009）。

Docker 生产：`docker compose up -d --build`，日志 `docker compose logs -f`。开发模式带热重载：`docker compose -f docker-compose.dev.yml up -d --build`。三个容器：redis(6379)、backend(8000)、frontend(80/443)。

前端生产用 Nginx，配置在 `frontend/nginx.conf`，`/api` 反代到 backend:8000，`/ws` 要带 Upgrade 头。HTTPS 就加个 443 ssl server 块。

## API

V1 任务协议是唯一入口：

```
POST /api/v1/tasks
```

请求体：

```json
{
  "type": "generate",
  "requirement": "实现一个高度传感器滤波模块...",
  "profile": "local",
  "options": {"simulate": true, "hitl_enabled": false}
}
```

返回 `task_id`，然后 WebSocket 连 `/api/v1/tasks/{task_id}/events`，推 stage_change、artifact_ready、log、progress、completed 这些事件。事件里带 `evidence` 字段，值是 observed / simulated / unavailable / failed 之一。

HITL 那组：`GET /api/hitl/pending`、`POST /api/hitl/approve`、`POST /api/hitl/reject`、`GET /api/hitl/history`、`POST /api/hitl/toggle`。健康检查 `GET /api/health` 返回 `{"status":"healthy"}`。

## 常见问题

**端口被占。** Windows：`netstat -ano | findstr :8000` 然后 taskkill。Linux/Mac：`lsof -i :8000` 再 kill。

**LLM 连不上。** 先确认 LM Studio 起了、1234 端口通不通，浏览器开 http://localhost:1234/v1/models 应该回 JSON。不行就切 mock，不影响走完流程。

**代码生成报错。** 看后端 `logs/`，先试 mock 模式定位。

**想关缓存。** `LLM_CACHE_ENABLED=false`，开发调试时默认开着能省时间。

**并行化会不会影响结果？** 不会。HITL 开着的时候，需求评审等待和契约生成是并行的，但契约只依赖 req_json；HITL 拒了就把并行产物丢掉，批了就用，跟串行结果一样。HITL 关着的时候直接串行，没区别。

**SCADE 支持哪些版本？** 支持 SCADE Suite 导出的 G-Lustre（`.lus`），标准 Lustre 语法子集：node 定义、let...tel、equations，inputs/outputs/locals 都认。

**真实 cppcheck / gcc 怎么开？** `USE_REAL_CPPCHECK=true` 调真 cppcheck（推荐 2.x），挂了自动降级 Mock；`USE_REAL_GCC=true` 让虚拟 MCU 真编译，编译失败也降级。

## 测试和证据

提交前跑一遍：

```bash
uv run pytest studio/app/tests src/skyforge_engine/tests src/skyforge_llm/security/tests -q
cd studio/frontend && pnpm test && pnpm build
```

有个原则别破：外部工具缺了就标 `unavailable` 或 `simulated`，不能拿空数组假装零违规；GCC 要记命令、版本、退出码、stderr；Z3/CBMC 按真实结果记，别硬编码通过。演示模式出的报告就叫模拟报告，别当适航证据。工具鉴定那套见 [TQP](./compliance/TQP.md)、[TOR](./compliance/TOR.md)、[TAS](./compliance/TAS.md)，合规草案 8 份都在 `docs/compliance/`。

还是那句话：SkyForge 给的是 DO-178C 工程辅助证据，工具本身没过适航鉴定。
