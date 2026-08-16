from hayes_verify.onboarding_bundle import build_bundle


def test_bundle_hashes_sources_and_never_attests_compliance(tmp_path):
 source=tmp_path/"summary.json";source.write_text("{}")
 plan={"assessment_plan_id":"PLAN-abcdef0123456789","plan_sha256":"a"*64}
 manifest,cert=build_bundle("RUN-test","REPO-9004",plan,[{"source":str(source),"path":"assessment_summary.json","artifact_type":"ASSESSMENT","authority_class":"IMMUTABLE_DERIVED_EVIDENCE"}],tmp_path/"runs")
 assert manifest["integrity_state"]=="COMPLETE" and cert["compliance_attestation"] is False
 assert (tmp_path/"runs"/"RUN-test"/"auditor_report.md").exists()
