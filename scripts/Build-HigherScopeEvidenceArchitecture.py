import argparse,csv,json
from pathlib import Path
import yaml
FAMILIES=json.loads(Path(__file__).resolve().parents[1].joinpath('registry','higher_scope_collector_families.json').read_text())['families']
def cname(c): return c.get('control_name') or c.get('name') or c.get('title') or c.get('control_id','')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--scope-registry',required=True);ap.add_argument('--catalog',required=True);ap.add_argument('--gaps',required=True);ap.add_argument('--outdir',required=True);a=ap.parse_args()
 scope=yaml.safe_load(Path(a.scope_registry).read_text()) or {};cat=yaml.safe_load(Path(a.catalog).read_text()) or {}
 cats={c['control_id']:c for c in cat.get('controls',[])};scopes={c['control_id']:c for c in scope.get('controls',[])}
 gaps=list(csv.DictReader(Path(a.gaps).open(encoding='utf-8-sig',newline='')));targets={r['control_id'] for r in gaps};fmap={cid:f for f in FAMILIES for cid in f['control_ids']};missing=sorted(targets-set(fmap))
 req=[]
 for cid in sorted(targets):
  c=cats.get(cid,{});s=scopes.get(cid,{});f=fmap.get(cid,{})
  req.append({'control_id':cid,'control_name':cname(c) or s.get('control_name',''),'scope':s.get('scope',''),'collector_id':f.get('collector_id','UNMAPPED'),'collector_family':f.get('family','UNMAPPED'),'required_evidence_class':'OPERATING_EVIDENCE','minimum_confidence':'0.90','required_sufficiency':'SUFFICIENT','promotion_mode':'FAIL_CLOSED','requirement':'Collect direct, attributable, retained operating evidence demonstrating execution or enforcement of '+(cname(c) or cid)+'.'})
 out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
 with (out/'higher_scope_evidence_requirements.csv').open('w',newline='',encoding='utf-8') as fh:w=csv.DictWriter(fh,fieldnames=list(req[0]));w.writeheader();w.writerows(req)
 collectors=[]
 for f in FAMILIES:
  active=[x for x in f['control_ids'] if x in targets]
  if active:collectors.append({'collector_id':f['collector_id'],'collector_family':f['family'],'control_count':len(active),'control_ids':';'.join(active),'output_contract':'evidence_envelopes.jsonl','source_class':'OPERATING_EVIDENCE','automatic_promotion':False,'implementation_status':'SCAFFOLDED'})
 with (out/'higher_scope_collector_registry.csv').open('w',newline='',encoding='utf-8') as fh:w=csv.DictWriter(fh,fieldnames=list(collectors[0]));w.writeheader();w.writerows(collectors)
 summary={'target_control_count':len(targets),'mapped_control_count':len(targets)-len(missing),'collector_family_count':len(collectors),'missing_controls':missing,'status':'PASS' if not missing else 'FAIL','promotion_performed':False};(out/'architecture_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));raise SystemExit(1 if missing else 0)
if __name__=='__main__':main()
