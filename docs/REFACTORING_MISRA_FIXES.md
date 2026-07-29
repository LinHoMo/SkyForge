# misra_fixes.py 重构方案

> 文件：`src/skyforge_engine/agents/misra_fixes.py`
> 现状：3500 多行，130 个修复函数，结构高度重复
> 状态：待实施

## 问题

现在每个修复函数都是一个模子刻出来的：

```python
def _fix_rule_XX_X(code: str, v: "Violation") -> tuple[str, RepairAction]:
    """Rule XX.X：描述。"""
    lines = code.splitlines(keepends=True)
    if not (0 < v.line <= len(lines)):
        return code, RepairAction(...)
    old_line = lines[v.line - 1]
    new_line = re.sub(...)
    if new_line == old_line:
        new_line = old_line.rstrip("\n") + "  /* [Rule-XX.X] TODO: ... */\n"
    lines[v.line - 1] = new_line
    new_code = "".join(lines)
    action = RepairAction(...)
    return new_code, action
```

130 个函数里九成形神都一样，真正不一样的就三样：正则模式、替换串、描述文本。新加一条规则要抄一整段，改个边界处理得去 130 个地方同步。

## 方案 A：通用修复器 + 规则配置（倾向这个）

把每条规则抽成配置：

```python
_MISRA_RULES: dict[str, dict[str, str]] = {
    "8.1": {
        "description": "函数必须要有原型",
        "pattern": r"^(void|int|double|...)\s+(\w+)\s*\(([^)]*)\)\s*\{?\s*$",
        "replacement": r"\1 \2(\3);",
        "todo_template": "/* [Rule-8.1] TODO: 添加函数原型声明 */",
    },
    # ... 其他规则
}

def _generic_fix_rule(code: str, v: "Violation", rule_config: dict) -> tuple[str, "RepairAction"]:
    lines = code.splitlines(keepends=True)
    if not (0 < v.line <= len(lines)):
        return code, RepairAction(rule_id=v.rule_id, line=v.line, description=f"{rule_config['description']}: 行号越界，跳过")
    old_line = lines[v.line - 1]
    new_line = re.sub(rule_config["pattern"], rule_config["replacement"], old_line)
    if new_line == old_line:
        new_line = old_line.rstrip("\n") + f"  {rule_config['todo_template']}\n"
    lines[v.line - 1] = new_line
    return "".join(lines), RepairAction(
        rule_id=v.rule_id, line=v.line,
        description=rule_config["description"],
        before=old_line.strip(), after=new_line.strip(),
    )

FIXERS = {rule_id: lambda code, v, cfg=cfg: _generic_fix_rule(code, v, cfg)
          for rule_id, cfg in _MISRA_RULES.items()}
```

## 方案 B：装饰器注册

保留原函数壳，用装饰器把它们挂进注册表，公共逻辑抽到 `_generic_fix`：

```python
@register_fixer("8.1", "函数必须要有原型", r"...", r"...", "/* [Rule-8.1] TODO */")
def _fix_rule_8_1(code, v):
    return _generic_fix(code, v, pattern, replacement, todo)
```

这个方案比 A 啰嗦一点，但每条规则的特殊处理还能留在自己函数里。

## 预期效果

| 指标 | 重构前 | 重构后 |
|------|--------|--------|
| 总行数 | 3500+ | ~600 |
| 函数数量 | 130 | 1 个通用函数 + 配置表 |
| 重复代码 | ~90% | <10% |
| 加一条规则 | ~20 行 | 一行配置 |

## 风险

正则在不同代码上下文里行为可能有细微差别，属于中风险。建议先挑 5 条最常用的规则试点，跟现有输出对一遍没问题再全量搬。回归测试靠 `test_code_repairer.py`，搬完必须全绿。

## 步骤

1. 把 130 个函数的正则、替换、描述抽到配置表
2. 写 `_generic_fix_rule()`
3. 替换 FIXERS 字典
4. 跑测试
5. 删旧函数

优先级中等，现在功能正常，主要收益在以后维护。
