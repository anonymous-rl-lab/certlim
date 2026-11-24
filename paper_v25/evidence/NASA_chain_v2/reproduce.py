"""Rerun the retained-data experiment from the packaged step table."""
from pathlib import Path
import os,sys,subprocess
root=Path(__file__).resolve().parent
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NASA_RESULTS='results')
def run(name,*args,fixed=False):
    print(name,*args, '[60 s]' if fixed else '',flush=True)
    subprocess.run([sys.executable,str(root/'src'/(name+'.py')),*args],cwd=root,check=True,
                   env=dict(env,NASA_RESULTS='results/fixed60' if fixed else 'results'))
if __name__=='__main__':
    run('run_legacy');run('extend');run('physical');run('confidence');run('confidence_frontier');run('thermal')
    run('cell_registration');run('ordered');run('diagnostics')
    run('physical','--endpoint','fixed60',fixed=True);run('cell_registration',fixed=True)
    run('ordered',fixed=True);run('diagnostics',fixed=True);run('figures');run('check')
