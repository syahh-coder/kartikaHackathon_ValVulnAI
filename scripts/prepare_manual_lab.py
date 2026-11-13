"""Create one manual-only lab copy; never overwrite an existing manual database."""
import json
import subprocess

SOURCE_VOLUME = "kartikahackathon_lab_data"
DESTINATION_VOLUME = "valvuln_manual_lab_data_20261113"
SOURCE_IMAGE = "kartikahackathon-lab"

COPY_PROGRAM = r'''
import hashlib,json,os,sqlite3,uuid,shutil,tempfile
from pathlib import Path
from lab.xss_catalog import POINTS
from lab.uploads import POINTS as UPLOADS
source=Path('/source/lab.sqlite3')
destination=Path('/manual/lab.sqlite3')
if not source.is_file(): raise SystemExit('SOURCE_DB_REQUIRED')
if destination.exists(): raise SystemExit('MANUAL_DB_EXISTS_NO_OVERWRITE')
source_files=[p for p in [source,Path(str(source)+'-wal'),Path(str(source)+'-shm')] if p.exists()]
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
# Source service must be stopped: copy DB and WAL into writable temporary storage
# so SQLite can recover its shared-memory state without writing the source mount.
scratch=tempfile.TemporaryDirectory()
for item in source_files: shutil.copyfile(item,Path(scratch.name)/item.name)
original=sqlite3.connect(str(Path(scratch.name)/source.name))
copy=sqlite3.connect(destination)
original.backup(copy)
snapshot=str(uuid.uuid4())
settings={'delete_owner_check':'0','notification_dom_html':'1','snapshot_id':snapshot,
          **{k:'1' for k in POINTS.values()},**{k:'1' for k in UPLOADS.values()}}
with copy:
 for key,value in settings.items(): copy.execute('INSERT OR REPLACE INTO settings(key,value) VALUES (?,?)',(key,value))
 copy.execute('UPDATE attachments SET deleted=0')
 copy.execute("DELETE FROM settings WHERE key LIKE 'operator_%'")
 copy.execute('DELETE FROM sessions')
counts={t:copy.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['users','requests','attachments']}
copy.close();original.close()
os.chown('/manual',10001,10001);os.chown(destination,10001,10001)
after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
scratch.cleanup()
if before!=after: raise SystemExit('SOURCE_DB_HASH_CHANGED')
print(json.dumps({'status':'MANUAL_COPY_PREPARED','source_volume':'kartikahackathon_lab_data',
 'source_unchanged':True,'manual_snapshot':snapshot,'manual_volume':'valvuln_manual_lab_data_20261113',
 'enabled_points':['BAC-08','XSS-08',*POINTS,*UPLOADS],'counts':counts}))
'''


def main():
    original = subprocess.run(["docker", "volume", "inspect", SOURCE_VOLUME], capture_output=True, text=True)
    if original.returncode:
        raise SystemExit("SOURCE_VOLUME_REQUIRED")
    containers = subprocess.run(["docker", "ps", "--filter", f"volume={SOURCE_VOLUME}", "--format", "{{.ID}}"],
                                check=True, capture_output=True, text=True)
    if containers.stdout.strip():
        raise SystemExit("STOP_SOURCE_LAB_BEFORE_COPY")
    subprocess.run(["docker", "volume", "create", "--label", "valvuln.purpose=manual-verification",
                    DESTINATION_VOLUME], check=True, capture_output=True)
    result = subprocess.run(["docker", "run", "--rm", "--network", "none", "--user", "0:0",
                             "--mount", f"type=volume,src={SOURCE_VOLUME},dst=/source,readonly",
                             "--mount", f"type=volume,src={DESTINATION_VOLUME},dst=/manual",
                             "--entrypoint", "python", SOURCE_IMAGE, "-c", COPY_PROGRAM],
                            capture_output=True, text=True)
    if result.returncode:
        # Helper accepts no credentials and emits only fixed errors/metadata.
        raise SystemExit(result.stderr.strip() or "MANUAL_COPY_FAILED")
    print(result.stdout.strip())


if __name__ == "__main__":
    main()
