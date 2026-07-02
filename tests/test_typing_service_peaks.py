from src.backend.domain.services.typing_service import PEAK_DELAY_SECONDS, TypingService


def test_peaks_start_after_one_second() -> None:
    service = TypingService()
    stat = service.score_data

    stat.time = PEAK_DELAY_SECONDS - 0.1
    stat.char_count = 10
    stat.key_stroke_count = 10
    service.update_peaks()

    assert service.peak_speed == 0.0
    assert service.peak_key_stroke == 0.0
    assert service.peak_code_length == float("inf")

    stat.time = PEAK_DELAY_SECONDS
    service.update_peaks()

    assert service.peak_speed == stat.speed
    assert service.peak_key_stroke == stat.keyStroke
    assert service.peak_code_length == stat.codeLength
