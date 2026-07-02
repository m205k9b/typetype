"""
成绩数据结构体测试
"""

import pytest

from src.backend.models.entity.session_stat import SessionStat


class TestSessionStatInitialization:
    """测试 SessionStat 初始化"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=10,
            date="2024-01-01 00:00:00",
        )
        assert score.time == 60.0
        assert score.key_stroke_count == 300
        assert score.char_count == 240
        assert score.wrong_char_count == 10
        assert score.date == "2024-01-01 00:00:00"

    def test_negative_time_correction(self):
        """测试负时间的自动修正"""
        score = SessionStat(
            time=-10.0,
            key_stroke_count=100,
            char_count=80,
            wrong_char_count=5,
            date="",
        )
        assert score.time == 0.0

    def test_negative_key_stroke_correction(self):
        """测试负按键次数的自动修正"""
        score = SessionStat(
            time=60.0, key_stroke_count=-50, char_count=40, wrong_char_count=2, date=""
        )
        assert score.key_stroke_count == 0

    def test_negative_selection_count_correction(self):
        """测试负选重次数的自动修正"""
        score = SessionStat(selection_count=-3)
        assert score.selection_count == 0

    def test_auto_date_generation(self):
        """测试自动生成时间戳"""
        score = SessionStat(
            time=60.0, key_stroke_count=100, char_count=80, wrong_char_count=5, date=""
        )
        assert score.date
        assert len(score.date) == 19  # YYYY-MM-DD HH:MM:SS


class TestSessionStatCalculations:
    """测试成绩计算属性"""

    def test_speed_calculation(self):
        """测试速度计算（错一罚五）"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=10,
            date="",
        )
        # penalized_char_count = max(0, 240 - 10 * 5) = 190
        # speed = 190 * 60 / 60 = 190
        assert score.speed == 190.0

    def test_speed_zero_time(self):
        """测试时间为零时的速度"""
        score = SessionStat(
            time=0.0, key_stroke_count=100, char_count=80, wrong_char_count=5, date=""
        )
        assert score.speed == 0.0

    def test_keystroke_frequency(self):
        """测试击键频率计算"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=10,
            date="",
        )
        # 300 / 60 = 5
        assert score.keyStroke == 5.0

    def test_keystroke_zero_time(self):
        """测试时间为零时的击键频率"""
        score = SessionStat(
            time=0.0, key_stroke_count=100, char_count=80, wrong_char_count=5, date=""
        )
        assert score.keyStroke == 0.0

    def test_code_length(self):
        """测试码长计算"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=10,
            date="",
        )
        # 300 / 240 = 1.25
        assert score.codeLength == pytest.approx(1.25)

    def test_code_length_zero_chars(self):
        """测试字符数为零时的码长"""
        score = SessionStat(
            time=60.0, key_stroke_count=100, char_count=0, wrong_char_count=0, date=""
        )
        assert score.codeLength == 0.0

    def test_accuracy_perfect(self):
        """测试完美准确率"""
        score = SessionStat(
            time=60.0, key_stroke_count=300, char_count=240, wrong_char_count=0, date=""
        )
        assert score.accuracy == 100.0

    def test_accuracy_with_errors(self):
        """测试有错误时的准确率"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=24,
            date="",
        )
        # (240 - 24) / 240 * 100 = 90
        assert score.accuracy == 90.0

    def test_accuracy_zero_chars(self):
        """测试字符数为零时的准确率"""
        score = SessionStat(
            time=60.0, key_stroke_count=100, char_count=0, wrong_char_count=0, date=""
        )
        assert score.accuracy == 100.0

    def test_effective_speed(self):
        """测试有效速度计算（错一罚五）"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=24,
            date="",
        )
        # penalized_char_count = max(0, 240 - 24 * 5) = 120
        # speed = 120 * 60 / 60 = 120, accuracy = 90%
        # effective_speed = 120 * 0.9 = 108
        assert score.effectiveSpeed == pytest.approx(108.0)

    def test_key_accuracy_perfect(self):
        """测试无错误时的键准"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=0,
            date="",
        )
        assert score.keyAccuracy == 100.0

    def test_key_accuracy_with_errors(self):
        """测试有错键时的键准"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=10,
            backspace_count=10,
            correction_count=5,
            date="",
        )
        # codeLength = 300 / 240 = 1.25
        # wrong_keys = 10 + 5 * 1.25 = 16.25
        # keyAccuracy = (300 - 16.25) / 300 * 100 = 94.583...
        assert score.keyAccuracy == pytest.approx(94.583, rel=1e-3)

    def test_key_accuracy_zero_keystrokes(self):
        """测试按键数为零时的键准"""
        score = SessionStat(
            time=0.0, key_stroke_count=0, char_count=0, wrong_char_count=0, date=""
        )
        assert score.keyAccuracy == 100.0

    def test_key_accuracy_clamped_to_zero(self):
        """测试键准下限截断为 0"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=10,
            char_count=5,
            wrong_char_count=5,
            backspace_count=100,
            correction_count=0,
            date="",
        )
        # wrong_keys = 100 + 0 = 100, keystrokes = 10
        # raw = (10 - 100) / 10 * 100 = -900%
        assert score.keyAccuracy == 0.0


class TestPenalizedCharCount:
    """测试错一罚五的有效字数计算"""

    def test_no_wrong_chars(self):
        """无错字时有效字数等于已打字数"""
        score = SessionStat(char_count=240, wrong_char_count=0)
        assert score.penalized_char_count == 240

    def test_some_wrong_chars(self):
        """有错字时有效字数 = 已打字数 - 错字数 × 5"""
        score = SessionStat(char_count=240, wrong_char_count=10)
        assert score.penalized_char_count == 190

    def test_penalty_exceeds_char_count(self):
        """错字过多导致有效字数归零"""
        score = SessionStat(char_count=10, wrong_char_count=5)
        # 10 - 5*5 = -15 → 0
        assert score.penalized_char_count == 0

    def test_exact_zero_boundary(self):
        """刚好归零的边界"""
        score = SessionStat(char_count=25, wrong_char_count=5)
        # 25 - 25 = 0
        assert score.penalized_char_count == 0

    def test_speed_uses_penalized_count(self):
        """速度基于有效字数计算"""
        score = SessionStat(
            time=30.0,
            char_count=100,
            wrong_char_count=10,
        )
        # penalized = 100 - 50 = 50, speed = 50 * 60 / 30 = 100
        assert score.speed == 100.0


class TestWordTypingRate:
    """测试打词率字段"""

    def test_default_is_zero(self):
        """默认打词率为 0"""
        score = SessionStat()
        assert score.word_typing_rate == 0.0

    def test_can_set_non_zero(self):
        """可设置非零打词率"""
        score = SessionStat(
            time=60.0,
            key_stroke_count=300,
            char_count=240,
            wrong_char_count=0,
            word_typing_rate=85.5,
        )
        assert score.word_typing_rate == 85.5
