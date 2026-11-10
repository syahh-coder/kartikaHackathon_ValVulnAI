import json
import os
from pathlib import Path
from uuid import uuid4


def safe_path(root: Path, name: str) -> Path:
    if Path(name).name != name or "/" in name or "\\" in name or name in {".", ".."}:
        raise ValueError("PATH_DENIED")
    path = root / name
    if root.is_symlink() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("PATH_DENIED")
    return path


def read_json(root: Path, name: str, maximum: int = 1048576) -> dict:
    path = safe_path(root, name)
    # O_NOFOLLOW also protects the last component against a symlink swap on Linux.
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        data = stream.read(maximum+1)
    if len(data)>maximum:
        raise ValueError("FILE_LIMIT")
    result = json.loads(data)
    if not isinstance(result, dict):
        raise ValueError("OBJECT_REQUIRED")
    return result


def write_json(root: Path, name: str, value: dict, maximum: int = 1048576):
    path = safe_path(root, name)
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if len(data)>maximum:
        raise ValueError("FILE_LIMIT")
    temporary = root / (str(uuid4())+".partial")
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
