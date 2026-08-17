"""RP1B safe ZIP intake; archive contents are never executed."""
from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .archive_assessment import ArchiveWorkflowError, sha256_file

MAX_ENTRIES=10000; MAX_EXPANDED_BYTES=256*1024*1024; MAX_SINGLE_FILE_BYTES=64*1024*1024; MAX_RATIO=100; MAX_PATH_LENGTH=240

def _now(): return datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def _sha_json(v:Any): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def safe_intake(archive:Path, extraction_root:Path, *, workflow_id:str, archive_target_id:str, source_zip_sha256:str)->dict[str,Any]:
    if not zipfile.is_zipfile(archive): raise ArchiveWorkflowError('corrupt or unsupported ZIP')
    seen=set(); files=[]; directory_count=0; total=0
    with zipfile.ZipFile(archive) as z:
      infos=z.infolist()
      if len(infos)>MAX_ENTRIES: raise ArchiveWorkflowError('ZIP entry count exceeds operational safety limit')
      for info in infos:
        name=info.filename.replace('\\','/')
        parts=Path(name).parts
        if not name or name.startswith(('/', '\\')) or '..' in parts or ':' in name or len(name)>MAX_PATH_LENGTH: raise ArchiveWorkflowError('unsafe ZIP path')
        key=name.casefold()
        if key in seen: raise ArchiveWorkflowError('duplicate ZIP path')
        seen.add(key)
        mode=info.external_attr>>16
        if stat.S_ISLNK(mode): raise ArchiveWorkflowError('ZIP symlink entries are not permitted')
        if info.is_dir(): directory_count+=1; continue
        if info.file_size>MAX_SINGLE_FILE_BYTES: raise ArchiveWorkflowError('ZIP entry exceeds single-file safety limit')
        total+=info.file_size
        if total>MAX_EXPANDED_BYTES: raise ArchiveWorkflowError('ZIP expanded size exceeds operational safety limit')
        if info.compress_size and info.file_size/info.compress_size>MAX_RATIO: raise ArchiveWorkflowError('ZIP compression ratio exceeds operational safety limit')
      extraction_root.mkdir(parents=True,exist_ok=False)
      for info in infos:
        if info.is_dir(): continue
        target=(extraction_root/info.filename).resolve()
        try: target.relative_to(extraction_root.resolve())
        except ValueError as exc: raise ArchiveWorkflowError('ZIP extraction escapes root') from exc
        target.parent.mkdir(parents=True,exist_ok=True)
        with z.open(info) as src,target.open('wb') as dst: dst.write(src.read())
        files.append({'path':info.filename.replace('\\','/'),'sha256':sha256_file(target),'size':target.stat().st_size})
    content={'version':'1.0','file_count':len(files),'files':sorted(files,key=lambda x:x['path'])}
    content_sha=_sha_json(content)
    manifest={'manifest_version':'1.0','workflow_id':workflow_id,'archive_target_id':archive_target_id,'source_zip_sha256':source_zip_sha256,'source_archive_size':archive.stat().st_size,'entry_count':len(infos),'file_count':len(files),'directory_count':directory_count,'embedded_git_detected':any(x['path'].startswith('.git/') for x in files),'extraction_integrity_state':'PASS','extracted_content_manifest_sha256':content_sha,'created_at':_now()}
    return {'source_manifest':manifest,'content_manifest':content}
