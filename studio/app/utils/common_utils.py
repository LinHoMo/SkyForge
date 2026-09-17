"""通用工具函数模块，提供任务 ID 生成、文件操作等功能。"""

import datetime
import os
import re
import secrets
from pathlib import Path

from app.utils.log_util import logger

WORK_DIR_ROOT = Path("project/work_dir").resolve()


def transform_link(task_id: str, content: str) -> str:
    """将内容中的文件路径转换为可点击的链接。"""
    if not content:
        return content

    def replace_path(match: re.Match) -> str:
        path = match.group(0)
        return f"[{path}](/task/{task_id}?file={path})"

    pattern = (
        r"(?:backend/project/work_dir/[^ \s'\"]+"
        r"|[\w/]+\.(?:c|h|yaml|json|txt|md))"
    )
    return re.sub(pattern, replace_path, content)


def split_footnotes(content: str) -> tuple[str, str]:
    """分离正文和脚注内容。"""
    if not content:
        return content, ""

    footnote_pattern = r'\[([^\]]+)\]\(#footnote-(\d+)\)'
    footnotes = []
    main_content = content

    for match in re.finditer(footnote_pattern, content):
        footnote_text = match.group(1)
        footnote_id = match.group(2)
        footnotes.append(f"[{footnote_id}]: {footnote_text}")

    main_content = re.sub(footnote_pattern, r'[\1]^{\2}', main_content)
    footnote_section = "\n\n".join(footnotes) if footnotes else ""

    return main_content, footnote_section

TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def create_task_id() -> str:
    """生成基于时间戳和密码学随机数的唯一任务 ID。"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    random_part = secrets.token_hex(4)
    return f"{timestamp}-{random_part}"


def ensure_safe_task_id(task_id: str) -> str:
    """验证任务 ID 的合法性，防止路径遍历攻击。"""
    normalized = (task_id or "").strip()
    if not normalized or not TASK_ID_PATTERN.fullmatch(normalized):
        raise ValueError("非法 task_id")
    return normalized


def create_work_dir(task_id: str) -> str:
    """为指定任务创建工作目录。"""
    work_dir = os.path.join("project", "work_dir", task_id)

    try:
        os.makedirs(work_dir, exist_ok=True)
        return work_dir
    except Exception as e:
        logger.error(f"创建工作目录失败: {str(e)}")
        raise


def get_work_dir(task_id: str) -> str:
    """获取指定任务的工作目录路径。"""
    work_dir = os.path.join("project", "work_dir", task_id)
    if os.path.exists(work_dir):
        return work_dir
    else:
        logger.error(f"工作目录不存在: {work_dir}")
        raise FileNotFoundError(f"工作目录不存在: {work_dir}")


def get_current_files(folder_path: str, type: str = "all") -> list[str]:
    """获取指定目录下的文件列表。"""
    files = os.listdir(folder_path)
    if type == "all":
        return files
    elif type == "md":
        return [file for file in files if file.endswith(".md")]
    elif type == "data":
        return [
            file for file in files if file.endswith(".xlsx") or file.endswith(".csv")
        ]
    elif type == "image":
        return [
            file for file in files if file.endswith(".png") or file.endswith(".jpg")
        ]
    return []


def safe_resolve_workdir(relative_path: str) -> Path:
    """安全地将相对路径解析到工作目录内，拒绝遍历。"""
    if not relative_path or not relative_path.strip():
        raise ValueError("path must not be empty")
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValueError(f"absolute path not allowed: {relative_path}")
    resolved = (WORK_DIR_ROOT / candidate).resolve()
    if not resolved.is_relative_to(WORK_DIR_ROOT):
        raise ValueError(f"path escapes work dir: {relative_path}")
    return resolved
