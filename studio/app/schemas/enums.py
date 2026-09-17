"""枚举类型定义模块。"""

from enum import Enum


class AgentType(str, Enum):
    """Agent 类型标识。"""

    REQUIREMENT_PARSER = "RequirementParserAgent"
    CONTRACT_GENERATOR = "ContractGeneratorAgent"
    CODE_GENERATOR = "CodeGeneratorAgent"
    CODE_REPAIRER = "CodeRepairerAgent"
    SIMULATION_ENGINE = "SimulationEngine"
    REPORT_GENERATOR = "ReportGenerator"


class AgentStatus(str, Enum):
    """Agent 执行状态。"""

    START = "start"
    WORKING = "working"
    DONE = "done"
    ERROR = "error"
    SUCCESS = "success"


class PipelineStage(str, Enum):
    """Pipeline 8 阶段枚举（V1 事件 ``stage`` 字段契约）。

    前端进度条直接按本枚举值驱动，不再靠 agent 名/日志关键字猜测。
    与前端 Generate.vue 的 8 阶段进度条一一对应：
    requirement → architecture → contract → code → misra → simulation → verify → report。
    """

    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    CONTRACT = "contract"
    CODE = "code"
    MISRA = "misra"
    SIMULATION = "simulation"
    VERIFY = "verify"
    REPORT = "report"
