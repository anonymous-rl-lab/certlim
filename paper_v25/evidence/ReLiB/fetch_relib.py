"""Fetch and check the unmodified 15.5 Ah public archive."""
from pathlib import Path
import argparse, hashlib, shutil, subprocess
from urllib.request import Request, urlopen
def checksum(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path); directory=ap.parse_args().directory
    directory.mkdir(exist_ok=True,parents=True); z=directory/'15.5Ah.tar.zst'; tar=directory/'15.5Ah.tar'
    url='https://www.kaggle.com/api/v1/datasets/download/liuyunlong0621/relib-100k/15.5Ah.tar.zst'
    if not z.exists():
        tmp=z.with_suffix('.part')
        with urlopen(Request(url,headers={'User-Agent':'CETL public replication/1.0'}),timeout=120) as r,tmp.open('wb') as f:
            shutil.copyfileobj(r,f,1<<20)
        if checksum(tmp)!='ff9a4e5bfc096fb517504aeb594069d900d600eb2e86667fcedd819ad4a0e6b1':
            raise ValueError('Public archive checksum mismatch')
        tmp.replace(z)
    if checksum(z)!='ff9a4e5bfc096fb517504aeb594069d900d600eb2e86667fcedd819ad4a0e6b1': raise ValueError('Bad download')
    if not tar.exists():
        tmp=tar.with_suffix('.tar.partial')
        with tmp.open('wb') as f:subprocess.run(['zstd','-q','-d','-c',str(z)],stdout=f,check=True)
        if checksum(tmp)!='e8d868b26a3b205a7a8446fac2642bf1e88ab51e31d2a1c46452bc653f1d961d': raise ValueError('Bad TAR')
        tmp.replace(tar)
    if checksum(tar)!='e8d868b26a3b205a7a8446fac2642bf1e88ab51e31d2a1c46452bc653f1d961d': raise ValueError('Bad TAR')
    print(tar)
if __name__=='__main__': main()
