# Windows Stable Notification Implementation Plan

> **Execution:** Implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add non-blocking Enterprise WeChat Zulong notifications, fix repeated Zulong monitoring, and make the Windows PyInstaller build repeatable.

**Architecture:** Keep Windows task execution and PySide6 UI unchanged outside the notification path. Introduce one focused asynchronous WeCom adapter, extract Zulong event fan-out from screenshot recognition, persist two player settings, and derive PyInstaller hidden imports from the dynamic task/model tree.

**Tech Stack:** Python 3.13, Requests, Pydantic 2, PySide6, PyInstaller 6, unittest/pytest.

## Global Constraints

- Work only on branch `windows-stable`, based on `c2e0e6c`.
- Do not merge `macos_app`, AppKit, WKWebView, or Mac configuration.
- Never commit a real Webhook URL, key, account Cookie, or login URL.
- External HTTP must not block screenshot capture or task scheduling.
- Preserve existing in-game guild notification behavior.
- Suppress similar observations of the same Zulong banner for 60 seconds.
- Keep “聊天通知” disabled and the Webhook empty by default.
- The Windows release is the entire `dist/游戏助手` directory, not only `游戏助手.exe`.

---

## File Structure

### New files

- `core/wecom_notifier.py`: Enterprise WeChat URL validation and asynchronous text sending.
- `core/build_manifest.py`: deterministic hidden-import discovery for PyInstaller.
- `build_windows.bat`: repeatable Windows validation and PyInstaller entry point.
- `tests_windows/test_wecom_notifier.py`: notifier boundary tests.
- `tests_windows/test_notification_config.py`: player configuration persistence tests.
- `tests_windows/test_zulong_notification.py`: monitor throttling and event fan-out tests.
- `tests_windows/test_build_manifest.py`: dynamic module discovery tests.

### Modified files

- `core/runtime_state.py`: recent Zulong event state.
- `core/window_thread.py`: monitor throttling, OCR safety, deduplication, and notification fan-out.
- `models/game_config.py`: notification fields and upgrade preservation.
- `ui/global_config_tab.py`: Windows controls and edit-buffer values.
- `ui/main_window.py`: Windows file save and live-thread synchronization.
- `游戏助手.spec`: use deterministic hidden imports and validate required data directories.

---

### Task 1: Enterprise WeChat Adapter

**Files:**
- Create: `tests_windows/test_wecom_notifier.py`
- Create: `core/wecom_notifier.py`

**Interfaces:**
- Produces: `企业微信通知器.地址有效(webhook: str) -> bool`
- Produces: `企业微信通知器.异步发送文本(webhook: str, content: str) -> Future | None`

- [ ] **Step 1: Write the failing notifier tests**

```python
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
```

- [ ] **Step 2: Verify RED**

Run:

```text
python -m pytest tests_windows/test_wecom_notifier.py -q
```

Expected: collection error `No module named 'core.wecom_notifier'`.

- [ ] **Step 3: Implement the minimal notifier**

Implement strict HTTPS host/path/key validation, `ThreadPoolExecutor(max_workers=2)`, Requests `post`, nonzero `errcode` handling, and redacted logging. The public submission method returns immediately after scheduling.

- [ ] **Step 4: Verify GREEN**

Run:

```text
python -m pytest tests_windows/test_wecom_notifier.py -q
```

Expected: all notifier tests pass.

- [ ] **Step 5: Commit**

```text
git add core/wecom_notifier.py tests_windows/test_wecom_notifier.py
git commit -m "feat: add asynchronous WeCom notifier"
```

---

### Task 2: Configuration and Zulong Event Fan-out

**Files:**
- Create: `tests_windows/test_notification_config.py`
- Create: `tests_windows/test_zulong_notification.py`
- Modify: `models/game_config.py`
- Modify: `core/runtime_state.py`
- Modify: `core/window_thread.py`
- Modify: `ui/global_config_tab.py`
- Modify: `ui/main_window.py`

**Interfaces:**
- Produces: `玩家配置.启用聊天通知: bool`
- Produces: `玩家配置.企业微信机器人Webhook: str`
- Produces: `窗口线程._处理祖龙事件(text: str, now: float | None = None) -> bool`

- [ ] **Step 1: Write failing configuration tests**

```python
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
```

- [ ] **Step 2: Write failing event tests**

Use `object.__new__(窗口线程)` with real `运行时公共变量`, a complete player configuration double, and a recording notifier. Assert:

```python
accepted = thread._处理祖龙事件(
    "张三成功召唤出了祖龙在西边",
    now=1_800_000_000.0,
)
self.assertTrue(accepted)
self.assertIn(
    "张三召唤祖龙在晒边",
    thread.公共变量.待发送聊天队列[0]["内容"],
)
self.assertIn(
    "张三成功召唤出了祖龙在西边",
    thread.企业微信通知器.messages[0][1],
)
```

Call the same event at `now + 59` and assert it returns `False`, with one guild item and one external notification. Set `启用聊天通知=False` and assert the guild item remains while no external call occurs. Make OCR return `None` and assert the monitor updates `上部信息框检查时间` without raising.

- [ ] **Step 3: Verify RED**

Run:

```text
python -m pytest \
  tests_windows/test_notification_config.py \
  tests_windows/test_zulong_notification.py -q
```

Expected: missing Pydantic fields, missing event method, and the existing `len(None)` failure.

- [ ] **Step 4: Add configuration fields and Windows editor wiring**

Add safe defaults and both names to `用户保留字段`. Add Windows controls under “通知消息”; load them from `玩家配置`; include them in the global edit buffer; save them to the account file; synchronize them to a running thread.

- [ ] **Step 5: Fix monitor throttling and extract event fan-out**

Update `上部信息框检查时间` once an interval-qualified check starts, remove recursive screenshot refresh, guard empty/short OCR with `or`, accept “太古” or “祖龙”, store per-window recent event text/time, and fan out one normalized event to guild chat and the asynchronous notifier.

- [ ] **Step 6: Verify GREEN**

Run:

```text
python -m pytest \
  tests_windows/test_wecom_notifier.py \
  tests_windows/test_notification_config.py \
  tests_windows/test_zulong_notification.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```text
git add core/runtime_state.py core/window_thread.py models/game_config.py \
  ui/global_config_tab.py ui/main_window.py \
  tests_windows/test_notification_config.py \
  tests_windows/test_zulong_notification.py
git commit -m "feat: notify WeCom on deduplicated Zulong events"
```

---

### Task 3: Deterministic Windows Packaging

**Files:**
- Create: `tests_windows/test_build_manifest.py`
- Create: `core/build_manifest.py`
- Create: `build_windows.bat`
- Modify: `游戏助手.spec`

**Interfaces:**
- Produces: `pyinstaller_hidden_imports(project_root: Path) -> list[str]`
- Produces: Windows command `build_windows.bat`

- [ ] **Step 1: Write the failing build-manifest test**

```python
import tempfile
import unittest
from pathlib import Path

from core.build_manifest import pyinstaller_hidden_imports


class BuildManifestTests(unittest.TestCase):
    def test_discovers_dynamic_tasks_rewards_and_models(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "tasks/示例任务.py",
                "tasks/base.py",
                "tasks/reward/示例奖励.py",
                "models/example.py",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")

            modules = pyinstaller_hidden_imports(root)

            self.assertEqual(
                [
                    "models.example",
                    "tasks.reward.示例奖励",
                    "tasks.示例任务",
                ],
                modules,
            )
```

- [ ] **Step 2: Verify RED**

Run:

```text
python -m pytest tests_windows/test_build_manifest.py -q
```

Expected: collection error `No module named 'core.build_manifest'`.

- [ ] **Step 3: Implement discovery and update the spec**

Discover top-level `.py` files in `tasks`, `tasks/reward`, and `models`, excluding `__init__` and `tasks/base`. Import the helper in `游戏助手.spec`, set `pathex` to the project root, and raise a clear `FileNotFoundError` if `main.py`, `config`, or `帝王霸业图库` is missing.

- [ ] **Step 4: Add the Windows build script**

`build_windows.bat` must use `%~dp0`, select `.venv\Scripts\python.exe` or `py -3.13`, run `compileall`, invoke PyInstaller, verify `dist\游戏助手\游戏助手.exe`, and propagate nonzero exit codes.

- [ ] **Step 5: Verify GREEN**

Run:

```text
python -m pytest tests_windows/test_build_manifest.py -q
python -m compileall -q core models ui tasks
```

Expected: tests and compilation pass.

- [ ] **Step 6: Commit**

```text
git add core/build_manifest.py tests_windows/test_build_manifest.py \
  build_windows.bat 游戏助手.spec
git commit -m "build: make Windows packaging deterministic"
```

---

### Task 4: Regression Verification and Delivery

**Files:**
- Modify only files required by a failing verification result.

**Interfaces:**
- Consumes all interfaces from Tasks 1–3.
- Produces a tested `windows-stable` branch ready for Windows packaging.

- [ ] **Step 1: Run all Windows-safe tests**

```text
python -m pytest tests_windows -q
```

Expected: all tests pass.

- [ ] **Step 2: Run compatibility checks**

```text
python -m compileall -q core models ui tasks
git diff --check master...HEAD
```

Expected: exit code 0 and no whitespace errors.

- [ ] **Step 3: Scan for secrets**

Search tracked files for `qyapi.weixin.qq.com/cgi-bin/webhook/send?key=` followed by a non-placeholder key. The only allowed Webhook occurrences are the empty UI placeholder and zero-value test fixture.

- [ ] **Step 4: Review requirements against the design**

Confirm the branch contains: safe config defaults, Windows UI fields, asynchronous sending, 60-second per-window deduplication, OCR safety, interval timestamp update, deterministic hidden imports, and one-click Windows build validation.

- [ ] **Step 5: Push or prepare browser upload**

Try the existing authenticated Git transport without exposing credentials. If unavailable, package the exact branch diff for upload through the authenticated Gitee UI; do not create an access token or SSH key without separate user approval.

- [ ] **Step 6: Windows build handoff**

If a Windows runner is available, execute `build_windows.bat` and publish the complete `dist/游戏助手` folder. Otherwise provide the tested branch and exact author build command without claiming a Windows `.exe` was produced.
