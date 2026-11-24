"""Download the authors' pinned multipart ZIP for academic use and verify every Git blob."""
from pathlib import Path
import concurrent.futures, urllib.request, zipfile, hashlib, json, shutil,sys
ROOT=Path(__file__).resolve().parent
SHA='253c46560892c6ba39979246dcb4dea9666d1860'
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'cache'
OUT.mkdir(parents=True,exist_ok=True)
repo='CETL-HFUT/Imbalanced-retired-battery-data'
def get(url):
    import time
    for i in range(3):
        try:
            with urllib.request.urlopen(url,timeout=110) as resp: return resp.read()
        except Exception:
            if i==2: raise
            time.sleep(1)
tree=json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{SHA}'))['tree']
def part(f):
    path=OUT/f['path']
    b=path.read_bytes() if path.exists() else get(f'https://raw.githubusercontent.com/{repo}/{SHA}/'+f['path'])
    assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==f['sha'],path
    path.write_bytes(b)
    return path
files=sorted([f for f in tree if '.zip.' in f['path']],key=lambda x:x['path'])
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as e:parts=list(e.map(part,files))
with (OUT/'all.zip').open('wb') as out:
    for p in parts:
        with p.open('rb') as inp:shutil.copyfileobj(inp,out)
with zipfile.ZipFile(OUT/'all.zip') as z:
    for n in z.namelist():
        if n.lower().endswith('.mat'):
            with z.open(n) as inp,(OUT/Path(n).name).open('wb') as out:shutil.copyfileobj(inp,out)
            print(Path(n).name,(OUT/Path(n).name).stat().st_size)
