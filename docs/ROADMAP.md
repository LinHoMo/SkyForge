# 路线图

## v1.0.0（当前）

2026-07-21 发版，文档后来 8 月又补过几轮。这版主要把引擎重排成 L0-L5 六层：协议、LLM 客户端、仿真验证（SIL/PIL/HIL）、验证链、Agent 策略、编排。PipelineOrchestrator 现在管 11 个 Stage 类（装了 10 个实例），支持串行、并行组和失败重试。

其他落地的东西：V1 唯一任务协议（idempotency_key + 事件续传 + provenance），三种 Profile（mock/cloud/local），验证工具链 Z3/CBMC/Cppcheck/GCC 可插拔，组件组合验证，MISRA 规则的语义搜索加 RAG，DO-178C 报告和追溯矩阵，MC/DC 覆盖分析（gcov_collector + mcdc_calculator，GCC 14.2+ lcov 真收集，缺了回退静态分析），SCADE G-Lustre 解析器，可插拔编码标准（MISRA-C / MISRA C++ / Python），数字孪生和 HITL。

测试这块，全仓 pytest 645 个过、2 个 skip（单看引擎层 281 个），前端 vitest 180 个。

## 历史版本

### v0.4.1（2026-07-18）

补工具链：z3-solver 改成 pip 自动装，cbmc 给了 Windows 安装包（`tools/cbmc-6.9.0-win64.msi`）。HITL 默认关掉，加了运行时 toggle（`POST /api/hil/toggle`）和 UI 开关，免得卡自动化。Dashboard 重排成四块（后端/LLM/工具链/持久化），实时探 gcc/z3/cbmc。

修了几个实际问题：长轮询组件在页面后台时用 visibilitychange 停掉；generate/repair/generateReport 统一 180s 超时，照顾本地模型推理慢；Windows 上 cppcheck 的 MISRA addon 改用 `sys.executable`，绕开 Microsoft Store 那个 python stub；前端 vue-tsc 错误清了 27 个，biome warning 清零；本地 LLM provider 按 Base URL 端口自动认 ollama(11434)/lmstudio(1234)。

### v1.0.0（2026-07-17）

第一版能跑的东西：四层可剥离架构，多 Agent 协同，DO-178C 合规检查引擎，MISRA-C 自动修复，数字孪生，HITL，SCADE 集成，Web 工作室界面，可插拔编码标准。

## v1.1.0（规划）

还没排期，想做的：更多故障注入模型、本地模型调优、GCC 交叉编译、自动生成 DO-178C 风格测试用例、工具鉴定流程、多模型并行推理。优先级上工具鉴定和自动化测试生成最靠前，多模型和交叉编译看情况。

最后更新：2026-08-06
