import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from core.runtime_state import 运行时公共变量


def _安装窗口线程依赖替身():
    qt_core = types.ModuleType("PySide6.QtCore")
    qt_core.QObject = object
    qt_core.Signal = lambda *args, **kwargs: object()
    pyside = types.ModuleType("PySide6")
    pyside.QtCore = qt_core
    sys.modules.setdefault("PySide6", pyside)
    sys.modules.setdefault("PySide6.QtCore", qt_core)

    symbols = {
        "core.task_scheduler": {"任务调度器": object},
        "core.map_navigator": {"步骤式地图进入器": object},
        "core.page_operations": {"页面操作集": object},
        "core.action_executor": {"ActionExecutor": object},
        "core.recognition": {
            "TextRecognizer": object,
            "TemplateMatcher": object,
            "PixelAnalyzer": object,
        },
        "core.window_manager": {"capture_window": lambda *args, **kwargs: None},
        "models.dynamic_tags": {"动态标签": object},
        "core.task_executors.registry": {
            "任务执行器注册表": SimpleNamespace()
        },
        "core.common_operations": {"通用操作集": object},
        "core.assistant": {"战斗辅助识别器": object},
        "core.chat_manager": {"聊天管理器": object},
        "core.reward_manager": {"强化奖励管理器": object},
        "tasks.base": {"任务定义": object},
    }
    for name, attributes in symbols.items():
        module = types.ModuleType(name)
        for attribute, value in attributes.items():
            setattr(module, attribute, value)
        sys.modules.setdefault(name, module)

    for name in ("win32api", "win32gui", "win32con"):
        sys.modules.setdefault(name, types.ModuleType(name))


_安装窗口线程依赖替身()

from core.window_thread import 窗口线程


VALID_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    "?key=00000000-0000-0000-0000-000000000000"
)


class RecordingNotifier:
    def __init__(self):
        self.messages = []

    def 异步发送文本(self, webhook, content):
        self.messages.append((webhook, content))
        return SimpleNamespace()


def create_event_thread(*, chat_notification=True, webhook=VALID_URL):
    thread = object.__new__(窗口线程)
    thread.公共变量 = 运行时公共变量()
    thread.游戏配置 = SimpleNamespace(
        玩家=SimpleNamespace(
            启用聊天通知=chat_notification,
            企业微信机器人Webhook=webhook,
        )
    )
    thread.企业微信通知器 = RecordingNotifier()
    return thread


class ZulongNotificationTests(unittest.TestCase):
    def test_new_event_keeps_game_chat_and_sends_original_text_to_wecom(self):
        thread = create_event_thread()

        accepted = thread._处理祖龙事件(
            "张三成功召唤出了祖龙在西边",
            now=1_800_000_000.0,
        )

        self.assertTrue(accepted)
        self.assertEqual(1, len(thread.公共变量.待发送聊天队列))
        game_text = thread.公共变量.待发送聊天队列[0]["内容"]
        self.assertIn("张三召唤祖龙在晒边", game_text)
        self.assertEqual(1, len(thread.企业微信通知器.messages))
        webhook, external_text = thread.企业微信通知器.messages[0]
        self.assertEqual(VALID_URL, webhook)
        self.assertIn("张三成功召唤出了祖龙在西边", external_text)

    def test_same_banner_is_dispatched_only_once_within_sixty_seconds(self):
        thread = create_event_thread()

        first = thread._处理祖龙事件("张三召唤祖龙在西边", now=1000.0)
        duplicate = thread._处理祖龙事件(
            "张三召唤祖龙在西边",
            now=1059.0,
        )

        self.assertTrue(first)
        self.assertFalse(duplicate)
        self.assertEqual(1, len(thread.公共变量.待发送聊天队列))
        self.assertEqual(1, len(thread.企业微信通知器.messages))

    def test_disabled_chat_notification_does_not_change_game_chat(self):
        thread = create_event_thread(chat_notification=False)

        accepted = thread._处理祖龙事件(
            "李四成功召唤出了祖龙在东边",
            now=2000.0,
        )

        self.assertTrue(accepted)
        self.assertEqual(1, len(thread.公共变量.待发送聊天队列))
        self.assertEqual([], thread.企业微信通知器.messages)

    def test_monitor_updates_interval_and_handles_empty_ocr_safely(self):
        thread = object.__new__(窗口线程)
        thread.公共变量 = 运行时公共变量()
        thread.游戏配置 = SimpleNamespace(
            玩家=SimpleNamespace(
                启用通知消息=True,
                发送太古祖龙刷新通知=True,
                上部信息框检查间隔=1.3,
            ),
            区域=SimpleNamespace(
                主界面=SimpleNamespace(
                    服务器喇叭文字显示区域标签=SimpleNamespace(
                        元组=(0, 0, 8, 8)
                    )
                )
            ),
        )
        thread.截图 = np.zeros((8, 8, 3), dtype=np.uint8)
        thread.像素分析器 = SimpleNamespace(
            count_colors=lambda *args, **kwargs: [10, 20]
        )
        thread.文字识别器 = SimpleNamespace(
            recognize_text=lambda *args, **kwargs: None
        )

        with patch("core.window_thread.time.time", return_value=100.0):
            thread._太古祖龙刷新监控()

        self.assertEqual(100.0, thread.公共变量.上部信息框检查时间)
