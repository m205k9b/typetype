# ADR-003: NavView 单实例页面切换

<!-- 状态: accepted | 最后验证: 2026-06-04 -->

## 背景

原实现使用 `StackView` 管理页面导航。存在以下问题：

1. **状态丢失**：每次 push/pop 创建新实例，页面状态（如选中的文本、分片进度）丢失
2. **信号时序复杂**：`StackView.status` 的变化与页面实际加载不同步，`Connections` 的 `enabled` 守卫在 `onActivating` 阶段为 false，导致 `textLoaded` 信号被丢弃
3. **动画开销**：push/pop 动画在快速切换时无意义且造成视觉闪烁

## 选项

### A. 保持 StackView，修复信号时序

在 `StackView.onActivated` 中延迟发送信号，修复信号时序问题。

**优点**：保留原生导航动画。
**缺点**：状态丢失问题仍在；StackView 生命周期复杂，容易出时序 bug。

### B. 改用单实例 pageInstances

移除 StackView，用 `pageInstances` 字典缓存页面实例，通过 `visible` + `active` 切换。

**优点**：
- 页面只创建一次，状态持久化
- `active` 变化语义明确，信号时序简单
- 无 push/pop 动画开销

**缺点**：需要手动管理实例生命周期；`onActiveChanged` 中需手动重置瞬态状态。

### C. 改用 TabBar

用 `TabBar` + `StackView` 的组合，每个 tab 一个 StackView。

**优点**：原生支持 tab 状态保持。
**缺点**：改变 UI 导航模式，用户习惯不同。

## 决策

**选择 B**。移除 StackView，改用 `pageInstances` 字典。

核心设计：
- 所有页面在 `Main.qml` 中预创建，缓存在 `pageInstances` 字典
- 通过 `visible: page.active` 切换可见性
- `onActiveChanged` 中重置 Bridge 瞬态状态（textId、textTitle 等）
- `safePop()` 变为空操作（无历史栈）

## 影响

- **正向**：页面状态自然持久化
- **正向**：信号时序问题根除（active 属性变化是即时的）
- **变更**：所有 QML 页面 `Connections.enabled` 从 `StackView.status === StackView.Active` 改为 `page.active`
- **变更**：`StackView.onActivating/onActivated` 替换为 `onActiveChanged`
- **注意**：`onActiveChanged` 中必须重置所有与"当前载文"相关的瞬态状态，否则成绩会提交到错误文本

## 参考

- 修改明细：`RinUI/LOCAL_MODIFICATIONS.md` § **修改 3**
- 已知陷阱：`AGENTS.md § ⚠️ 单实例页面切换时必须重置 appBridge 瞬态状态`
