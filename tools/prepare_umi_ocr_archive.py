"""创建适合公开发布的 Umi-OCR 运行时归档。"""

import argparse
import hashlib
import zipfile
from pathlib import Path


_排除目录 = {"logs", "__pycache__"}
_排除后缀 = {".pyc", ".log", ".tmp"}


def _应排除(relative_path: Path) -> bool:
    lowered_parts = {part.lower() for part in relative_path.parts}
    return bool(lowered_parts & _排除目录) or (
        relative_path.suffix.lower() in _排除后缀
    )


def prepare_umi_ocr_archive(
    source: Path,
    output: Path,
    license_file: Path,
) -> str:
    """归档 Umi-OCR 并返回 ZIP 的 SHA-256。"""

    source = Path(source).resolve()
    output = Path(output).resolve()
    license_file = Path(license_file).resolve()

    if not source.is_dir():
        raise FileNotFoundError(f"Umi-OCR 目录不存在: {source}")
    executable = source / "Umi-OCR.exe"
    if not executable.is_file():
        raise FileNotFoundError(f"缺少 Umi-OCR.exe: {executable}")
    if not license_file.is_file():
        raise FileNotFoundError(f"缺少 Umi-OCR 许可证: {license_file}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for file_path in sorted(source.rglob("*")):
            if not file_path.is_file() or file_path.is_symlink():
                continue
            relative_path = file_path.relative_to(source)
            if _应排除(relative_path):
                continue
            archive.write(
                file_path,
                (Path("Umi-OCR") / relative_path).as_posix(),
            )
        archive.write(
            license_file,
            "Umi-OCR/LICENSE-Umi-OCR.txt",
        )

    digest = hashlib.sha256()
    with output.open("rb") as archive_file:
        for chunk in iter(lambda: archive_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="创建去除日志和缓存的 Umi-OCR ZIP",
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("license_file", type=Path)
    args = parser.parse_args()

    checksum = prepare_umi_ocr_archive(
        args.source,
        args.output,
        args.license_file,
    )
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
