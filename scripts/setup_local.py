"""Create only missing local transport/account secrets; never rotate/reset implicitly."""
import json
from pathlib import Path
import secrets

root=Path(__file__).resolve().parents[1]/".local-data"/"secrets"
root.mkdir(parents=True,exist_ok=True)
for name,data in {
    "job-key":secrets.token_hex(32),
    "lab-accounts.json":json.dumps({alias:{"password":secrets.token_urlsafe(24)} for alias in ("requester-a","requester-b")}),
}.items():
    path=root/name
    if not path.exists():
        with path.open("x",encoding="utf-8") as stream:
            stream.write(data)
        path.chmod(0o600)
print("Konfigurasi lokal tersedia di .local-data/secrets; nilai secret tidak ditampilkan. Data lama dipertahankan.")
