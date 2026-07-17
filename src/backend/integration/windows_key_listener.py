"""Windows global keyboard listener based on a low-level keyboard hook."""

from __future__ import annotations

import ctypes
import sys
import threading
from ctypes import wintypes
from typing import Any

from PySide6.QtCore import QObject, Signal

from ..ports.key_codes import KeyCodes
from ..utils.logger import log_info

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012
PM_NOREMOVE = 0x0000


class KBDLLHOOKSTRUCT(ctypes.Structure):
    """Windows KBDLLHOOKSTRUCT passed to WH_KEYBOARD_LL callbacks."""

    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


VK_TO_EVDEV = {
    0x08: KeyCodes.EVDEV_BACKSPACE,
    0x30: KeyCodes.EVDEV_0,
    0x31: KeyCodes.EVDEV_1,
    0x32: KeyCodes.EVDEV_2,
    0x33: KeyCodes.EVDEV_3,
    0x34: KeyCodes.EVDEV_4,
    0x35: KeyCodes.EVDEV_5,
    0x36: KeyCodes.EVDEV_6,
    0x37: KeyCodes.EVDEV_7,
    0x38: KeyCodes.EVDEV_8,
    0x39: KeyCodes.EVDEV_9,
    0x60: KeyCodes.EVDEV_0,
    0x61: KeyCodes.EVDEV_1,
    0x62: KeyCodes.EVDEV_2,
    0x63: KeyCodes.EVDEV_3,
    0x64: KeyCodes.EVDEV_4,
    0x65: KeyCodes.EVDEV_5,
    0x66: KeyCodes.EVDEV_6,
    0x67: KeyCodes.EVDEV_7,
    0x68: KeyCodes.EVDEV_8,
    0x69: KeyCodes.EVDEV_9,
    0xBA: KeyCodes.EVDEV_SEMICOLON,
    0xDE: KeyCodes.EVDEV_APOSTROPHE,
    0xA2: KeyCodes.EVDEV_LEFT_CTRL,
    0xA3: KeyCodes.EVDEV_RIGHT_CTRL,
    0xA0: KeyCodes.EVDEV_LEFT_SHIFT,
    0xA1: KeyCodes.EVDEV_RIGHT_SHIFT,
    0xA4: KeyCodes.EVDEV_LEFT_ALT,
    0xA5: KeyCodes.EVDEV_RIGHT_ALT,
    0x5B: KeyCodes.EVDEV_LEFT_META,
    0x5C: KeyCodes.EVDEV_RIGHT_META,
    0x14: KeyCodes.EVDEV_CAPS_LOCK,
    0x24: KeyCodes.EVDEV_HOME,
    0x23: KeyCodes.EVDEV_END,
    0x26: KeyCodes.EVDEV_UP,
    0x28: KeyCodes.EVDEV_DOWN,
    0x25: KeyCodes.EVDEV_LEFT,
    0x27: KeyCodes.EVDEV_RIGHT,
    0x21: KeyCodes.EVDEV_PAGEUP,
    0x22: KeyCodes.EVDEV_PAGEDOWN,
    0x2D: KeyCodes.EVDEV_INSERT,
    0x2E: KeyCodes.EVDEV_DELETE,
}


VK_IGNORED = frozenset(
    {
        0x09,  # Tab：焦点导航，不参与打字击键
        0x0D,  # Enter：换行/确认，不参与正文输入统计
        0x1B,  # Escape
        *range(0x70, 0x88),  # F1-F24
    }
)


VK_COUNTABLE = frozenset(
    {
        0x20,  # Space
        *range(0x30, 0x3A),  # 0-9
        *range(0x41, 0x5B),  # A-Z
        *range(0x60, 0x6F),  # Numpad digits/operators
        *range(0xBA, 0xC1),  # OEM punctuation
        *range(0xDB, 0xE0),  # OEM punctuation
        0xE2,  # OEM angle/backslash key
    }
)


def _vk_to_evdev(vk_code: int) -> int | None:
    if vk_code in VK_TO_EVDEV:
        return VK_TO_EVDEV[vk_code]
    if vk_code in VK_IGNORED:
        return None
    if vk_code in VK_COUNTABLE:
        return vk_code
    return None


class WindowsKeyListener(QObject):
    """Listen for Windows hardware key-down events before IME handling."""

    keyPressed = Signal(int, str)

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise ImportError("Windows only")

        super().__init__()
        self._thread: threading.Thread | None = None
        self._hook_handle: int | None = None
        self._thread_id = 0
        self._hook_proc: Any | None = None
        self._pressed_shortcut_modifiers: set[int] = set()
        self._started_event = threading.Event()
        self._startup_error: str | None = None
        self._user32: Any | None = None
        self._kernel32: Any | None = None

    def start(self) -> None:
        """Install the hook and start the Windows message loop thread."""
        if self._thread and self._thread.is_alive():
            return

        self._started_event.clear()
        self._startup_error = None
        self._thread = threading.Thread(
            target=self._run_hook_loop,
            name="typetype-windows-key-listener",
            daemon=True,
        )
        self._thread.start()
        if not self._started_event.wait(timeout=2):
            raise RuntimeError("Windows 键盘监听不可用：钩子线程启动超时。")
        if self._startup_error:
            raise RuntimeError(self._startup_error)
        log_info("Windows 全局键盘监听器已启动")

    def stop(self) -> None:
        """Stop the listener message loop."""
        if self._user32 and self._thread_id:
            self._user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)
        self._thread = None
        self._thread_id = 0
        self._hook_handle = None
        self._hook_proc = None
        self._pressed_shortcut_modifiers.clear()
        log_info("Windows 全局键盘监听器已停止")

    # === Protocol stubs（Windows 无设备枚举概念，不会调用） ===

    def get_all_devices(self) -> list[dict[str, Any]]:
        return []

    def get_selected_device_paths(self) -> list[str]:
        return []

    def set_selected_device_paths(self, paths: list[str]) -> None:
        pass

    def has_selected_devices(self) -> bool:
        return False

    def get_active_device_paths(self) -> list[str]:
        return []

    def restart_with_selection(self, paths: list[str]) -> None:
        pass

    def restart_auto_detect(self) -> None:
        pass

    def _run_hook_loop(self) -> None:
        try:
            user32, kernel32, hook_proc_type = self._load_windows_api()
            self._user32 = user32
            self._kernel32 = kernel32
            self._thread_id = int(kernel32.GetCurrentThreadId())
            msg = wintypes.MSG()
            user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_NOREMOVE)
            self._hook_proc = hook_proc_type(self._callback)
            self._hook_handle = user32.SetWindowsHookExW(
                WH_KEYBOARD_LL,
                self._hook_proc,
                kernel32.GetModuleHandleW(None),
                0,
            )
            if not self._hook_handle:
                self._startup_error = "Windows 键盘监听不可用：SetWindowsHookExW 失败。"
                self._started_event.set()
                return

            self._started_event.set()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as exc:
            self._startup_error = f"Windows 键盘监听不可用：{exc}"
            self._started_event.set()
        finally:
            if self._user32 and self._hook_handle:
                self._user32.UnhookWindowsHookEx(self._hook_handle)
            self._hook_handle = None

    @staticmethod
    def _load_windows_api() -> tuple[Any, Any, Any]:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hook_proc_type = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(
            wintypes.LPARAM,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            hook_proc_type,
            wintypes.HINSTANCE,
            wintypes.DWORD,
        ]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.CallNextHookEx.argtypes = [
            wintypes.HHOOK,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.CallNextHookEx.restype = wintypes.LPARAM
        user32.PeekMessageW.argtypes = [
            ctypes.POINTER(wintypes.MSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.PeekMessageW.restype = wintypes.BOOL
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        user32.GetMessageW.argtypes = [
            ctypes.POINTER(wintypes.MSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.GetMessageW.restype = wintypes.BOOL
        user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.TranslateMessage.restype = wintypes.BOOL
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.DispatchMessageW.restype = wintypes.LPARAM
        user32.PostThreadMessageW.argtypes = [
            wintypes.DWORD,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.PostThreadMessageW.restype = wintypes.BOOL
        kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        return user32, kernel32, hook_proc_type

    def _callback(self, n_code: int, w_param: int, l_param: int) -> int:
        user32 = self._user32
        if not user32:
            return 0

        if n_code < 0:
            return user32.CallNextHookEx(None, n_code, w_param, l_param)

        kb = ctypes.cast(
            l_param,
            ctypes.POINTER(KBDLLHOOKSTRUCT),
        )[0]
        normalized = _vk_to_evdev(int(kb.vkCode))
        if normalized is None:
            return user32.CallNextHookEx(None, n_code, w_param, l_param)

        is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
        is_up = w_param in (WM_KEYUP, WM_SYSKEYUP)

        if KeyCodes.is_shortcut_modifier(normalized):
            if is_down:
                self._pressed_shortcut_modifiers.add(normalized)
            elif is_up:
                self._pressed_shortcut_modifiers.discard(normalized)

        if is_down and not self._should_ignore(normalized):
            self.keyPressed.emit(normalized, "Windows keyboard")

        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _should_ignore(self, key_code: int) -> bool:
        if KeyCodes.is_shortcut_modifier(key_code) or KeyCodes.is_backspace(key_code):
            return False
        return bool(self._pressed_shortcut_modifiers)
