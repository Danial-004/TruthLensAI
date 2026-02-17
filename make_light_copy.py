import os
import shutil
from pathlib import Path

# === НАСТРОЙКИ ===
SOURCE_DIR = Path(r"C:\Users\Admin\Desktop\TruthLensAI2")     # Путь к исходному проекту
TARGET_DIR = Path(r"C:\Users\Admin\Desktop\TruthLensAI_light")  # Путь к "облегчённой" версии

# Папки, которые не копируем
EXCLUDE_DIRS = {
    ".git", ".idea", "__pycache__", "venv", "env", "node_modules",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".vscode",
    ".next", ".expo", "coverage", "logs", "tmp"
}

# Файлы, которые не копируем
EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db"
}

# Расширения, которые копируются
ALLOWED_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json",
    ".yml", ".yaml", ".toml", ".ini", ".env.example",
    ".md", ".txt", ".ipynb"
}

# Файлы, которые явно разрешены (независимо от расширения)
ALWAYS_INCLUDE_FILES = {
    "requirements.txt", "package.json", "pyproject.toml", "Dockerfile"
}


def should_copy(file_path: Path) -> bool:
    """
    Возвращает True, если файл должен быть скопирован в облегчённую версию.
    """
    if file_path.name in EXCLUDE_FILES:
        return False

    if file_path.name in ALWAYS_INCLUDE_FILES:
        return True

    if file_path.suffix.lower() in ALLOWED_EXTS:
        return True

    return False


def copy_lightweight_project(src: Path, dst: Path):
    """
    Копирует только нужные файлы из исходного проекта в новую папку.
    """
    if not src.exists():
        print(f"❌ Исходная папка не найдена: {src}")
        return

    if dst.exists():
        print(f"⚠️ Целевая папка уже существует. Удаляю: {dst}")
        shutil.rmtree(dst)

    dst.mkdir(parents=True)

    for root, dirs, files in os.walk(src, topdown=True):
        rel_root = Path(root).relative_to(src)

        # Удаляем исключённые директории из обхода
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file_name in files:
            file_path = Path(root) / file_name

            if should_copy(file_path):
                target_path = dst / rel_root / file_name
                target_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.copy2(file_path, target_path)
                except Exception as e:
                    print(f"❌ Ошибка при копировании {file_path}: {e}")

    print(f"\n✅ Облегчённая копия проекта создана: {dst}")


if __name__ == "__main__":
    copy_lightweight_project(SOURCE_DIR, TARGET_DIR)
