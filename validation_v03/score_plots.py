"""Standalone diagnostic ROC/DET figures; never select thresholds or show raw IDs."""
from pathlib import Path


def plot_curves(report, output):
    output=Path(output)
    extension=output.suffix.lower().lstrip('.')
    if extension not in ('png','svg','pdf'):
        raise ValueError('Plot output must be PNG, SVG or PDF')
    for result in report['metrics'].values():
        if 'diagnostic_curves' not in result:
            raise ValueError('Diagnostic curves required before rendering')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(12.6,7.2),layout='constrained')
    try:
        for column,split in enumerate(('development','validation','test')):
            for metric,label,color in [('legacy_score','Legacy','#2563eb'),
                                       ('candidate_score','Candidate','#c2410c')]:
                result=report['metrics'][metric]
                curve=result['diagnostic_curves'][split]
                points=curve['points']
                x=[p['attack_accept_rate'] for p in points]
                for row,key in enumerate(('human_accept_rate','human_reject_rate')):
                    axes[row,column].plot(x,[p[key] for p in points],color=color,
                        linewidth=1.8,label=f"{label} (AUC {curve['auc']:.3f})" if row==0 else label)
                    if split in ('validation','test') and result['status']=='evaluated':
                        endpoint=result[split]
                        human=endpoint['human']['score_accept_rate_among_scored']
                        attack=endpoint['attack']['score_accept_rate_among_scored']
                        axes[row,column].scatter([attack],[human if row==0 else 1-human],
                                                 marker='x',s=65,color=color,zorder=5)
            for row in (0,1):
                axis=axes[row,column]
                axis.plot([0,1],[0,1] if row==0 else [1,0],color='#a3a3a3',linestyle='--',linewidth=.8)
                axis.set(xlim=(-.02,1.02),ylim=(-.02,1.02),xlabel='Attack accept rate',
                         ylabel='Human accept rate' if row==0 else 'Human reject rate',
                         title=f"{'ROC' if row==0 else 'DET'} - {split}")
                axis.grid(alpha=.2);axis.legend(loc='best',fontsize=8)
        scope = 'SYNTHETIC EXAMPLE - no measured performance' if report.get('data_scope')=='synthetic' else 'Supplied scores - provenance not independently verified'
        fig.suptitle(scope+'\nDiagnostic score-only curves | x: threshold selected on validation',fontsize=12)
        fig.supxlabel('Scored trials only. Raw probability axes; failures and all-attempt counts are reported separately.',fontsize=9)
        with output.open('xb') as stream:
            fig.savefig(stream,format=extension,dpi=160)
    finally:
        plt.close(fig)
