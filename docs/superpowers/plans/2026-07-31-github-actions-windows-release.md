# GitHub Actions Windows Release Implementation Plan

> **Execution:** Implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mirror the tested Windows branch to `fateshen/pyauto` and produce a downloadable GitHub Actions artifact containing both the PyInstaller application and the user's local Umi-OCR runtime.

**Architecture:** Keep the 224 MB third-party OCR runtime out of Git history by publishing a sanitized, checksummed ZIP as a pinned GitHub Release asset. A Windows Actions workflow downloads that asset first, restores the locked Python environment, runs Windows-safe tests, invokes the existing deterministic PyInstaller build, merges Umi-OCR into the application directory, and uploads one complete ZIP.

**Tech Stack:** Python 3.13, `unittest`, `zipfile`, uv, PyInstaller, GitHub Actions `windows-latest`, GitHub Releases.

## Global Constraints

- GitHub repository: public `fateshen/pyauto`.
- Source branch: `windows-stable`.
- Actions triggers: pushes to `windows-stable` and manual `workflow_dispatch`.
- Umi-OCR source: `/Users/shen/Desktop/game/游戏助手/Umi-OCR`.
- Umi-OCR release tag: `umi-ocr-local-20260731`.
- Umi-OCR release asset: `Umi-OCR-local-20260731.zip`.
- Final artifact: `PyAuto-Windows-complete.zip`.
- The archive must contain `游戏助手/Umi-OCR/Umi-OCR.exe`.
- Never commit a webhook key, game login URL, Cookie, LocalStorage, cache, or log.
- Exclude Umi-OCR logs, `__pycache__`, `.pyc`, `.log`, and `.tmp` files from the public asset.
- Include the upstream Umi-OCR MIT license notice.

---

## File Structure

### New files

- `tools/prepare_umi_ocr_archive.py`: sanitizes and packages the local Umi-OCR runtime.
- `tests_windows/test_prepare_umi_ocr_archive.py`: archive layout and exclusion tests.
- `tests_windows/test_windows_release_workflow.py`: static workflow contract tests.
- `.github/workflows/windows-release.yml`: Windows test, build, bundle, and artifact upload workflow.

### Existing files used unchanged

- `build_windows.bat`: deterministic Windows PyInstaller entry point.
- `游戏助手.spec`: dynamic task/model collection and data inclusion.
- `uv.lock`: locked cross-platform dependency graph.

---

### Task 1: Sanitized Umi-OCR Release Asset

**Files:**
- Create: `tests_windows/test_prepare_umi_ocr_archive.py`
- Create: `tools/prepare_umi_ocr_archive.py`
- Produce outside Git: `/Users/shen/Desktop/game/pyauto-master/artifacts/Umi-OCR-local-20260731.zip`

**Interfaces:**
- Produces: `prepare_umi_ocr_archive(source: Path, output: Path, license_file: Path) -> str`
- Produces: a lowercase hexadecimal SHA-256 checksum.
- Consumes: one Umi-OCR directory containing `Umi-OCR.exe`.

- [ ] **Step 1: Write the failing archive tests**

```python
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
```

- [ ] **Step 2: Verify RED**

Run:

```text
/Users/shen/Desktop/game/pyauto-master/.venv-mac313/bin/python \
  -m unittest tests_windows.test_prepare_umi_ocr_archive -v
```

Expected: import error for `tools.prepare_umi_ocr_archive`.

- [ ] **Step 3: Implement the archive builder**

Implement:

```python
def prepare_umi_ocr_archive(
    source: Path,
    output: Path,
    license_file: Path,
) -> str:
```

Use `zipfile.ZipFile(..., ZIP_DEFLATED, compresslevel=6)`, map all accepted
files beneath one `Umi-OCR/` prefix, add the license as
`Umi-OCR/LICENSE-Umi-OCR.txt`, and reject missing source, executable, or
license paths. Skip any path containing `logs` or `__pycache__` and files with
`.pyc`, `.log`, or `.tmp` suffixes. Hash the completed ZIP with SHA-256.

- [ ] **Step 4: Verify GREEN**

Run:

```text
/Users/shen/Desktop/game/pyauto-master/.venv-mac313/bin/python \
  -m unittest tests_windows.test_prepare_umi_ocr_archive -v
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```text
git add tools/prepare_umi_ocr_archive.py \
  tests_windows/test_prepare_umi_ocr_archive.py
git commit -m "build: prepare sanitized Umi-OCR release asset"
```

- [ ] **Step 6: Obtain the upstream license and build the real asset**

Download the exact upstream license from:

```text
https://raw.githubusercontent.com/hiroi-sora/Umi-OCR/main/LICENSE
```

Save it outside Git, then run the archive tool against the confirmed local
source. Verify these members exist:

```text
Umi-OCR/Umi-OCR.exe
Umi-OCR/UmiOCR-data/settings
Umi-OCR/LICENSE-Umi-OCR.txt
```

Record the resulting SHA-256 checksum.

---

### Task 2: Windows Actions Workflow

**Files:**
- Create: `tests_windows/test_windows_release_workflow.py`
- Create: `.github/workflows/windows-release.yml`

**Interfaces:**
- Consumes release asset:
  `releases/download/umi-ocr-local-20260731/Umi-OCR-local-20260731.zip`
- Produces Actions artifact `PyAuto-Windows-complete`.
- Produces ZIP member layout:
  `游戏助手/游戏助手.exe` and `游戏助手/Umi-OCR/Umi-OCR.exe`.

- [ ] **Step 1: Write the failing workflow contract test**

The test reads `.github/workflows/windows-release.yml` as UTF-8 text and
asserts all of these exact contracts:

```python
required_fragments = (
    "windows-latest",
    "python-version: '3.13'",
    "uv sync --frozen --group dev",
    "python -m unittest discover -s tests_windows",
    "build_windows.bat",
    "umi-ocr-local-20260731",
    "Umi-OCR-local-20260731.zip",
    "dist\\\\游戏助手\\\\游戏助手.exe",
    "dist\\\\游戏助手\\\\Umi-OCR\\\\Umi-OCR.exe",
    "PyAuto-Windows-complete.zip",
    "actions/upload-artifact@v4",
)
```

Also assert that both `workflow_dispatch:` and the `windows-stable` push
branch are present.

- [ ] **Step 2: Verify RED**

Run:

```text
/Users/shen/Desktop/game/pyauto-master/.venv-mac313/bin/python \
  -m unittest tests_windows.test_windows_release_workflow -v
```

Expected: `FileNotFoundError` for `.github/workflows/windows-release.yml`.

- [ ] **Step 3: Create the minimal workflow**

Create a workflow with:

- `permissions: contents: read`;
- `runs-on: windows-latest`;
- `timeout-minutes: 120`;
- Umi-OCR asset download and extraction before dependency restoration so a
  missing asset fails quickly;
- `actions/setup-python@v5` with Python 3.13;
- `astral-sh/setup-uv@v6` with cache enabled;
- `uv sync --frozen --group dev`;
- standard-library `unittest` discovery;
- `cmd /c build_windows.bat`;
- explicit PowerShell file checks;
- `Compress-Archive` over `dist\游戏助手`;
- `actions/upload-artifact@v4` with `retention-days: 14`.

- [ ] **Step 4: Verify GREEN**

Run:

```text
/Users/shen/Desktop/game/pyauto-master/.venv-mac313/bin/python \
  -m unittest tests_windows.test_windows_release_workflow -v
/Users/shen/Desktop/game/pyauto-master/.venv-mac313/bin/python \
  -m pytest tests_windows -q
git diff --check
```

Expected: workflow test and the complete Windows-safe suite pass.

- [ ] **Step 5: Commit and push to Gitee**

```text
git add .github/workflows/windows-release.yml \
  tests_windows/test_windows_release_workflow.py
git commit -m "ci: build complete Windows release on GitHub"
git push origin windows-stable
```

The Umi-OCR ZIP remains outside Git.

---

### Task 3: GitHub Repository and Release Asset

**Files:**
- No tracked file changes.
- Upload:
  `/Users/shen/Desktop/game/pyauto-master/artifacts/Umi-OCR-local-20260731.zip`

**Interfaces:**
- Consumes Gitee source URL: `https://gitee.com/ios_shen/pyauto.git`
- Produces public repository: `https://github.com/fateshen/pyauto`
- Produces release:
  `https://github.com/fateshen/pyauto/releases/tag/umi-ocr-local-20260731`

- [ ] **Step 1: Import the repository**

Use the authenticated GitHub browser session to import the public Gitee
repository. Set owner `fateshen`, repository name `pyauto`, and visibility
public. Wait until import completes and verify `windows-stable` exists at the
expected local commit.

- [ ] **Step 2: Read the browser upload instructions**

Before selecting the local ZIP, read the browser client's `file-uploads`
documentation completely and use its supported local upload flow.

- [ ] **Step 3: Create the pinned Umi-OCR release**

Create tag `umi-ocr-local-20260731` targeting `windows-stable`, title it
`Local Umi-OCR runtime 20260731`, state that it contains the user's tested
runtime plus upstream MIT license, and upload exactly
`Umi-OCR-local-20260731.zip`.

- [ ] **Step 4: Verify the release**

Confirm the asset name and displayed size. Open the asset URL and ensure it is
reachable without exposing credentials. Do not upload the ZIP as ordinary Git
content.

---

### Task 4: Windows Build, Diagnosis, and Delivery

**Files:**
- Modify only workflow or source files required by an observed Windows failure.

**Interfaces:**
- Consumes the workflow and pinned Umi-OCR release from Tasks 2–3.
- Produces successful Actions run and artifact
  `PyAuto-Windows-complete`.

- [ ] **Step 1: Locate or start the workflow run**

If the import generated a failed run before the release existed, rerun it after
the asset upload. Otherwise manually dispatch `windows-release.yml` on
`windows-stable`.

- [ ] **Step 2: Monitor to a terminal result**

Inspect each step and its logs. A failure is not completion. Apply the
systematic debugging workflow to the first causal error, reproduce locally
where platform-independent, write or extend a test, and commit the smallest
fix.

- [ ] **Step 3: Mirror required fixes**

Push source fixes to Gitee. Apply the same reviewed file content to GitHub
through the authenticated repository UI if Git CLI authentication is
unavailable. Never create or expose a personal access token.

- [ ] **Step 4: Verify the successful Windows build**

Require all of:

- Windows-safe tests passed;
- `build_windows.bat` passed;
- `dist\游戏助手\游戏助手.exe` existed;
- `dist\游戏助手\Umi-OCR\Umi-OCR.exe` existed;
- `PyAuto-Windows-complete.zip` uploaded successfully.

- [ ] **Step 5: Download and checksum the final artifact**

Download the Actions artifact to:

```text
/Users/shen/Desktop/game/pyauto-master/artifacts/
```

Calculate SHA-256 and inspect the ZIP member list for both executables.

- [ ] **Step 6: Final regression and secret scan**

Run:

```text
/Users/shen/Desktop/game/pyauto-master/.venv-mac313/bin/python \
  -m pytest tests_windows -q
/Users/shen/Desktop/game/pyauto-master/.venv-mac313/bin/python \
  -m compileall -q core models ui tasks tools
git diff --check master...HEAD
```

Search tracked files for real Enterprise WeChat keys, account login links, and
credential material. Only the placeholder webhook test URL is allowed.

- [ ] **Step 7: Deliver**

Report:

- GitHub repository URL;
- Actions run URL;
- release asset URL;
- final artifact name and local file link;
- commit SHA;
- Umi-OCR source ZIP SHA-256;
- final Actions artifact SHA-256.
