"""Generate shareable figures from measured results; never retrain models."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=Path(__file__).resolve().parents[1]
r=json.loads((root/'reports/results.json').read_text())
rows=[x for x in r['results'] if x['algorithm']=='logistic']
colors=['#8293ab','#225de5','#149083','#293b58']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#34465f','text.color':'#182940'})
fig,(ax,roc)=plt.subplots(1,2,figsize=(12,4.8),gridspec_kw={'width_ratios':[1.35,1]})
for i,(row,c) in enumerate(zip(rows,colors)):
 a=row['test']['auc'];lo,hi=row['auc_ci'];ax.errorbar(a,3-i,xerr=np.array([[a-lo],[hi-a]]),fmt='o',color=c,capsize=4,markersize=8)
 roc.plot(row['roc']['fpr'],row['roc']['tpr'],label=row['label'].replace('Demographics','Demo.'),color=c,lw=2)
ax.set_yticks(range(4),[x['label'].replace('Demographics','Demo.') for x in rows][::-1]);ax.set_xlim(0,1);ax.set_ylim(-.6,3.6);ax.set_xlabel('Test ROC-AUC (0–1)');ax.set_title('Logistic models: held-out discrimination',loc='left',fontsize=13);ax.axvline(.5,color='#ccd4df',ls='--');ax.grid(axis='x',alpha=.2)
roc.plot([0,1],[0,1],ls='--',color='#ccd4df');roc.set(xlabel='False-positive rate',ylabel='True-positive rate',xlim=(0,1),ylim=(0,1.03));roc.set_title('Receiver operating characteristic',loc='left',fontsize=13);roc.legend(fontsize=8,loc='lower right',frameon=False)
fig.suptitle('NeuroVolume | What does MRI add?',x=.02,ha='left',fontsize=20,fontweight='bold')
fig.text(.02,.01,'OASIS-2 · 30 held-out baseline participants · 95% stratified bootstrap intervals (5,000 resamples).\nResearch classification of CDR > 0; not future decline or clinical diagnosis.',fontsize=9,color='#586b83')
fig.tight_layout(rect=[0,.09,1,.9])
fig.savefig(root/'reports/model-comparison.png',dpi=180,bbox_inches='tight');fig.savefig(root/'reports/model-comparison.svg',bbox_inches='tight')
print('Figures saved.')
