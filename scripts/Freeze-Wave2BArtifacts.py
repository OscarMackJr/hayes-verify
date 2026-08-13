import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
from datetime import datetime,timezone

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ems-root",required=True)
    ap.add_argument("--certdir",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()

    root=Path(a.ems_root).resolve()
    cert=Path(a.certdir).resolve()
    out=Path(a.outdir).resolve()
    out.mkdir(parents=True,exist_ok=True)

    include=[
        root/"registry",
        root/"schemas",
        root/"evidence",
        root/"registers",
        root/"generated"/"wave2",
        cert
    ]

    stage=out/"wave2b-baseline"
    if stage.exists(): shutil.rmtree(stage)
    stage.mkdir(parents=True)

    copied=[]
    for src in include:
        if not src.exists(): continue
        rel=src.relative_to(root) if root in src.parents or src==root else Path("certification")
        dest=stage/rel
        if src.is_dir():
            shutil.copytree(src,dest,dirs_exist_ok=True)
            for p in dest.rglob("*"):
                if p.is_file(): copied.append(p)
        else:
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dest);copied.append(dest)

    manifest=[]
    for p in sorted(set(copied)):
        manifest.append({
            "path":str(p.relative_to(stage)).replace("\\","/"),
            "bytes":p.stat().st_size,
            "sha256":sha256(p)
        })

    m={
        "wave":"2B",
        "frozen_at":datetime.now(timezone.utc).isoformat(),
        "file_count":len(manifest),
        "files":manifest
    }
    (stage/"wave2b_freeze_manifest.json").write_text(json.dumps(m,indent=2),encoding="utf-8")

    zip_path=out/"EMS_Wave2B_BranchReady_Closeout.zip"
    if zip_path.exists(): zip_path.unlink()
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        for p in stage.rglob("*"):
            if p.is_file(): z.write(p,p.relative_to(stage))

    summary={
        "status":"PASS",
        "stage":str(stage),
        "file_count":len(manifest)+1,
        "zip":str(zip_path),
        "zip_sha256":sha256(zip_path)
    }
    (out/"freeze_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
