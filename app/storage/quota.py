import shutil
from pathlib import Path

from app.common import AppError
from app.config import Settings


def check_storage(config: Settings, incoming: int = 0):
    directory = config.data_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    used = 0
    for folder in (directory / "uploads", directory / "evidence"):
        if folder.is_symlink() or not folder.resolve().is_relative_to(directory):
            raise AppError(503, "STORAGE_UNSAFE", "Storage memerlukan pemeriksaan operator.")
        if folder.exists():
            for file in folder.rglob("*"):
                if file.is_symlink():
                    raise AppError(503, "STORAGE_UNSAFE", "Storage memerlukan pemeriksaan operator.")
                if file.is_file():
                    used += file.stat().st_size
    if used + incoming > config.storage_limit_bytes or shutil.disk_usage(directory).free-incoming < config.min_free_bytes:
        raise AppError(503, "STORAGE_LIMIT", "Ruang penyimpanan tidak mencukupi.")
