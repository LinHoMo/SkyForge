# SkyForge 功能缺口与技术债 Backlog

> 来源：对标 SonarQube / Microsoft DevUI / maishac / Monaco Diff Editor / Frama-C 后的差距分析。
> 范围：studio 前端 + 后端 pipeline。工作量为前端/后端合计的粗估，单人全职。
> 分级：P0 = 现在就能做且价值大；P1 = 值得做但工作量大；P2 = 锦上添花。

## P0

| 功能名 | 为什么需要 | 参考项目 | 工作量 |
| --- | --- | --- | --- |
| ✅ MISRA 违规 inline diff 视图 | 现在 RepairTimeline 只给 before/after 整段代码，工程师无法一眼定位"这一行到底改了啥"。已有 MonacoDiffEditor 组件但修复循环里没用上，浪费现成资产。 | Monaco Diff Editor（并排 original/modified、只读 review 模式） | 1.5 天 |
| ✅ 合规报告导出 PDF/HTML 完整版 | 现在只有 CSV 导出和 ReportDownload 的 HTML 预览，没有带封面/签字页/追溯矩阵的可交付件。DO-178C 交付物必须能归档。 | SonarQube PDF report / Parasoft 报告包 | 2 天 |
| ✅ 需求-代码-测试追溯链可视化 | 现在追溯是 tag 高亮 + 追溯矩阵文本，看不到"一个 REQ 串起哪些 CON/TST/code 行"的图。审查者要的是一张图。 | Visure / Parasoft traceability graph | 3 天 |
| ✅ Pipeline 阶段后端 stage 字段落地 | 前端进度条目前靠 agent 名/日志关键字猜阶段，mock 模式下 ARCH/SIM/VERIFY/REPORT 阶段推不动。需要后端 V1 事件显式带 `stage` 枚举。 | maishac / Microsoft DevUI | 0.5 天 |
| ✅ 修复循环"第 N 轮 / 剩 N 违规"显式指示 | 现在 RepairTimeline 有轮次但没有"还剩几个违规、还要跑几轮"的进度感，maishac 的 engineered fix loop 是卖点。 | maishac fix loop | 1 天 |

> P0 五项已于 2026-09-17 全部落地：Generate.vue 接入 MonacoDiffEditor inline diff + 8 阶段进度条 + 修复轮次/剩余违规指示；PipelineStage 枚举落地于 `studio/app/schemas/enums.py`；ComplianceAudit.vue 新增"导出完整报告"按钮；ArchitectureView.vue 新增追溯链 tab。

## P1

| 功能名 | 为什么需要 | 参考项目 | 工作量 |
| --- | --- | --- | --- |
| 多用户/团队协作与角色权限 | 现在是单机单用户，DO-178C 要求"作者-评审者-批准者"分离，没有角色就不能进流程评审。 | SonarQube 角色权限 | 5 天 |
| CI/CD 集成（GitHub Actions 跑 MISRA） | 现在只能本地一键生成，接不了 CI。客户要求 PR 阶段自动跑 cppcheck MISRA addon 并评论结果。 | maishac + GitHub Actions | 3 天 |
| 增量分析（只扫改动文件） | 全量 cppcheck 每次 5-15s，大项目不可接受。按 git diff 只分析改动文件能把反馈压到亚秒级。 | SonarQube incremental analysis | 4 天 |
| 自定义规则插件系统 | 内置 MISRA/CERT 不够，客户有自己的项目规约（航电/车载企业内部）。需要允许 YAML 声明新规则。 | SonarQube custom rules / ESLint plugin | 6 天 |
| 云端多 LLM 对比 | 同一需求跑 GPT/Claude/本地模型，对比合规率、代码行数、修复轮次，帮选型。 | maishac / Helicone 对比 | 4 天 |
| HITL 评审工作流落地 | 前端有开关但没有评审队列/拒绝回退/历史，只是个 flag。DO-178C 目标 SC 才需要完整。 | DO-178C review workflow | 5 天 |

## P2

| 功能名 | 为什么需要 | 参考项目 | 工作量 |
| --- | --- | --- | --- |
| 暗色模式微调 | 已有 CSS 变量但 dashboard/Generate 深色下对比度未全面走查。 | SonarQube dark mode | 1 天 |
| 全局快捷键 | 生成(Ctrl+Enter)、切 Tab、复制代码，老手需要。 | VSCode / DevUI | 0.5 天 |
| 数据导出 Excel | 客户审计要 .xlsx 汇总违规/任务，CSV 不够。 | SonarQube export | 0.5 天 |
| i18n 补全 | 已有 i18n 框架，但只中/英，且部分新组件文案硬编码（如 formalVerify 新四态标签需回扫）。 | vue-i18n | 1 天 |
| Pipeline 完成浏览器通知 | 长任务（5-15min）用户切走标签页，完成后要 Notify API 提醒。 | 通用 | 0.5 天 |
| 违规规则按严重度聚合视图 | 现在是平铺列表，几百条违规时需要按 Mandatory/Required/Advisory 分组折叠。 | SonarQube issue list | 1 天 |

## 技术债

| 项 | 说明 | 工作量 |
| --- | --- | --- |
| V1/WebSocket 双通道死代码 | legacy `/ws/agent-stream` fallback 在 V1 稳定后仍保留，维护两套解析，建议收敛。 | 1 天 |
| TaskSummary.progress 语义滥用 | RunRecords 把 `progress`（0-100 进度）当违规数展示，类型层没分开，应加 `violation_count` 字段。 | 0.5 天 |
| FormalVerificationResult 旧 key 残留 | statusPassed/badgePassed 等 i18n key 已不再被引用，四态改造后应清理。 | 0.2 天 |
| 后端 stage 枚举未契约化 | 前端 mapStageToIndex 靠子串匹配，后端 stage 命名一旦漂移就静默失效，需要 OpenAPI 枚举约束。 | 0.5 天 |
