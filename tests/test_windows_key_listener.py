"""WindowsKeyListener pure logic tests."""

from src.backend.integration.windows_key_listener import _vk_to_evdev
from src.backend.integration.windows_key_listener import WindowsKeyListener
from src.backend.ports.key_codes import KeyCodes


def test_vk_digit_codes_map_to_evdev_digit_codes():
    assert _vk_to_evdev(0x30) == KeyCodes.EVDEV_0
    assert _vk_to_evdev(0x31) == KeyCodes.EVDEV_1
    assert _vk_to_evdev(0x39) == KeyCodes.EVDEV_9


def test_vk_numpad_digit_codes_map_to_evdev_digit_codes():
    assert _vk_to_evdev(0x60) == KeyCodes.EVDEV_0
    assert _vk_to_evdev(0x62) == KeyCodes.EVDEV_2
    assert _vk_to_evdev(0x69) == KeyCodes.EVDEV_9


def test_countable_text_input_keys_return_vk_code():
    assert _vk_to_evdev(0x20) == 0x20
    assert _vk_to_evdev(0x41) == 0x41
    assert _vk_to_evdev(0x5A) == 0x5A
    assert _vk_to_evdev(0xBC) == 0xBC


def test_vk_selection_and_backspace_codes_map_to_evdev_codes():
    assert _vk_to_evdev(0xBA) == KeyCodes.EVDEV_SEMICOLON
    assert _vk_to_evdev(0xDE) == KeyCodes.EVDEV_APOSTROPHE
    assert _vk_to_evdev(0x08) == KeyCodes.EVDEV_BACKSPACE


def test_vk_modifier_codes_map_to_evdev_codes():
    assert _vk_to_evdev(0xA0) == KeyCodes.EVDEV_LEFT_SHIFT
    assert _vk_to_evdev(0xA1) == KeyCodes.EVDEV_RIGHT_SHIFT
    assert _vk_to_evdev(0xA2) == KeyCodes.EVDEV_LEFT_CTRL
    assert _vk_to_evdev(0xA3) == KeyCodes.EVDEV_RIGHT_CTRL
    assert _vk_to_evdev(0xA4) == KeyCodes.EVDEV_LEFT_ALT
    assert _vk_to_evdev(0xA5) == KeyCodes.EVDEV_RIGHT_ALT


def test_unmapped_vk_code_returns_none():
    assert _vk_to_evdev(0x09) is None
    assert _vk_to_evdev(0x70) is None
    assert _vk_to_evdev(0x90) is None


def test_should_ignore_switches_with_shortcut_modifier_state():
    listener = WindowsKeyListener.__new__(WindowsKeyListener)
    listener._pressed_shortcut_modifiers = set()

    assert listener._should_ignore(KeyCodes.EVDEV_2) is False

    listener._pressed_shortcut_modifiers.add(KeyCodes.EVDEV_LEFT_CTRL)
    assert listener._should_ignore(KeyCodes.EVDEV_2) is True
    assert listener._should_ignore(KeyCodes.EVDEV_LEFT_CTRL) is False
    assert listener._should_ignore(KeyCodes.EVDEV_BACKSPACE) is False

    listener._pressed_shortcut_modifiers.discard(KeyCodes.EVDEV_LEFT_CTRL)
    assert listener._should_ignore(KeyCodes.EVDEV_2) is False
