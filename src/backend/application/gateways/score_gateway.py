"""Score Gateway - DTO 转换 + 剪贴板操作。

将领域对象转换为 DTO，供 UI 层使用。
"""

from typing import TYPE_CHECKING

from ...models.dto.score_dto import (
    SCORE_TEXT_OPTIONAL_ITEM_DEFINITIONS,
    SCORE_TEXT_OPTIONAL_KEYS,
    HistoryRecordDTO,
    ScoreSummaryDTO,
)
from ...models.entity.session_stat import SessionStat
from ...ports.clipboard import ClipboardWriter

if TYPE_CHECKING:
    from ...config.runtime_config import RuntimeConfig


class ScoreGateway:
    """成绩网关，封装 DTO 转换和剪贴板操作。

    职责：
    - 将 SessionStat 转换为 HistoryRecordDTO
    - 将 SessionStat 转换为 ScoreSummaryDTO
    - 将分数摘要复制到剪贴板

    不负责：
    - 业务流程编排
    """

    def __init__(
        self, clipboard: ClipboardWriter, runtime_config: "RuntimeConfig | None" = None
    ):
        self._clipboard = clipboard
        self._runtime_config = runtime_config
        self._enabled_optional_items = list(SCORE_TEXT_OPTIONAL_KEYS)
        self._slow_chars_limit = 10

    @property
    def enabled_optional_items(self) -> list[str]:
        if self._runtime_config:
            return list(self._runtime_config.score_text.enabled_optional_items)
        return list(self._enabled_optional_items)

    @property
    def slow_chars_limit(self) -> int:
        if self._runtime_config:
            return self._runtime_config.score_text.slow_chars_limit
        return self._slow_chars_limit

    def get_score_text_options(self) -> list[dict[str, str]]:
        return [
            {"key": key, "label": label}
            for key, label in SCORE_TEXT_OPTIONAL_ITEM_DEFINITIONS
        ]

    def is_score_text_item_enabled(self, key: str) -> bool:
        return key in set(self.enabled_optional_items)

    def set_score_text_item_enabled(self, key: str, enabled: bool) -> None:
        if key not in SCORE_TEXT_OPTIONAL_KEYS:
            return
        current = set(self.enabled_optional_items)
        if enabled:
            current.add(key)
        else:
            current.discard(key)
        self.update_score_text_config(
            enabled_optional_items=[k for k in SCORE_TEXT_OPTIONAL_KEYS if k in current]
        )

    def update_score_text_config(
        self,
        *,
        enabled_optional_items: list[str] | None = None,
        slow_chars_limit: int | None = None,
    ) -> None:
        if self._runtime_config:
            self._runtime_config.update_score_text_config(
                enabled_optional_items=enabled_optional_items,
                slow_chars_limit=slow_chars_limit,
            )
            return
        if enabled_optional_items is not None:
            allowed = set(SCORE_TEXT_OPTIONAL_KEYS)
            seen: set[str] = set()
            self._enabled_optional_items = []
            for item in enabled_optional_items:
                if item in allowed and item not in seen:
                    self._enabled_optional_items.append(item)
                    seen.add(item)
        if slow_chars_limit is not None:
            self._slow_chars_limit = min(max(int(slow_chars_limit), 1), 10)

    def build_history_record(
        self, score_data: SessionStat
    ) -> dict[str, float | int | str]:
        """构建历史记录字典。"""
        return HistoryRecordDTO.from_score_data(score_data).to_dict()

    def build_score_message(self, score_data: SessionStat | None) -> str:
        """构建分数摘要 HTML。"""
        if not score_data:
            return "获取分数失败"
        return ScoreSummaryDTO.from_score_data(score_data).to_html(
            enabled_optional_keys=self.enabled_optional_items,
            slow_chars_limit=self.slow_chars_limit,
        )

    def build_score_plain_text(self, score_data: SessionStat | None) -> str:
        """构建分数摘要纯文本。"""
        if not score_data:
            return ""
        return ScoreSummaryDTO.from_score_data(score_data).to_clipboard_text(
            enabled_optional_keys=self.enabled_optional_items,
            slow_chars_limit=self.slow_chars_limit,
        )

    def copy_score_to_clipboard(self, score_data: SessionStat | None) -> None:
        """复制分数摘要纯文本到剪贴板。"""
        plain_text = self.build_score_plain_text(score_data)
        if not plain_text:
            return
        self._clipboard.setText(plain_text)

    def _build_aggregate_items(
        self, slice_stats: list[dict]
    ) -> list[tuple[str, str, str, str]]:
        n = len(slice_stats)
        if n == 0:
            return []

        avg_speed = sum(s["speed"] for s in slice_stats) / n
        avg_keystroke = sum(s["keyStroke"] for s in slice_stats) / n
        avg_code_length = sum(s["codeLength"] for s in slice_stats) / n
        total_chars = sum(s["char_count"] for s in slice_stats)
        total_wrong = sum(s["wrong_char_count"] for s in slice_stats)
        total_backspace = sum(s["backspace_count"] for s in slice_stats)
        total_correction = sum(s["correction_count"] for s in slice_stats)
        total_selection = sum(s.get("selection_count", 0) for s in slice_stats)
        total_time = sum(s["time"] for s in slice_stats)
        total_key_strokes = sum(s.get("key_stroke_count", 0) for s in slice_stats)
        key_accuracy = (
            (total_key_strokes - total_backspace - total_correction * avg_code_length)
            / total_key_strokes
            * 100
            if total_key_strokes > 0
            else 100.0
        )
        optional = set(self.enabled_optional_items)
        all_items = [
            ("speed", "速度", f"{avg_speed:.2f}", "字/分"),
            ("key_stroke", "击键", f"{avg_keystroke:.2f}", "击/秒"),
            ("code_length", "码长", f"{avg_code_length:.2f}", "击/字"),
            ("wrong_chars", "错字", f"{total_wrong}", "字"),
            ("corrections", "回改", f"{total_correction}", "次"),
            ("backspaces", "退格", f"{total_backspace}", "次"),
            ("selections", "选重", f"{total_selection}", "次"),
            ("key_accuracy", "键准", f"{key_accuracy:.2f}", "%"),
            ("char_count", "字数", f"{total_chars}", ""),
            ("time", "用时", f"{total_time:.3f}", "秒"),
            ("key_count", "键数", f"{total_key_strokes}", ""),
        ]
        return [
            item
            for item in all_items
            if item[0] in {"speed", "key_stroke", "code_length"} or item[0] in optional
        ]

    def build_aggregate_message(self, slice_stats: list[dict], slice_count: int) -> str:
        """构建分片模式综合成绩 HTML 消息。

        Args:
            slice_stats: 每片 SessionStat 快照列表（dict 格式）
            slice_count: 片数
        """
        items = self._build_aggregate_items(slice_stats)
        if not items:
            return ""

        lines = [f"<b>综合成绩（{slice_count}片）</b><br>"]
        for _key, label, value_str, unit in items:
            if unit in ("秒", "%"):
                lines.append(f"{label}: <b>{value_str}</b>{unit}<br>")
            elif unit:
                lines.append(f"{label}: <b>{value_str}</b> {unit}<br>")
            else:
                lines.append(f"{label}: <b>{value_str}</b><br>")
        return "".join(lines)

    def build_aggregate_plain_text(
        self, slice_stats: list[dict], slice_count: int
    ) -> str:
        """构建分片模式综合成绩纯文本（木易单行格式，用于剪贴板）。"""
        items = self._build_aggregate_items(slice_stats)
        if not items:
            return ""

        parts = [f"综合成绩（{slice_count}片）"]
        for _key, label, value_str, unit in items:
            if unit in ("秒", "%"):
                parts.append(f"{label}{value_str}{unit}")
            else:
                parts.append(f"{label}{value_str}")
        return " ".join(parts)
