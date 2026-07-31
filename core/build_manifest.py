"""PyInstaller 动态模块清单生成。"""

from pathlib import Path


def pyinstaller_hidden_imports(project_root: Path) -> list[str]:
    """返回任务、奖励和模型目录下需要显式收集的模块。"""

    project_root = Path(project_root)
    search_roots = (
        ("models", project_root / "models"),
        ("tasks", project_root / "tasks"),
        ("tasks.reward", project_root / "tasks" / "reward"),
    )
    modules: set[str] = set()

    for package, directory in search_roots:
        if not directory.is_dir():
            continue
        for source in directory.glob("*.py"):
            if source.stem == "__init__":
                continue
            if package == "tasks" and source.stem == "base":
                continue
            modules.add(f"{package}.{source.stem}")

    return sorted(modules)
