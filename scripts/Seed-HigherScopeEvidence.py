import argparse,yaml
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scope-registry",required=True)
    ap.add_argument("--authority-registry",required=True)
    ap.add_argument("--out-root",required=True)
    a=ap.parse_args()

    reg=yaml.safe_load(Path(a.scope_registry).read_text(encoding="utf-8"))
    auth=yaml.safe_load(Path(a.authority_registry).read_text(encoding="utf-8"))
    root=Path(a.out_root)

    count=0
    for c in reg["controls"]:
        scope=c["scope"]
        if scope not in {"EMS","ORGANIZATION"}:
            continue

        folder=root/("ems" if scope=="EMS" else "organization")
        folder.mkdir(parents=True,exist_ok=True)
        p=folder/f"{c['control_id']}.yaml"

        if p.exists():
            continue

        authority=auth["authorities"][scope]["authority_id"]
        payload={
            "evidence_id":f"{scope}-{c['control_id']}-PENDING",
            "control_id":c["control_id"],
            "scope":scope,
            "authority_id":authority,
            "status":"NOT_EVALUATED",
            "evidence_date":"2026-08-12",
            "expires_on":None,
            "evidence_summary":"Higher-scope evidence has not yet been supplied.",
            "evidence_references":[],
            "notes":"Seeded by Wave 2B.1. Replace with controlled evidence before inheritance can resolve."
        }
        p.write_text(yaml.safe_dump(payload,sort_keys=False),encoding="utf-8")
        count+=1

    print(f"Seeded {count} higher-scope evidence record(s).")

if __name__=="__main__":main()
