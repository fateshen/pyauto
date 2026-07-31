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

    def test_ignores_non_python_files_and_package_initializers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "tasks/__init__.py",
                "tasks/说明.txt",
                "tasks/reward/__init__.py",
                "models/__init__.py",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")

            self.assertEqual([], pyinstaller_hidden_imports(root))
