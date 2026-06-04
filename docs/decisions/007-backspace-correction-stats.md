# ADR-007: 回改/退格统计指标

<!-- 状态: accepted | 最后验证: 2026-06-04 -->

## 背景

原有统计只有 `char_count`（有效字符）、`wrong_char_count`（错字），缺少：
- **回改（correction）**：输入错字后修正为正确字
- **退格（backspace）**：直接删除前一个字符（非修正）

这两个指标对分析打字习惯很重要（高回改率表示用户在犹豫，高退比率表示粗心和快速修正）。

## 选项

### A. 仅 QML 侧统计

在 QML `Keys.onPressed` 中检测退格键，累计计数。

**优点**：实现简单。
**缺点**：Wayland 下 QML 按键事件不可靠；码长统计有同样问题。

### B. 平台差异化检测

- **Wayland**：通过 evdev 直接读取 `KEY_BACKSPACE` 事件
- **非 Wayland**：通过 QML `Keys.onPressed` 检测

回改通过 `textChanged` 信号的 `growLength < 0` 检测（文本变短说明有删除+输入）。

**优点**：跨平台准确检测。
**缺点**：需要维护两套检测逻辑。

### C. 服务端统一计算

只提交原始击键序列，服务端计算所有指标。

**优点**：服务端是唯一事实来源。
**缺点**：需要传输大量原始数据；隐私问题。

## 决策

**选择 B**。平台差异化检测。

核心设计：
- `SessionStat` 新增 `backspace_count` 和 `correction_count`
- Wayland 路径：evdev `KEY_BACKSPACE` → 退格计数
- 非 Wayland 路径：QML `Keys.onPressed` 检测退格
- 回改检测：`handleCommittedText` 中 `growLength < 0`

## 影响

- **变更**：`SessionStat` 实体新增 2 个字段
- **变更**：成绩 DTO 新增 `backspace_count`、`correction_count`
- **变更**：服务端需接受新增字段

## 参考

- 设计文档：[`docs/history/2026-04-20-backspace-correction-stats-design.md`](../history/2026-04-20-backspace-correction-stats-design.md)
