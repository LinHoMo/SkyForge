"""V1 task event Pydantic 模型（用于 OpenAPI schema 契约化）。

WebSocket 事件本身不生成 OpenAPI，但通过把该模型挂到 HTTP 路由的
``responses`` 上，FastAPI 会把 ``PipelineStage`` 枚举与事件字段一并写入
``/openapi.json`` 的 components，使前端可按契约消费 ``stage`` 字段，
避免后端 stage 命名漂移导致前端静默失效。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.enums import PipelineStage


class TaskEventOut(BaseModel):
    """V1 task 事件（WS /api/v1/tasks/{id}/events 推送单元）。"""

    seq: int = Field(description="事件序列号，单调递增，用于断线重连 after_seq 重放")
    task_id: str = Field(description="所属任务 ID")
    stage: PipelineStage | None = Field(
        default=None,
        description=(
            "Pipeline 阶段枚举。前端进度条直接按此驱动，不再靠 agent 名/日志关键字猜测。"
            "取值: requirement/architecture/contract/code/misra/simulation/verify/report。"
        ),
    )
    level: str = Field(description="日志级别: info/success/warn/error/complete")
    agent: str = Field(description="Agent 徽章名，如 REQ-Parser/CON-Gen/REPAIR")
    message: str = Field(description="日志正文")
    evidence_status: str = Field(description="证据状态: observed/simulated/unavailable")
    round_number: int | None = Field(
        default=None,
        description="当前修复轮次（1-based），仅 misra 阶段事件有值",
    )
    remaining_violations: int | None = Field(
        default=None,
        description="当前剩余 MISRA 违规数，仅 misra 阶段事件有值",
    )
    time: str | None = Field(default=None, description="事件时间（ISO8601）")
