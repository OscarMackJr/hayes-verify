import argparse,csv,json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
a=p.parse_args()
root=Path(a.root)
reg=root/"registers"/"wave2c"/"ems-review"
reg.mkdir(parents=True,exist_ok=True)
path=reg/"annual_ems_review_register.csv"
headers=[
 "review_id","review_date","participants","findings_or_observations",
 "decisions","actions_and_owners","review_status","evidence_reference"
]
if not path.exists():
    with path.open("w",newline="",encoding="utf-8") as f:
        csv.writer(f).writerow(headers)
print(json.dumps({"status":"PASS","register":str(path),"promotion_performed":False},indent=2))
