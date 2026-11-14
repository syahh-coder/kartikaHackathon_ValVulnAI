"""Build an explicit local source candidate. Excludes credentials, runtime data and private evaluation artifacts."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

DIRECTORIES = ("app", "boundary", "worker", "lab", "evaluator", "containers", "scripts", "tests", "docs", "submission")
FILES = ("README.md", "AGENTS.md", "plan.md", "prd.md", "pyproject.toml", "requirements.lock", "requirements-dev.lock",
         "requirements-worker.lock", "Dockerfile", "compose.yaml", "compose.preview.yaml", "compose.azure.yaml",
         "compose.manual-lab.yaml", "compose.provider.azure.yaml", "compose.provider.groq.yaml", ".github/workflows/checks.yml",
         ".env.azure.example", ".env.groq.example", ".dockerignore", ".gitignore", ".env.example")
SUFFIXES = {".py", ".sql", ".js", ".cjs", ".css", ".html", ".md", ".json", ".yaml", ".lock", ".toml", ".txt", ".png", ".svg", ".pdf", ".webm"}


def selected(root: Path):
    paths = [root/name for name in FILES if (root/name).is_file()]
    for folder in DIRECTORIES:
        for p in (root/folder).rglob("*"):
            if p.is_symlink():
                raise ValueError("SYMLINK_NOT_ALLOWED: "+p.relative_to(root).as_posix())
            relative = p.relative_to(root)
            if (not p.is_file() or any(part.startswith(".") or part == "__pycache__" for part in relative.parts) or
                    (relative.parts[:2] == ("docs", "sources") and p.suffix in {".pdf", ".txt"})):
                continue
            if p.suffix in SUFFIXES or p.name in {"Dockerfile", "PLAYWRIGHT-LICENSE"}:
                paths.append(p)
    return sorted(set(paths), key=lambda p: p.relative_to(root).as_posix())


def build(root: Path, output: Path):
    output.mkdir(parents=True, exist_ok=False)
    payload = {}
    for p in selected(root):
        if not p.resolve().is_relative_to(root.resolve()):
            raise ValueError("PATH_ESCAPE")
        data = p.read_bytes()
        # Real API keys/private keys are never intended source artifacts. Synthetic test credentials are explicitly named.
        if p.suffix not in {".png", ".pdf", ".webm"}:
            text = data.decode("utf-8")
            for key in re.findall(r"sk-or-v1-[A-Za-z0-9_-]{20,}", text):
                if "synthetic" not in key.lower():
                    raise ValueError("POSSIBLE_SECRET: "+p.relative_to(root).as_posix())
            if ("-----BEGIN " + "PRIVATE KEY-----") in text:
                raise ValueError("POSSIBLE_PRIVATE_KEY")
        payload[p.relative_to(root).as_posix()] = data
    inventory = {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for name, data in payload.items()}
    manifest = {"status": "LOCAL_REVIEW_CANDIDATE_NOT_PUBLISHED", "license": "PROJECT_LICENSE_PENDING_USER_DECISION",
                "runtime_data_included": False, "private_gt_included": False, "files": inventory}
    archive = output/"valvuln-ai-review-source.zip"
    with ZipFile(archive, "x", compression=ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in payload.items():
            info = ZipInfo("valvuln-ai/"+name, date_time=(2026, 11, 7, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            z.writestr(info, data)
        z.writestr("valvuln-ai/PACKAGE-MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/"valvuln-ai-review-source.zip.sha256").write_text(digest+"  "+archive.name+"\n", encoding="ascii")
    (output/"package-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return {"archive": str(archive), "sha256": digest, "files": len(payload), "bytes": archive.stat().st_size,
            "published": False, "license_selected": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[1], args.output)))
