"""外部工具管理器。

检测和管理 SkyForge 所需的外部工具，确保工具缺失时明确报错而非降级。
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

from app.utils.log_util import logger


@dataclass
class ToolInfo:
    """外部工具信息。"""

    name: str
    min_version: str
    description: str
    install_hint: str = ""
    found: bool = False
    version: str = ""


# SkyForge 核心外部工具清单
#
# 说明：
# - pip 可安装的工具（z3、semgrep）已纳入 pyproject.toml 依赖，
#   运行 `uv sync` 即可安装，install_hint 因此指向 uv sync / pip。
# - 系统级工具（cbmc、gcc、lcov、cppcheck）需各自平台的包管理器或安装包，
#   install_hint 给出分平台指引。
TOOLS_REQUIREMENTS: list[ToolInfo] = [
    ToolInfo(
        name="cbmc",
        min_version="6.0",
        description="形式化验证",
        install_hint="系统工具：Windows 用 winget/choco 安装 cbmc 或从 https://github.com/diffblue/cbmc/releases 下载；Linux: apt install cbmc",
    ),
    ToolInfo(
        name="z3",
        min_version="4.12",
        description="SMT约束求解",
        install_hint="运行 uv sync（已纳入项目依赖）或 pip install z3-solver",
    ),
    ToolInfo(
        name="semgrep",
        min_version="1.60",
        description="静态分析",
        install_hint="运行 uv sync（已纳入项目依赖）或 pip install semgrep",
    ),
    ToolInfo(
        name="cppcheck",
        min_version="2.0",
        description="C/C++ 静态分析",
        install_hint="系统工具：Windows 从 https://cppcheck.sourceforge.io 下载或 MSYS2 执行 pacman -S mingw-w64-ucrt-x86_64-cppcheck；Linux: apt install cppcheck",
    ),
    ToolInfo(
        name="gcc",
        min_version="14.0",
        description="代码编译",
        install_hint="系统工具：Windows 安装 MinGW-w64 或 MSYS2；Linux: apt install gcc；macOS: xcode-select --install",
    ),
    ToolInfo(
        name="lcov",
        min_version="2.0",
        description="覆盖率收集",
        install_hint="系统工具：Linux: apt install lcov；macOS: brew install lcov；Windows 经 MSYS2 安装（或改用 OpenCppCoverage）",
    ),
]


def _extract_version(text: str) -> Optional[str]:
    """从文本中提取类似 ``1.2.3`` 的版本号。"""
    match = re.search(r"(\d+(?:\.\d+){0,2})", text)
    return match.group(1) if match else None


def _version_tuple(version: str | None) -> tuple[int, ...]:
    """将版本号字符串转换为可比较的元组。"""
    if version is None:
        return ()
    return tuple(int(part) for part in version.split(".") if part.isdigit())


def check_tool_available(name: str, min_version: str) -> Optional[str]:
    """检查单个外部工具是否可用并满足最低版本。

    使用 ``shutil.which`` 在 ``PATH`` 中查找可执行文件；
    若存在，则运行 ``tool --version`` 获取版本输出，
    使用正则提取版本号并与 *min_version* 比较。

    对于 ``z3``，额外检测 Python ``z3-solver`` 包的导入可用性。
    """
    # z3 特殊处理：优先检测 Python 包，其次检测命令行二进制
    if name == "z3":
        try:
            import importlib.metadata as _meta
            ver = _meta.version("z3-solver")
            if ver and _version_tuple(ver) >= _version_tuple(min_version):
                return ver
        except Exception:
            pass
        # 也检查 z3 模块
        try:
            import z3 as _z3  # noqa: F401
            try:
                ver = _z3.get_version_string()
                if ver and _version_tuple(ver) >= _version_tuple(min_version):
                    return ver
            except Exception:
                pass
        except ImportError:
            pass

    tool_path = shutil.which(name)
    if tool_path is None:
        return None

    try:
        # Windows 上 .cmd/.bat 需要通过 shell=True 才能由 subprocess 执行
        use_shell = platform.system() == "Windows" and tool_path.lower().endswith((".cmd", ".bat"))
        result = subprocess.run(
            [name, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            shell=use_shell,
        )
        version_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    except Exception:
        version_line = ""

    actual = _extract_version(version_line)
    if actual is None:
        # 能找到但无法解析版本时，保守地视为可用
        return version_line or "unknown"

    if _version_tuple(actual) < _version_tuple(min_version):
        return None

    return actual


def check_all_tools() -> list[ToolInfo]:
    """检查 ``TOOLS_REQUIREMENTS`` 中所有工具的状态。"""
    results: list[ToolInfo] = []
    for req in TOOLS_REQUIREMENTS:
        version = check_tool_available(req.name, req.min_version)
        found = version is not None
        results.append(
            ToolInfo(
                name=req.name,
                min_version=req.min_version,
                description=req.description,
                install_hint=req.install_hint,
                found=found,
                version=version or "",
            )
        )
    return results


def check_tools_on_startup() -> list[ToolInfo]:
    """启动时检查所有外部工具并记录日志。

    对缺失或版本不足的工具打印 ``warning`` 日志，
    便于运维人员快速定位环境缺失问题。
    """
    results = check_all_tools()
    for info in results:
        if not info.found:
            hint = f" {info.install_hint}" if info.install_hint else ""
            logger.warning(
                f"外部工具缺失: {info.name} (需要 >= {info.min_version}) — {info.description}{hint}"
            )
        else:
            logger.info(
                f"外部工具就绪: {info.name}={info.version} (要求 >= {info.min_version})"
            )
    return results


def add_tools_to_path() -> None:
    """将 SkyForge 本地工具目录添加到 ``PATH``。

    优先查找用户级本地目录中的离线安装包，避免全局污染：

    - Windows: ``%LOCALAPPDATA%\\SkyForge\\tools\\bin``
    - Linux/macOS: ``~/.local/share/skyforge/tools/bin``

    若目录存在，则插入到 ``PATH`` 最前，使本地版本优先于系统版本。
    """
    system = platform.system()
    if system == "Windows":
        local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        local_bin = os.path.join(local_appdata, "SkyForge", "tools", "bin")
    else:
        local_bin = os.path.expanduser("~/.local/share/skyforge/tools/bin")

    if os.path.isdir(local_bin):
        current_path = os.environ.get("PATH", "")
        if local_bin not in current_path.split(os.pathsep):
            os.environ["PATH"] = local_bin + os.pathsep + current_path
            logger.info(f"已将本地工具目录加入 PATH: {local_bin}")
    else:
        logger.debug(f"本地工具目录不存在，跳过: {local_bin}")


# ToolExecutor: 工具标准化调用

from dataclasses import dataclass as _dc  # noqa: E402
from subprocess import run as _run  # noqa: E402
from typing import Any as _Any  # noqa: E402


@_dc
class ToolExecutionResult:
    """工具执行的标准化结果。"""

    tool_name: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    parsed_result: dict[str, _Any]
    error_message: str = ""


class ToolExecutor:
    """工具标准化执行器。

    提供统一的工具调用接口，确保所有外部工具的调用参数、
    超时控制、结果解析遵循同一规范。
    """

    @staticmethod
    def run(
        tool_name: str,
        args: list[str] | None = None,
        timeout: int = 60,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> ToolExecutionResult:
        """执行指定工具并返回标准化结果。"""
        import time as _time

        start = _time.monotonic()
        cmd_args = args or []

        try:
            result = _run(
                [tool_name] + cmd_args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=cwd,
                env=env,
                shell=False,
            )
            duration_ms = int((_time.monotonic() - start) * 1000)
            return ToolExecutionResult(
                tool_name=tool_name,
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                duration_ms=duration_ms,
                parsed_result=ToolExecutor._parse_output(tool_name, result.stdout, result.stderr),
            )
        except Exception as e:
            duration_ms = int((_time.monotonic() - start) * 1000)
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration_ms=duration_ms,
                parsed_result={},
                error_message=str(e),
            )

    @staticmethod
    def _parse_output(tool_name: str, stdout: str, stderr: str) -> dict[str, _Any]:
        """解析工具输出为结构化数据。

        每个工具可能有不同的输出格式，这里提供基础解析。
        后续可扩展为每个工具独立的解析器。
        """
        lines = stdout.strip().splitlines() + stderr.strip().splitlines()
        errors = [line for line in lines if "error" in line.lower()]
        warnings = [line for line in lines if "warning" in line.lower()]
        return {
            "total_lines": len(lines),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors[:10],
            "warnings": warnings[:10],
        }


def get_install_hint(tool_name: str) -> dict[str, str]:
    """返回指定工具在不同平台上的安装指引。"""
    hints: dict[str, dict[str, str]] = {
        "cbmc": {
            "windows": "winget install DiffBlue.CBMC 或 choco install cbmc；也可从 https://github.com/diffblue/cbmc/releases 下载",
            "linux": "apt install cbmc 或 dnf install cbmc",
            "macos": "brew install cbmc",
        },
        "z3": {
            "windows": "运行 uv sync（已纳入项目依赖）；或 pip install z3-solver",
            "linux": "运行 uv sync（已纳入项目依赖）；或 pip install z3-solver / apt install z3",
            "macos": "运行 uv sync（已纳入项目依赖）；或 pip install z3-solver / brew install z3",
        },
        "semgrep": {
            "windows": "运行 uv sync（已纳入项目依赖）；或 pip install semgrep",
            "linux": "运行 uv sync（已纳入项目依赖）；或 pip install semgrep",
            "macos": "运行 uv sync（已纳入项目依赖）；或 pip install semgrep / brew install semgrep",
        },
        "cppcheck": {
            "windows": "从 https://cppcheck.sourceforge.io 下载安装包；或 MSYS2 执行 pacman -S mingw-w64-ucrt-x86_64-cppcheck",
            "linux": "apt install cppcheck 或 dnf install cppcheck",
            "macos": "brew install cppcheck",
        },
        "gcc": {
            "windows": "安装 MinGW-w64 或 MSYS2（winget install MSYS2.MSYS2）",
            "linux": "apt install gcc 或 dnf install gcc",
            "macos": "xcode-select --install",
        },
        "lcov": {
            "windows": "经 MSYS2 安装（pacman -S mingw-w64-ucrt-x86_64-lcov）；或改用 OpenCppCoverage",
            "linux": "apt install lcov 或 dnf install lcov",
            "macos": "brew install lcov",
        },
    }
    return hints.get(tool_name, {
        "windows": f"请参考 {tool_name} 官方文档安装",
        "linux": f"请参考 {tool_name} 官方文档安装",
        "macos": f"请参考 {tool_name} 官方文档安装",
    })
