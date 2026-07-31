import contextlib
import unittest

from core.debug import 线程日志管理器


class StrictCp1252Stream:
    encoding = "cp1252"

    def __init__(self):
        self.chunks = []

    def write(self, text):
        text.encode(self.encoding, errors="strict")
        self.chunks.append(text)
        return len(text)

    def flush(self):
        return None


class DebugConsoleEncodingTests(unittest.TestCase):
    def test_chinese_log_falls_back_to_escaped_text_on_cp1252_console(self):
        stream = StrictCp1252Stream()
        original_enabled = 线程日志管理器._控制台启用
        线程日志管理器._控制台启用 = True
        self.addCleanup(
            setattr,
            线程日志管理器,
            "_控制台启用",
            original_enabled,
        )

        with contextlib.redirect_stdout(stream):
            线程日志管理器._输出到控制台("祖龙刷新")

        self.assertEqual(
            "\\u7956\\u9f99\\u5237\\u65b0\n",
            "".join(stream.chunks),
        )


if __name__ == "__main__":
    unittest.main()
