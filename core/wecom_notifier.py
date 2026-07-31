"""企业微信群机器人异步通知。"""

from concurrent.futures import Future, ThreadPoolExecutor
from urllib.parse import parse_qs, urlparse

import requests

from core.debug import 调试器


_通知执行器 = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="wecom-notify",
)


class 企业微信通知器:
    """校验并异步发送企业微信群机器人文本消息。"""

    def __init__(self, 会话=None, 执行器=None):
        self._会话 = 会话 or requests.Session()
        self._执行器 = 执行器 or _通知执行器

    @staticmethod
    def 地址有效(webhook: str) -> bool:
        if not isinstance(webhook, str) or not webhook.strip():
            return False
        try:
            parsed = urlparse(webhook.strip())
        except ValueError:
            return False
        return (
            parsed.scheme == "https"
            and parsed.hostname == "qyapi.weixin.qq.com"
            and parsed.path == "/cgi-bin/webhook/send"
            and bool(parse_qs(parsed.query).get("key", [""])[0])
        )

    def 异步发送文本(
        self,
        webhook: str,
        content: str,
    ) -> Future | None:
        webhook = (webhook or "").strip()
        content = (content or "").strip()
        if not self.地址有效(webhook):
            调试器.warning("聊天通知", "企业微信机器人地址无效，已跳过")
            return None
        if not content:
            调试器.warning("聊天通知", "企业微信通知内容为空，已跳过")
            return None
        return self._执行器.submit(self._发送文本, webhook, content)

    def _发送文本(self, webhook: str, content: str) -> bool:
        try:
            response = self._会话.post(
                webhook,
                json={
                    "msgtype": "text",
                    "text": {"content": content},
                },
                timeout=(3.05, 5.0),
            )
            response.raise_for_status()
            result = response.json()
        except Exception as exc:
            调试器.warning(
                "聊天通知",
                f"企业微信发送失败: {type(exc).__name__}",
            )
            return False

        error_code = result.get("errcode")
        if error_code != 0:
            error_message = str(result.get("errmsg", "unknown"))[:160]
            调试器.warning(
                "聊天通知",
                f"企业微信返回错误: errcode={error_code}, errmsg={error_message}",
            )
            return False

        调试器.info("聊天通知", "企业微信祖龙通知发送成功")
        return True
