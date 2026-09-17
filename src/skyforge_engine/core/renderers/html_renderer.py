"""HTML 报告渲染器。

实现 ReportRendererProtocol，复用现有的 report_generator 生成 HTML 报告。
"""

from __future__ import annotations

from typing import Any

from skyforge_engine.report.report_generator import generate_report


class HTMLRenderer:
    """HTML 报告渲染器。

    将 ReportDataCollector 收集的数据渲染为 HTML 格式报告。
    """

    @property
    def mime_type(self) -> str:
        return "text/html"

    @property
    def format_name(self) -> str:
        return "html"

    def render(self, data: dict[str, Any]) -> str:
        """渲染 HTML 报告。"""
        return generate_report(data)
