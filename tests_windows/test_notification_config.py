import unittest

from models.game_config import 玩家配置, 用户保留字段


class NotificationConfigTests(unittest.TestCase):
    def test_defaults_are_safe_and_preserved_during_upgrades(self):
        config = 玩家配置.创建默认("测试账号")

        self.assertFalse(config.启用聊天通知)
        self.assertEqual("", config.企业微信机器人Webhook)
        self.assertIn("启用聊天通知", 用户保留字段)
        self.assertIn("企业微信机器人Webhook", 用户保留字段)

    def test_notification_settings_round_trip(self):
        config = 玩家配置.创建默认("测试账号")
        config.启用聊天通知 = True
        config.企业微信机器人Webhook = "https://example.invalid"

        loaded = 玩家配置(**config.model_dump())

        self.assertTrue(loaded.启用聊天通知)
        self.assertEqual(
            "https://example.invalid",
            loaded.企业微信机器人Webhook,
        )
