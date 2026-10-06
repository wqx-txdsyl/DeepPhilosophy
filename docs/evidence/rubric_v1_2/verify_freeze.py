"""Read-only integrity check. Integrity is not evaluator validity."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
root = base.parents[2]
manifest = json.loads((base / "FREEZE_MANIFEST.json").read_text())
failures = []
for relative, expected in manifest["files"].items():
    path = root / relative
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        failures.append(relative)
print(json.dumps({"integrity_ok": not failures, "files_checked": len(manifest["files"]), "failures": failures,
                  "freeze_scope": manifest["scope"], "automated_evaluator_accepted": manifest["automated_evaluator_accepted"]}, ensure_ascii=False, indent=2))
raise SystemExit(bool(failures))
