import unittest
from concurrent.futures import Future

from core.wecom_notifier import 企业微信通知器


VALID_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    "?key=00000000-0000-0000-0000-000000000000"
)


class Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"errcode": 0, "errmsg": "ok"}


class Session:
    def __init__(self):
        self.calls = []

    def post(self, url, *, json, timeout):
        self.calls.append((url, json, timeout))
        return Response()


class InlineExecutor:
    def submit(self, function, *args):
        future = Future()
        future.set_result(function(*args))
        return future


class EnterpriseWeChatNotifierTests(unittest.TestCase):
    def test_only_accepts_enterprise_wechat_group_robot_urls(self):
        self.assertTrue(企业微信通知器.地址有效(VALID_URL))
        self.assertFalse(企业微信通知器.地址有效(""))
        self.assertFalse(
            企业微信通知器.地址有效(
                "https://example.com/cgi-bin/webhook/send?key=x"
            )
        )
        self.assertFalse(
            企业微信通知器.地址有效(
                "http://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=x"
            )
        )

    def test_send_posts_exact_text_payload_with_bounded_timeout(self):
        session = Session()
        notifier = 企业微信通知器(session, InlineExecutor())

        future = notifier.异步发送文本(VALID_URL, "祖龙刷新")

        self.assertTrue(future.result())
        self.assertEqual(
            (
                VALID_URL,
                {"msgtype": "text", "text": {"content": "祖龙刷新"}},
                (3.05, 5.0),
            ),
            session.calls[0],
        )

    def test_rejects_empty_text_without_submitting(self):
        notifier = 企业微信通知器(Session(), InlineExecutor())

        self.assertIsNone(notifier.异步发送文本(VALID_URL, "  "))
