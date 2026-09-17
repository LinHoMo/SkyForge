"""CLI 显示工具模块，提供 ASCII 横幅和终端居中显示功能。"""


def center_cli_str(text: str, width: int | None = None):
    """将多行文本在终端中居中显示。"""
    import shutil

    width = width or shutil.get_terminal_size().columns
    lines = text.split("\n")
    max_line_len = max(len(line) for line in lines)
    return "\n".join(
        (line + " " * (max_line_len - len(line))).center(width) for line in lines
    )


def get_ascii_banner(center: bool = True) -> str:
    """获取项目 ASCII 横幅。"""
    text = "SkyForge (天锻): AI智能体驱动的机载软件轻量化开发工具"
    if center:
        return center_cli_str(text)
    else:
        return text
