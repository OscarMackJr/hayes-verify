import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--root",required=True);a=p.parse_args();r=Path(a.root)
reg=r/"registers"/"wave2c"/"ai-governance";out=r/"generated"/"wave2c"/"ai-governance";reg.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
defs={"approved_ai_platforms.csv":["platform_name","business_use","owner","approval_authority","approval_status","approved_at","unapproved_handling","evidence_reference"],"prompt_data_classification.csv":["record_id","platform_name","use_case","data_classification","sensitive_data_handling","owner","reviewed_at","evidence_reference"],"ai_security_reviews.csv":["review_id","platform_or_use_case","review_date","reviewer","finding_or_risk","severity","owner","disposition","evidence_reference"]}
for n,h in defs.items():
 f=reg/n
 if not f.exists():
  with f.open("w",newline="",encoding="utf-8") as x: csv.writer(x).writerow(h)
def load(n):
 with (reg/n).open(encoding="utf-8-sig",newline="") as x:return list(csv.DictReader(x))
P,D,S=load("approved_ai_platforms.csv"),load("prompt_data_classification.csv"),load("ai_security_reviews.csv")
R=[]
def add(c,n,pop,keys):
 q=sum(all(str(x.get(k,"")).strip() for k in keys) for x in pop);R.append({"control_id":c,"assertion":n,"record_count":len(pop),"qualifying_record_count":q,"operating_evidence_sufficient":q>0,"reason":"QUALIFYING_RECORD_PRESENT" if q else ("EMPTY_REGISTER" if not pop else "NO_QUALIFYING_RECORD")})
add("EMS-CTRL-049","approved_platform_inventory_recorded",P,["platform_name","approval_status"]);add("EMS-CTRL-049","approval_or_owner_recorded",P,["owner","approval_authority"]);add("EMS-CTRL-049","unapproved_platform_handling_recorded",P,["unapproved_handling"])
add("EMS-CTRL-050","prompt_data_classification_recorded",D,["use_case","data_classification"]);add("EMS-CTRL-050","sensitive_data_handling_recorded",D,["sensitive_data_handling"]);add("EMS-CTRL-050","accountable_owner_or_review_recorded",D,["owner","reviewed_at"])
add("EMS-CTRL-053","security_review_recorded",S,["review_id","review_date","reviewer"]);add("EMS-CTRL-053","finding_or_risk_recorded",S,["finding_or_risk"]);add("EMS-CTRL-053","owner_and_disposition_recorded",S,["owner","disposition"])
(out/"assertion_evidence.json").write_text(json.dumps({"wave":"2C.2","assertions":R,"promotion_performed":False},indent=2))
print(json.dumps({"assertion_count":len(R),"sufficient_assertion_count":sum(x["operating_evidence_sufficient"] for x in R),"promotion_performed":False},indent=2))