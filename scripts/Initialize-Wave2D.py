import argparse,json,subprocess
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

def run(*args):
    cp=subprocess.run(args,cwd=root,capture_output=True,text=True)
    if cp.returncode!=0:
        raise SystemExit(cp.stderr.strip() or cp.stdout.strip() or f"Command failed: {args}")
    return cp.stdout.strip()

branch=run("git","branch","--show-current")
if branch!=spec["branch"]:
    raise SystemExit(f"Initialization blocked: expected branch {spec['branch']}, current={branch}")

reg=json.loads((root/spec["baseline_registration"]).read_text(encoding="utf-8"))
tag_sha=run("git","rev-list","-n","1",spec["baseline_tag"])

wave2d_registry=root/"registry"/"wave2d"
wave2d_generated=root/"generated"/"wave2d"
wave2d_registry.mkdir(parents=True,exist_ok=True)
wave2d_generated.mkdir(parents=True,exist_ok=True)

scope={
    "wave":"2D",
    "baseline_tag":spec["baseline_tag"],
    "baseline_commit_sha":tag_sha,
    "scope_count":0,
    "controls":[],
    "population_policy":"NO_IMPLICIT_CARRY_FORWARD",
    "status":"PASS"
}
(wave2d_registry/"scope.json").write_text(json.dumps(scope,indent=2),encoding="utf-8")

population={
    "wave":"2D",
    "population_count":0,
    "items":[],
    "source_wave":"2C",
    "carry_forward_performed":False,
    "status":"PASS"
}
(wave2d_registry/"population.json").write_text(json.dumps(population,indent=2),encoding="utf-8")

record={
    "wave":"2D",
    "initialized_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS",
    "branch":branch,
    "baseline_tag":spec["baseline_tag"],
    "baseline_commit_sha":tag_sha,
    "baseline_state":reg["baseline_state"],
    "scope_count":0,
    "population_count":0,
    "carry_forward_performed":False,
    "wave2c_mutation_detected":False,
    "initialization_state":"INITIALIZED"
}
Path(a.out).parent.mkdir(parents=True,exist_ok=True)
Path(a.out).write_text(json.dumps(record,indent=2),encoding="utf-8")
print(json.dumps(record,indent=2))
