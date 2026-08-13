import argparse,csv,json
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--collectors',required=True);ap.add_argument('--outdir',required=True);a=ap.parse_args();rows=list(csv.DictReader(Path(a.collectors).open(encoding='utf-8-sig')));out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
 for r in rows:
  text=f'''# {r["collector_id"]}\n# Wave 2B.2 disabled collector scaffold.\n# Controls: {r["control_ids"]}\n# MUST emit direct operating evidence only; never infer PASS from catalogs, policy, scope, or prior compliance.\n[CmdletBinding()]\nparam([string]$EMSPath="C:\\temp\\standars\\ems")\n$ErrorActionPreference="Stop"\nthrow "{r['collector_id']} is scaffolded but not implemented. Implement source-specific operating evidence collection before enabling."\n'''
  (out/f"Collect-{r['collector_id']}.ps1").write_text(text)
 print(json.dumps({'scaffold_count':len(rows),'enabled_count':0,'outdir':str(out)},indent=2))
if __name__=='__main__':main()
