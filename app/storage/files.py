import os
from pathlib import Path

from app.common import AppError, uid


def write_private(root: Path, path: Path, data: bytes, maximum: int):
    root = root.resolve()
    if len(data)>maximum or not path.resolve().is_relative_to(root):
        raise AppError(413, "ARTIFACT_LIMIT", "Artefak di luar batas storage.")
    for parent in [path, *path.parents]:
        if parent==root:
            break
        if parent.is_symlink():
            raise AppError(503, "STORAGE_UNSAFE", "Path storage tidak sah.")
    if path.exists():
        raise AppError(409, "ARTIFACT_EXISTS", "Artefak immutable sudah ada.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(uid()+".partial")
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
