"""Tests for slow entry collection based on correct commit intervals."""

from unittest.mock import patch

from src.backend.domain.services.typing_service import TypingService


def _create_service(text: str) -> TypingService:
    service = TypingService()
    service.set_plain_doc(text)
    service.set_total_chars(len(text))
    return service


def test_first_correct_single_char_uses_typing_start_time():
    service = _create_service("你")

    with patch(
        "src.backend.domain.services.typing_service.time",
        side_effect=[1.0, 1.3],
    ):
        service.start()
        updates, completed = service.handle_committed_text("你", 1)

    assert updates == [(0, "你", False)]
    assert completed is True
    assert service.state.correct_commit_entries == [("你", 300.0)]


def test_consecutive_correct_phrase_commits_stay_separate():
    service = _create_service("中国功夫")

    with patch(
        "src.backend.domain.services.typing_service.time",
        side_effect=[1.0, 1.4, 2.2],
    ):
        service.start()
        service.handle_committed_text("中国", 2)
        updates, completed = service.handle_committed_text("功夫", 2)

    assert updates == [(2, "功", False), (3, "夫", False)]
    assert completed is True
    assert service.state.correct_commit_entries == [
        ("中国", 400.0),
        ("功夫", 800.0),
    ]


def test_wrong_commit_does_not_advance_correct_commit_baseline():
    service = _create_service("你好世界")

    with patch(
        "src.backend.domain.services.typing_service.time",
        side_effect=[1.0, 1.3, 1.9, 2.1, 2.6],
    ):
        service.start()
        service.handle_committed_text("你", 1)
        service.handle_committed_text("错", 1)
        service.handle_committed_text("", -1)
        service.handle_committed_text("好", 1)

    assert service.state.correct_commit_entries == [
        ("你", 300.0),
        ("好", 1300.0),
    ]


def test_capture_slow_chars_mixes_slow_char_and_phrase_entries():
    service = _create_service("中国人")

    with patch(
        "src.backend.domain.services.typing_service.time",
        side_effect=[1.0, 1.9, 2.2],
    ):
        service.start()
        service.handle_committed_text("中国", 2)
        service.handle_committed_text("人", 1)

    service.capture_slow_chars()

    assert service.score_data.slow_chars == [("中国", 0.9)]


def test_get_history_record_rebuilds_slow_entries_without_precapture():
    service = _create_service("中国人")

    with patch(
        "src.backend.domain.services.typing_service.time",
        side_effect=[1.0, 1.9, 2.7],
    ):
        service.start()
        service.handle_committed_text("中", 1)
        service.handle_committed_text("国人", 2)

    record = service.get_history_record()

    assert record["slowChars"] == [("中", 0.9), ("国人", 0.8)]


def test_slow_entry_removes_trailing_punctuation():
    service = _create_service("文本。")
    service.state.correct_commit_entries = [("文本。", 900.0)]

    service.capture_slow_chars()

    assert service.score_data.slow_chars == [("文本", 0.9)]


def test_slow_entry_ignores_punctuation_only_commit():
    service = _create_service("。")
    service.state.correct_commit_entries = [("。", 900.0)]

    service.capture_slow_chars()

    assert service.score_data.slow_chars == []


def test_slow_entry_removes_inner_punctuation():
    service = _create_service("你，好")
    service.state.correct_commit_entries = [("你，好", 900.0)]

    service.capture_slow_chars()

    assert service.score_data.slow_chars == [("你好", 0.9)]


def test_duplicate_slow_char_keeps_slowest_entry():
    service = _create_service("你你")
    service.state.correct_commit_entries = [("你", 700.0), ("你", 1200.0)]

    service.capture_slow_chars()

    assert service.score_data.slow_chars == [("你", 1.2)]


def test_duplicate_slow_phrase_normalizes_punctuation_and_keeps_slowest():
    service = _create_service("中国。中国中国")
    service.state.correct_commit_entries = [
        ("中国。", 900.0),
        ("中国", 1300.0),
        ("中国", 800.0),
    ]

    service.capture_slow_chars()

    assert service.score_data.slow_chars == [("中国", 1.3)]


def test_slow_entries_are_limited_after_deduplication():
    service = _create_service("".join(str(i % 10) for i in range(24)))
    service.state.correct_commit_entries = [
        (f"词{i}", 1000.0 + i) for i in range(12)
    ] + [
        ("词0。", 3000.0),
        ("。", 4000.0),
    ]

    result = service._build_slow_commit_entries(limit=10)

    assert len(result) == 10
    assert result[0] == ("词0", 3.0)
    assert "。" not in [text for text, _time in result]


def test_history_record_rebuilds_normalized_deduplicated_slow_entries():
    service = _create_service("中国。中国")
    service.state.correct_commit_entries = [("中国。", 900.0), ("中国", 1200.0)]

    record = service.get_history_record()

    assert record["slowChars"] == [("中国", 1.2)]
