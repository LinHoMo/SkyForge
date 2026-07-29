# 二次开发与扩展

这篇讲怎么往 SkyForge 里加东西。真正做成插件式的只有编码标准这一块；Agent 和扫描器那边是继承基类，没有独立的插件加载框架，别照着别的文档以为有 `plugins/` 目录。

## 编码标准注册表

实现在 `src/skyforge_engine/coding_standards/`。DO-178C 那套过程标准是写死的，编码规范走注册表，加新标准不用动主流程。

`base.py` 里有 `CodingStandard` 数据类和 `get_registry()`（全局单例）。注册完自动被这几个模块用上：`rag_enhancer.py` 做红线规则检测和 Agent 查询，`rule_parser.py` 做规则分类，`cppcheck_scanner.py` 走 Mock 扫描模式，`code_repairer.py` 调度修复函数。

现在注册了三个：

| 标准 ID | 名称 | 语言 | 红线规则 | 修复器 |
|---------|------|------|---------|--------|
| `misra_c_2012` | MISRA-C:2012 | C | 10 条 | 57 个 |
| `jsf_av_cpp` | MISRA C++ / JSF AV C++ / CERT C++ | C++ | 5 条 | — |
| `python_safety` | 军工软件 Python 编程规范（T/ZASDI 0002-2023） | Python | 3 条 | 4 个 |

加新的编码标准：

```python
from skyforge_engine.coding_standards.base import CodingStandard, get_registry

my_std = CodingStandard(
    standard_id="my_custom_standard",
    name="My Custom Standard",
    languages=["c"],
    version="1.0",
    rule_data_file="path/to/rules.txt",
    red_line_rules=["R1", "R2"],
    fixers={"R1": my_fixer_func},
    mock_scan_patterns=[{"pattern": r"...", "rule_id": "R1", "severity": "error", "message": "..."}],
    rule_prefix_category={"R": "Category 1"},
    agent_default_queries={"code_generator": ["query1", "query2"]},
    agent_display_names={"code_generator": "代码生成 Agent"},
    priority=100,
)

get_registry().register(my_std)
```

注册完就能 `registry.get_red_line_rules("c")`、`registry.get_fixers("c")` 这样取。

## 加扫描器

静态扫描器继承 `tools/base_scanner.py` 的 `BaseScanner`，实现 `is_available()` 和 `scan(code)`。Python 的 `RuffScanner`、`MypyScanner` 都在这个基类上，照抄一个就行：

```python
from skyforge_engine.tools.base_scanner import BaseScanner, Violation

class RustScanner(BaseScanner):
    def __init__(self):
        self._clippy_path = shutil.which("cargo")

    def is_available(self) -> bool:
        return self._clippy_path is not None

    def scan(self, code: str, **kwargs) -> list[Violation]:
        # 调 cargo clippy
        ...
```

`scan_multi(code, language="c"|"cpp"|"python")` 是统一入口，按语言分发到对应扫描器。

## 加 Agent

Agent 继承 `agents/agent.py` 的 `BaseAgent`，实现 `execute`。现有的需求解析、LLR、架构、契约、代码生成、修复都是这个套路，直接看 `agents/` 下哪个最接近你要做的，照着改。

## 加修复规则

修复函数就是个 `(code, violation) -> (new_code, RepairAction)` 的函数。C 那边在 `agents/misra_fixes.py`，Python 在 `agents/python_fixes.py`，C++ 在 `misra_cpp_fixes.py`。写好之后挂到对应编码标准的 `fixers` 表里，`code_repairer` 会按 rule_id 找到它。

## 验证器链

想加新的验证器，继承 `core/verifiers/` 下的基类，然后丢进 `VerifierChain`：

```python
from skyforge_engine.core.verifiers.chain import VerifierChain
from skyforge_engine.core.verifiers.z3_verifier import Z3Verifier

chain = VerifierChain(fail_fast=False)
chain.add(Z3Verifier())
results = chain.verify_all(code, contract)
```

每个验证器返回 `VerificationResult`，带 `passed`、`tool_name`、`tool_available`、`output` 四个字段。

---

许可证跟主项目一致，MIT。
