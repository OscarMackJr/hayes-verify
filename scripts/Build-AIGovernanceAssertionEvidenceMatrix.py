import argparse,csv,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--classification",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    with Path(a.classification).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    grouped={}
    for r in rows:
        key=(r["control_id"],r["control_name"],r["scope"],r["assertion"])
        grouped.setdefault(key,[]).append(r)

    out=[]
    for key,items in grouped.items():
        operating=[x for x in items if x["source_class"]=="OPERATING_EVIDENCE"]
        rejected=[x for x in items if x["source_class"]!="OPERATING_EVIDENCE"]
        out.append({
            "control_id":key[0],
            "control_name":key[1],
            "scope":key[2],
            "assertion":key[3],
            "source_count":len(items),
            "operating_evidence_count":len(operating),
            "rejected_source_count":len(rejected),
            "operating_evidence_sufficient":len(operating)>=1,
            "operating_sources":";".join(x["source_path"] for x in operating),
            "rejected_sources":";".join(x["source_path"] for x in rejected)
        })

    fields=list(out[0].keys()) if out else []
    with Path(a.out).open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(out)

    print(json.dumps({
        "assertion_count":len(out),
        "assertions_with_operating_evidence":sum(str(x["operating_evidence_sufficient"]).lower()=="true" for x in out),
        "assertions_without_operating_evidence":sum(str(x["operating_evidence_sufficient"]).lower()!="true" for x in out)
    },indent=2))

if __name__=="__main__":main()
