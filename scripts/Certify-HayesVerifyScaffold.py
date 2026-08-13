import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def run(cmd):
    cp=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
    return cp.returncode,cp.stdout,cp.stderr

errors=[]

# Contract bundle validation
rc,out,err=run([sys.executable,"scripts/validate_contract_bundle.py","--root","."])
contract_status="PASS" if rc==0 else "FAIL"
contract_count=None
try:
    contract_count=json.loads(out).get("contract_count")
except Exception:
    pass
if rc!=0:
    errors.append("contract bundle validation failed")

# Pytest
rc_p,pyout,pyerr=run([sys.executable,"-m","pytest","-q"])
pytest_status="PASS" if rc_p==0 else "FAIL"
if rc_p!=0:
    errors.append("pytest failed")

# Count passed tests from output conservatively.
test_count=0
import re
m=re.search(r"(\d+)\s+passed",pyout)
if m:
    test_count=int(m.group(1))
if test_count < spec["expected_test_count"]:
    errors.append(f"test_count={test_count}, expected>={spec['expected_test_count']}")

# Ruff
rc_r,rout,rerr=run([sys.executable,"-m","ruff","check","src","tests"])
ruff_status="PASS" if rc_r==0 else "FAIL"
if rc_r!=0:
    errors.append("ruff failed")

# Bootstrap evaluator invariant
code = """
import json
from pathlib import Path
from hayes_verify.contracts import ContractBundle
from hayes_verify.orchestration import run_evaluation
import tempfile

bundle=ContractBundle.discover()
req=json.loads((Path('examples')/'evaluation_request.json').read_text())
with tempfile.TemporaryDirectory(dir='.pytest-temp') as d:
    req['repository_name']=d
    result=run_evaluation(bundle,req)
    print(result['promotion_state'])
"""
rc_b,bout,berr=run([sys.executable,"-c",code])
promotion_state=bout.strip() if rc_b==0 else "ERROR"
if promotion_state!=spec["required_promotion_state"]:
    errors.append(f"bootstrap promotion_state={promotion_state}")

files=[]
for rel in spec["files_to_hash"]:
    p=root/rel
    if not p.exists():
        errors.append(f"missing file: {rel}")
        continue
    files.append({"path":rel,"sha256":sha256(p)})

record={
    "component":"Hayes Verify",
    "phase":"Windows Test Determinism & Scaffold Certification",
    "certified_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if not errors else "FAIL",
    "contract_validation_status":contract_status,
    "pytest_status":pytest_status,
    "ruff_status":ruff_status,
    "test_count":test_count,
    "contract_count":contract_count,
    "bootstrap_promotion_state":promotion_state,
    "pytest_basetemp":spec["pytest_basetemp"],
    "errors":errors,
    "files":files
}
outp=root/spec["certification_output"]
outp.parent.mkdir(parents=True,exist_ok=True)
outp.write_text(json.dumps(record,indent=2),encoding="utf-8")
print(json.dumps(record,indent=2))
raise SystemExit(0 if not errors else 1)
