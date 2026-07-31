import unittest
from pathlib import Path


class WindowsReleaseWorkflowTests(unittest.TestCase):
    def test_workflow_builds_and_bundles_complete_windows_release(self):
        workflow = Path(
            ".github/workflows/windows-release.yml"
        ).read_text(encoding="utf-8")

        required_fragments = (
            "windows-latest",
            "python-version: '3.13'",
            "uv sync --frozen --group dev",
            "python -m unittest discover -s tests_windows",
            "build_windows.bat",
            "umi-ocr-local-20260731",
            "Umi-OCR-local-20260731.zip",
            "dist\\游戏助手\\游戏助手.exe",
            "dist\\游戏助手\\Umi-OCR\\Umi-OCR.exe",
            "PyAuto-Windows-complete.zip",
            "actions/upload-artifact@v4",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, workflow)

        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("branches: [windows-stable]", workflow)
