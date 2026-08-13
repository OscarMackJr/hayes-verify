import argparse,csv,json,sys
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--requirements',required=True);ap.add_argument('--collectors',required=True);ap.add_argument('--report',required=True);a=ap.parse_args();req=list(csv.DictReader(Path(a.requirements).open(encoding='utf-8-sig')));cols=list(csv.DictReader(Path(a.collectors).open(encoding='utf-8-sig')));errors=[];ids=[r['control_id'] for r in req]
 if len(ids)!=29:errors.append(f'Expected 29 evidence-gap controls, found {len(ids)}.')
 if len(ids)!=len(set(ids)):errors.append('Duplicate control IDs in requirements registry.')
 valid={c['collector_id'] for c in cols}
 for r in req:
  if r['collector_id'] not in valid:errors.append(f"{r['control_id']}: collector not registered")
  if r['required_evidence_class']!='OPERATING_EVIDENCE':errors.append(f"{r['control_id']}: invalid evidence class")
  if r['promotion_mode']!='FAIL_CLOSED':errors.append(f"{r['control_id']}: promotion must be FAIL_CLOSED")
 result={'status':'PASS' if not errors else 'FAIL','requirement_count':len(req),'collector_count':len(cols),'errors':errors,'promotion_performed':False};Path(a.report).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));sys.exit(1 if errors else 0)
if __name__=='__main__':main()
