from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

def main():
    z=pd.read_csv(OUT/'corrected_frontier.csv')
    main=pd.read_csv(OUT/'physical_summary.csv')
    refin=pd.read_csv(OUT/'ordered_summary.csv')
    v=pd.concat([main,refin]).query('scope=="missing_only" and validation=="locked_14" and n==4')
    fig,axs=plt.subplots(1,2,figsize=(10.6,4.3),layout='constrained')
    ax=axs[0]
    ax.fill_between(z.n,z.four_D_lower,z.four_D_upper,color='#e6a34a',alpha=.5,label='Four symbols: proved bounds')
    ax.plot(z.n,z.cutoff_D,'o-',color='#126a75',markersize=4,label='Cutoff count: exact')
    ax.axhline(.1,color='0.5',linestyle=':',linewidth=1)
    ax.set(xlabel='Independent draws from a fixed law',ylabel='Worst-case decisive probability',title='A   Corrected registered experiment',ylim=(0,.82))
    ax.yaxis.set_major_formatter(PercentFormatter(1,0));ax.legend(loc='upper left',fontsize=8,frameon=False)
    ax=axs[1]; names=['cutoff_count','load_and_cutoff','plain_tiebreak','ordered_tiebreak']; labs=['Count','Current + count','Tie-break','Order + tie-break']
    ys=np.arange(len(names))
    for gr,color,off,label in [('S','#126a75',-.15,'Safe'),('U','#b36819',.15,'Unsafe')]:
        vals=v[v.grade==gr].set_index('method').loc[names,'cell_equal_decisive']
        ax.barh(ys+off,vals,.27,color=color,label=label)
    ax.set(yticks=ys,yticklabels=labs,xlabel='Cell-balanced decisive probability',title='B   Four real measurements per block',xlim=(0,.73));ax.invert_yaxis()
    ax.xaxis.set_major_formatter(PercentFormatter(1,0));ax.legend(frameon=False,fontsize=8)
    for ax in axs:
        ax.spines[['right','top']].set_visible(False)
    fig.savefig(ROOT/'NASA_frontier_and_replay.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
if __name__=='__main__':main()
