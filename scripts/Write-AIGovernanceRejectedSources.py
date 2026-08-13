import argparse,csv
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--classification",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    with Path(a.classification).open(encoding="utf-8-sig",newline="") as fh:
        rows=[r for r in csv.DictReader(fh) if r["source_class"]!="OPERATING_EVIDENCE"]

    fields=["control_id","control_name","scope","assertion","source_path","source_class","classification_reason"]
    with Path(a.out).open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(rows)

    print(f"Rejected source rows: {len(rows)}")

if __name__=="__main__":main()
