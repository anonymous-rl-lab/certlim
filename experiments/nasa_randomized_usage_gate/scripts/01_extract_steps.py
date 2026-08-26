import scipy.io as sio, numpy as np, pandas as pd, os, sys, glob
ARMS={
 'Battery_Uniform_Distribution_Charge_Discharge_DataSet_2Post':('uniform_cd','room'),
 'Battery_Uniform_Distribution_Discharge_Room_Temp_DataSet_2Post':('uniform_d','room'),
 'Battery_Uniform_Distribution_Variable_Charge_Room_Temp_DataSet_2Post':('uniform_vc','room'),
 'RW_Skewed_High_Room_Temp_DataSet_2Post':('skew_high','room'),
 'RW_Skewed_High_40C_DataSet_2Post':('skew_high','40C'),
 'RW_Skewed_Low_Room_Temp_DataSet_2Post':('skew_low','room'),
 'RW_Skewed_Low_40C_DataSet_2Post':('skew_low','40C'),
}
rows=[]
for folder,(arm,temp) in ARMS.items():
    for f in sorted(glob.glob(f'{folder}/data/Matlab/*.mat')):
        cell=os.path.basename(f)[:-4]
        steps=sio.loadmat(f,simplify_cells=True)['data']['step']
        stage=0; last_ref=-99; k=0
        for i,s in enumerate(steps):
            c=str(s['comment'])
            if 'reference discharge' in c and i-last_ref>3:
                stage+=1; last_ref=i
            if s['type']!='D' or 'random walk' not in c: continue
            V=np.asarray(s['voltage']).ravel(); I=np.abs(np.asarray(s['current']).ravel())
            T=np.asarray(s['temperature']).ravel(); rt=np.asarray(s['relativeTime']).ravel()
            if V.size<3 or I.size<3: continue
            rows.append((cell,arm,temp,stage,k,float(np.median(I)),float(V[0]),float(V[-1]),
                         float(V.min()),float(T.max()),float(T[0]),float(rt[-1]),
                         float(np.trapezoid(I,rt)/3600)))
            k+=1
df=pd.DataFrame(rows,columns=['cell','arm','temp','stage','step_k','I_med','V0','Vend','Vmin',
                              'Tmax','T0','dur_s','Ah'])
df.to_parquet(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','steps.parquet')); print(len(df),'steps,',df.cell.nunique(),'cells')
print(df.groupby(['arm','temp']).agg(cells=('cell','nunique'),steps=('cell','size')).to_string())
