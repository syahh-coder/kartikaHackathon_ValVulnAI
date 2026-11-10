import pytest

from app.common import AppError
from app.storage.files import write_private


def test_private_atomic_files_and_quotas(tmp_path):
    path = tmp_path / "evidence" / "run" / "evidence.json"
    write_private(tmp_path, path, b'{"mode":"mock"}', 100)
    assert path.read_bytes()==b'{"mode":"mock"}'
    assert not list(tmp_path.rglob("*.partial"))
    with pytest.raises(AppError):
        write_private(tmp_path, path, b"replace", 100)
    with pytest.raises(AppError):
        write_private(tmp_path, tmp_path.parent / "outside.txt", b"outside", 100)
    with pytest.raises(AppError):
        write_private(tmp_path, tmp_path / "large.txt", b"x"*101, 100)
    assert not (tmp_path / "large.txt").exists()
