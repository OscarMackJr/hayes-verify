import argparse,json,hashlib,subprocess
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

def run(*args):
    cp=subprocess.run(args,cwd=root,capture_output=True,text=True)
    if cp.returncode!=0:
        raise SystemExit(cp.stderr.strip() or cp.stdout.strip() or f"Command failed: {args}")
    return cp.stdout.strip()

branch=run("git","branch","--show-current")
if branch!="main":
    raise SystemExit(f"Baseline verification blocked: expected main, current={branch}")

head=run("git","rev-parse","HEAD")
origin=run("git","rev-parse","origin/main")
if head!=origin:
    raise SystemExit(f"Baseline verification blocked: HEAD {head} != origin/main {origin}")

reg_path=root/spec["baseline_registration"]
if not reg_path.exists():
    raise SystemExit(f"Baseline verification blocked: missing {reg_path}")

reg=json.loads(reg_path.read_text(encoding="utf-8"))
if reg.get("wave")!="2C":
    raise SystemExit("Baseline verification blocked: registration wave is not 2C.")
if reg.get("release_tag")!=spec["baseline_tag"]:
    raise SystemExit("Baseline verification blocked: release tag mismatch.")
if reg.get("baseline_state")!=spec["baseline_state_required"]:
    raise SystemExit("Baseline verification blocked: baseline not AUTHORITATIVE.")
if reg.get("control_results_changed") is not False:
    raise SystemExit("Baseline verification blocked: control_results_changed must be false.")

tag_sha=run("git","rev-list","-n","1",spec["baseline_tag"])
if tag_sha!=reg.get("tag_commit_sha"):
    raise SystemExit(f"Baseline verification blocked: tag SHA {tag_sha} != registered tag SHA {reg.get('tag_commit_sha')}")

result={
    "status":"PASS",
    "baseline_tag":spec["baseline_tag"],
    "baseline_commit_sha":tag_sha,
    "registration_main_commit_sha":reg.get("main_commit_sha"),
    "baseline_state":reg.get("baseline_state"),
    "next_wave":reg.get("next_wave"),
    "control_results_changed":False
}
print(json.dumps(result,indent=2))
