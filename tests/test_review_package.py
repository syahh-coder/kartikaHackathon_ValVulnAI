import hashlib
import json
from zipfile import ZipFile

import pytest

from scripts.build_review_package import build


def test_package_excludes_private_data_and_records_exact_source_hashes(tmp_path):
    root, output = tmp_path/"source", tmp_path/"package"
    (root/"app").mkdir(parents=True)
    (root/"artifacts").mkdir()
    (root/"docs/sources").mkdir(parents=True)
    (root/"app/__pycache__").mkdir()
    (root/".env").write_text("PRIVATE_KEY", encoding="utf-8")
    (root/".env.example").write_text("VALVULN_TRIAGE_MODE=mock", encoding="utf-8")
    (root/"artifacts/private-gt.json").write_text('{"gt":"PRIVATE"}', encoding="utf-8")
    (root/"app/__pycache__/private.pyc").write_bytes(b"PRIVATE")
    (root/"docs/sources/guidebook.pdf").write_bytes(b"PRIVATE_PDF")
    (root/"app/main.py").write_text("# review source\n", encoding="utf-8")
    result = build(root, output)
    with ZipFile(result["archive"]) as z:
        assert set(z.namelist()) == {"valvuln-ai/.env.example", "valvuln-ai/app/main.py", "valvuln-ai/PACKAGE-MANIFEST.json"}
        manifest = json.loads(z.read("valvuln-ai/PACKAGE-MANIFEST.json"))
        assert not manifest["runtime_data_included"] and not manifest["private_gt_included"]
        for name, record in manifest["files"].items():
            assert hashlib.sha256(z.read("valvuln-ai/"+name)).hexdigest() == record["sha256"]
    assert result["sha256"] == hashlib.sha256((output/"valvuln-ai-review-source.zip").read_bytes()).hexdigest()
    with pytest.raises(FileExistsError): build(root, output)


def test_possible_secret_aborts_source_archive(tmp_path):
    (tmp_path/"app").mkdir()
    (tmp_path/"app/main.py").write_text('key="'+"sk-or-v1-"+"x"*64+'"', encoding="utf-8")
    with pytest.raises(ValueError, match="POSSIBLE_SECRET"):
        build(tmp_path, tmp_path/"output")
