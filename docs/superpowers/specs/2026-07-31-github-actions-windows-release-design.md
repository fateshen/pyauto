# GitHub Actions Windows Release Design

## Goal

Create a public `fateshen/pyauto` GitHub repository from the tested Gitee
`windows-stable` branch and use a GitHub-hosted Windows runner to produce a
downloadable, self-contained release ZIP.

The ZIP must contain:

- the PyInstaller `dist/游戏助手` directory;
- the user's local, working `Umi-OCR` directory;
- the existing configuration and image assets collected by PyInstaller.

## Repository Strategy

Import the existing public Gitee repository into `fateshen/pyauto` through the
authenticated GitHub web session. Preserve repository history and the
`windows-stable` branch.

The workflow is committed on `windows-stable`. It runs:

- automatically for pushes to `windows-stable`;
- manually through `workflow_dispatch`.

No Enterprise WeChat webhook, account login URL, Cookie, LocalStorage, game
cache, log file, or other private runtime data is committed.

## Umi-OCR Distribution

The local source directory is:

`/Users/shen/Desktop/game/游戏助手/Umi-OCR`

It is approximately 224 MB and contains the executable, Python runtime,
plugins, OCR models, and settings required by that executable. Committing the
directory to ordinary Git would permanently enlarge every clone, so it is
packaged as a ZIP and uploaded as a GitHub Release asset instead.

Before upload:

- exclude logs, generated caches, and transient OCR output if present;
- preserve the HTTP service configuration on `127.0.0.1:1224`;
- include the upstream Umi-OCR MIT license notice;
- calculate and record a SHA-256 checksum.

The release tag is `umi-ocr-local-20260731` and the asset is
`Umi-OCR-local-20260731.zip`. The archive contains one top-level `Umi-OCR`
directory so extraction into `dist/游戏助手` creates the exact runtime layout.

## Windows Workflow

The workflow uses `windows-latest` and performs these stages:

1. Check out `windows-stable`.
2. Install Python 3.13.
3. Install `uv`.
4. Run `uv sync --frozen --group dev` to restore dependencies from the
   committed lock file, including the PyInstaller development dependency.
5. Run the Windows-safe `unittest` suite with Python's standard library.
6. Execute `build_windows.bat`.
7. Download the pinned local Umi-OCR release asset.
8. Expand `Umi-OCR` beside `游戏助手.exe` in `dist/游戏助手`.
9. Create `PyAuto-Windows-complete.zip`.
10. Upload the ZIP as a GitHub Actions artifact.

The workflow fails if tests fail, PyInstaller does not create
`dist/游戏助手/游戏助手.exe`, the Umi-OCR asset is missing, or
`dist/游戏助手/Umi-OCR/Umi-OCR.exe` is absent after extraction.

## Permissions and Secrets

The workflow uses only the repository-provided `GITHUB_TOKEN` with read access
to repository contents and release assets. It does not need the Enterprise
WeChat webhook during build.

The real webhook remains a per-account runtime setting entered in the Windows
application after download.

## Verification and Delivery

Before enabling the workflow:

- validate the workflow YAML syntax;
- verify the source branch is the tested commit or a descendant containing
  only the workflow and documentation changes;
- verify the Umi-OCR archive checksum;
- scan tracked files for webhook keys and login credentials.

After the first run:

- inspect every failed or warning step;
- confirm the PyInstaller executable exists;
- confirm the bundled Umi-OCR executable exists;
- download the Actions artifact;
- report the run URL, artifact name, commit SHA, and checksum.

PyInstaller output can only be considered validated as a Windows build after
the GitHub-hosted Windows runner completes successfully.
