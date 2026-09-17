"""LLM Provider 抽象基类。"""

from abc import ABC, abstractmethod
from skyforge_llm.types import StandardResponse


class BaseProvider(ABC):
    """LLM Provider 基类，定义统一的调用接口。"""

    @abstractmethod
    async def call(
        self,
        messages: list[dict],
        model: str,
        api_key: str,
        base_url: str | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        max_tokens: int | None = None,
        top_p: float | None = None,
    ) -> StandardResponse:
        """调用 LLM 并返回标准化响应。"""
        ...
