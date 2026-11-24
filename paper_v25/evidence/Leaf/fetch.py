"""Fetch the authors' unmodified OSF C/20 workbook archive."""
import argparse
import hashlib
import shutil
import urllib.request
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('target',type=Path);a=p.parse_args()
expected='a4952be5b9d960c57b208a523b90ef9923f65ee92767b46b6b1b88560a62c98c'
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
if a.target.exists():
    if digest(a.target)!=expected:raise ValueError('Existing file has unexpected hash')
else:
    a.target.parent.mkdir(parents=True,exist_ok=True)
    temp=a.target.with_suffix('.partial')
    with urllib.request.urlopen('https://osf.io/download/jr8gs/',timeout=180) as r,temp.open('wb') as out:
        shutil.copyfileobj(r,out)
    if digest(temp)!=expected:raise ValueError('Download checksum mismatch')
    temp.replace(a.target)
print(expected,a.target)
