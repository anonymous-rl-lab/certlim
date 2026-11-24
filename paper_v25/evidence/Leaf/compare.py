"""Compute all-schedule denominators and the sensitivity to a zero abstention band."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd

def main():
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);out=p.parse_args().out
    t=pd.read_csv(out/'traces.csv',dtype={'cell':str})
    b=pd.read_csv(out/'paired.csv',dtype={'cell':str})
    full=t.merge(b[['cell','visit','previous']],on=['cell','visit'],how='left',validate='one_to_one')
    full['previous']=full.previous.fillna('REFER')
    def actions(d,act):
        return {g:{'n':len(x),'wrong':int(x[act].eq('FAIL' if g=='qualified' else 'PASS').sum()),
                    'decisive':int(x[act].ne('REFER').sum())} for g,x in d.groupby('grade')}
    def no_band(d,col):
        d=d.copy();d['at_spec']=np.where(d[col]>=22.75,'PASS','FAIL')
        return actions(d,'at_spec')
    result=dict(primary_all_scheduled=actions(full,'previous'),posthoc_no_band_previous=no_band(b,'prior_Ah'),
                posthoc_no_band_same_visit_all=no_band(t,'charge_Ah'),
                charge_discharge_abs_difference_quantiles_Ah=(t.charge_Ah-t.reference_Ah).abs().quantile([0,.5,.95,1]).to_dict(),
                same_visit_all_potential_h=float(t.loc[t.same_visit.ne('REFER'),'reference_h'].sum()),
                same_visit_first_of_each_unit=actions(t[t.visit==1],'same_visit'))
    (out/'schedule_and_controls.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
