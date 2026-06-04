<!-- 状态: active | 最后验证: 2026-06-04 -->
# 教程：第一次给 TypeType 添加功能

> 面向初次接触代码库的开发者。走完这个教程，你会理解项目的分层架构并在正确的位置添加功能。

---

## 前置条件

- Python 3.12+ 已安装
- `uv` 已安装（`curl -LsSf https://astral.sh/uv/install.sh | sh`）
- 项目代码已克隆

## 第一步：运行项目

```bash
cd /path/to/typetype
uv sync
uv run python main.py
```

你应该看到 TypeType 主窗口打开。这是 **运行时验证**——确保环境没问题。

## 第二步：跑一遍测试

```bash
uv run pytest -v
```

所有测试应该通过。如果失败，先修复测试再继续。

## 第三步：理解你改什么

打开 [ARCHITECTURE.md](../ARCHITECTURE.md) 的 **分层架构** 部分。记住一条规则：

> **QML 不直接碰业务，Domain 不直接碰 Qt。**

当你想改功能时，用下面的决策树：

| 我想加什么？ | 改这里 |
|:--- |:--- |
| 一个新的文本来源（如 PDF） | `integration/` 新建 Port 实现 + `ports/` 定义协议 + `text_source_gateway.py` 加路由 |
| 一个新的统计规则（如"连续正确率"） | `domain/services/typing_service.py` |
| 一个新的 QML 页面 | `src/qml/pages/` + `Bridge` + 对应 `Adapter` |
| 一个新的后台任务（如批量导出） | `workers/` 新建 worker + `Bridge` 暴露 Slot |

## 第四步：实际改一个功能

**任务：在 TypingPage 上添加一个"当前文本标题"显示。**

### 4.1 确定层次

这是一个 **QML 能力**（显示信息），但数据来自后端。所以：

1. **后端**：`TextAdapter` 暴露当前文本标题属性
2. **Bridge**：代理该属性到 QML
3. **QML**：在页面上显示

### 4.2 后端：TextAdapter

在 `src/backend/presentation/adapters/text_adapter.py` 中新增：

```python
# 在 class TextAdapter 中添加
current_text_title = Property(str, fget=_get_current_text_title, notify=current_text_title_changed)
```

### 4.3 Bridge

在 `src/backend/presentation/bridge.py` 中代理：

```python
current_text_title = Property(str, fget=lambda: self._text_adapter.current_text_title)
```

### 4.4 QML

在 `src/qml/pages/TypingPage.qml` 中添加：

```qml
Text {
    text: appBridge.currentTextTitle
    color: "gray"
    font.pixelSize: 14
}
```

### 4.5 测试

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

### 4.6 更新文档

按照 [AGENTS.md § 文档维护指南](../../AGENTS.md#-文档维护指南) 更新：
- `docs/reference/bridge-slots.md`：新增 `currentTextTitle` 属性
- 不需要改 ARCHITECTURE.md（没有架构变更）

## 第五步：提交

```bash
git add -A
git commit -m "feat: 在 TypingPage 显示当前文本标题"
```

---

## 常见问题

**Q: 为什么要加 Bridge 代理，QML 直接读 Adapter 不行吗？**

A: 违反了分层规则。QML → Bridge → Adapter 是正确的依赖方向。Bridge 是 QML 能看到的唯一后端门面。

**Q: 什么时候需要写 UseCase？**

A: 当有 **流程编排** 或 **分支判断** 时。单纯的属性读写或单步调用不需要 UseCase。

**Q: 测试写在哪里？**

A: 与源文件同级。`text_adapter.py` → `test_text_adapter.py`。优先测业务逻辑，不测 UI。
