# ADR-002: 打字会话状态机（TypingSessionContext）

<!-- 状态: accepted | 最后验证: 2026-06-04 -->

## 背景

`main.py` 中的 `appBridge`（Bridge 实例）直接承载了会话状态：`textId`、`sliceIndex`、`sliceTotal`、`passCount` 等属性。这导致：

- Presentation 层直接操作状态，违反"Bridge 是薄适配层"的原则
- 状态与 Bridge 生命周期耦合，页面切换时瞬态状态不会自动重置
- 分片载文的业务逻辑（达标检测、段切换）散落在 Bridge 中，难以测试

## 选项

### A. 在 Bridge 中增加状态管理方法

保持 Bridge 作为状态所有者，增加 `SessionContext` 属性封装状态数据。

**优点**：改动最小，QML 侧无需修改。
**缺点**：Bridge 仍承担状态职责，只是内部委托。

### B. 创建独立 SessionContext 领域对象

在 Application 层创建 `TypingSessionContext`，作为唯一状态源。Adapter 和 UseCase 通过它读写状态。

**优点**：
- 状态集中管理，职责清晰
- 状态机逻辑可独立测试
- 页面切换时由 `onActiveChanged` 集中重置
- 分片业务逻辑（达标、段切换）可以统一实现

**缺点**：需要跨层传递引用，改动面较大。

### C. 将状态提升到 QML 侧

在 TypingPage 中管理状态，Bridge 只暴露只读属性。

**优点**：符合"UI 状态由 UI 管理"的原则。
**缺点**：状态分散在多个页面，难以保证一致性；服务端提交成绩需要状态信息。

## 决策

**选择 B**。创建 `application/session_context.py` 中的 `TypingSessionContext`。

核心设计：
- 状态机阶段：`idle` → `loading` → `typing` → `ended`
- 分片模式：`slice_mode` 携带 `current_slice`、`total_slices`、`pass_count`、`slices_met`
- 上传资格推导：根据当前阶段 + 分片状态自动计算
- Adapter 只读代理：QML 通过 Bridge 间接访问，不直接持有 SessionContext

## 影响

- **正向**：Bridge 瘦身 200+ 行业务逻辑，聚焦信号转发和属性代理
- **正向**：分片载文逻辑集中到一个可测试的类
- **变更**：所有 Adapter 新增 `setup_*` 代理方法
- **变更**：QML 页面通过 `Bridge.sessionContext.xxx` 访问状态
- **变更**：`onActiveChanged` 中需重置所有瞬态状态

## 参考

- 详细设计：[`docs/history/2026-04-22-session-context-design.md`](../history/2026-04-22-session-context-design.md)
- 实施计划：[`docs/history/2026-04-26-client-server-score-contract-alignment.md`](../history/2026-04-26-client-server-score-contract-alignment.md)
