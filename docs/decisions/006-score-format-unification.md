# ADR-006: 成绩展示格式统一与 sliceStatusBar 导航

<!-- 状态: accepted | 最后验证: 2026-06-04 -->

## 背景

客户端和服务端成绩指标定义不一致：
- 客户端独立计算 `speed`（字/分钟）、`accuracy`（%）、`codeLength`、`keystrokes`
- 服务端可能用不同公式计算，或字段名不匹配
- 分片模式的"达标"逻辑在客户端实现，服务端无法感知

## 选项

### A. 客户端完全自算

客户端独立计算所有指标，不依赖服务端。

**优点**：完全可控，无接口变更。
**缺点**：服务端无法做跨文本对比；客户端计算可能有 bug。

### B. 客户端+服务端对齐

定义统一的 DTO，客户端和服务端都用同一套公式。

**优点**：数据一致性有保障。
**缺点**：需要服务端改造；历史数据可能不兼容。

### C. 客户端自算 + 服务端信任

客户端计算所有指标，服务端只存储和展示，不做二次计算。

**优点**：服务端无需改动；客户端有控制权。
**缺点**：服务端完全信任客户端数据。

## 决策

**选择 C**。客户端计算所有指标并打包提交，服务端不做二次计算。

核心设计：
- `ScoreSummaryDTO` 和 `HistoryRecordDTO` 统一格式
- 服务端 `@PreAuthorize` 校验提交频率（5s 间隔）
- 成绩指标由客户端 `TypingService` 计算，通过 `ScoreSubmitter` 提交
- 新增 `sliceStatusBar` 导航组件，显示分片进度和达标状态

## 影响

- **正向**：服务端无需做计算逻辑变更
- **变更**：客户端 DTO 结构统一，消除版本差异
- **注意**：服务端需做防刷校验（提交频率限制）

## 参考

- 设计文档：[`docs/history/2026-04-25-score-format-unification-design.md`](../history/2026-04-25-score-format-unification-design.md)
- 实施计划：[`docs/history/2026-04-25-score-format-unification.md`](../history/2026-04-25-score-format-unification.md)
