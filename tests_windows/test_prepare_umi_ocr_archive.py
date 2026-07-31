import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.prepare_umi_ocr_archive import prepare_umi_ocr_archive


class PrepareUmiOcrArchiveTests(unittest.TestCase):
    def test_archive_has_one_runtime_root_and_excludes_generated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            (source / "UmiOCR-data" / "logs").mkdir(parents=True)
            (source / "UmiOCR-data" / "__pycache__").mkdir(parents=True)
            (source / "Umi-OCR.exe").write_bytes(b"exe")
            (source / "UmiOCR-data" / "model.onnx").write_bytes(b"model")
            (source / "UmiOCR-data" / "logs" / "private.log").write_text(
                "private",
                encoding="utf-8",
            )
            (source / "UmiOCR-data" / "__pycache__" / "cache.pyc").write_bytes(
                b"cache"
            )
            license_file = root / "LICENSE"
            license_file.write_text("MIT License", encoding="utf-8")
            output = root / "Umi-OCR.zip"

            checksum = prepare_umi_ocr_archive(
                source,
                output,
                license_file,
            )

            self.assertEqual(64, len(checksum))
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
            self.assertIn("Umi-OCR/Umi-OCR.exe", names)
            self.assertIn("Umi-OCR/UmiOCR-data/model.onnx", names)
            self.assertIn("Umi-OCR/LICENSE-Umi-OCR.txt", names)
            self.assertNotIn(
                "Umi-OCR/UmiOCR-data/logs/private.log",
                names,
            )
            self.assertNotIn(
                "Umi-OCR/UmiOCR-data/__pycache__/cache.pyc",
                names,
            )

    def test_missing_executable_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            license_file = root / "LICENSE"
            license_file.write_text("MIT License", encoding="utf-8")

            with self.assertRaisesRegex(
                FileNotFoundError,
                "Umi-OCR.exe",
            ):
                prepare_umi_ocr_archive(
                    source,
                    root / "output.zip",
                    license_file,
                )
