from pathlib import Path
import hashlib, json, shutil, datetime

root = Path(__file__).resolve().parent
source = root.parent / 'CAPTCHA'
target = root / 'data' / 'raw'
target.mkdir(parents=True, exist_ok=True)
records = []
for p in sorted(source.rglob('*')):
    if not p.is_file(): continue
    rel = p.relative_to(source)
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    q = target / rel
    q.parent.mkdir(parents=True, exist_ok=True)
    if q.exists():
        assert hashlib.sha256(q.read_bytes()).hexdigest() == digest, str(rel)
    else: shutil.copy2(p, q)
    assert hashlib.sha256(q.read_bytes()).hexdigest() == digest
    records.append(dict(path=rel.as_posix(), bytes=p.stat().st_size, sha256=digest,
                        modified_ns=p.stat().st_mtime_ns))
(root / 'data' / 'inventory.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(records), bytes=sum(r['bytes'] for r in records), snapshot_verified=True)))
