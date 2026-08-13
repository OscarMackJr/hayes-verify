import argparse,csv,json
from pathlib import Path

MAP={
"EMS-CTRL-063":{
    "file":"data_classification_register.json",
    "assertions":["data_owner_or_steward_recorded"],
    "qualifies":lambda r: bool(r.get("data_owner_or_steward")) and bool(r.get("classification_level")) and bool(r.get("system_or_dataset")) and bool(r.get("review_date"))
},
"EMS-CTRL-065":{
    "file":"data_retention_register.json",
    "assertions":["retention_period_recorded","data_scope_or_category_recorded"],
    "qualifies":lambda r: bool(r.get("retention_period")) and bool(r.get("data_scope_or_category")) and bool(r.get("owner_or_authority")) and bool(r.get("disposition_action")) and bool(r.get("execution_date"))
},
"EMS-CTRL-066":{
    "file":"production_data_protection_register.json",
    "assertions":["protection_control_or_handling_recorded"],
    "qualifies":lambda r: bool(r.get("protection_control")) and bool(r.get("data_scope")) and bool(r.get("owner_or_responsible_party")) and bool(r.get("validation_date")) and bool(r.get("validation_result"))
}
}

ap=argparse.ArgumentParser()
ap.add_argument("--register-dir",required=True)
ap.add_argument("--outdir",required=True)
a=ap.parse_args()

out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
rows=[]
for cid,cfg in MAP.items():
    path=Path(a.register_dir)/cfg["file"]
    obj=json.loads(path.read_text(encoding="utf-8"))
    records=obj.get("records",[])
    qualifying=[r for r in records if cfg["qualifies"](r)]
    if not records:
        reason="EMPTY_REGISTER"
    elif not qualifying:
        reason="NO_QUALIFYING_OPERATING_RECORD"
    else:
        reason="QUALIFYING_OPERATING_RECORD_PRESENT"
    for assertion in cfg["assertions"]:
        rows.append({
            "control_id":cid,
            "assertion":assertion,
            "record_count":len(records),
            "qualifying_record_count":len(qualifying),
            "operating_evidence_sufficient":bool(qualifying),
            "operating_source":str(path) if qualifying else "",
            "reason":reason
        })

with (out/"register_assertion_evidence.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print(json.dumps({
    "row_count":len(rows),
    "sufficient_assertion_count":sum(bool(x["operating_evidence_sufficient"]) for x in rows),
    "empty_register_assertion_count":sum(x["reason"]=="EMPTY_REGISTER" for x in rows)
},indent=2))
