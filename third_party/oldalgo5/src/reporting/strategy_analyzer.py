
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Optional
from scipy import stats

@dataclass
class StrategyGrade:
    overall_score: float
    performance_grade: str
    risk_grade: str
    consistency_grade: str
    robustness_grade: str
    metrics: Dict[str, float]
    notes: str = ""

class StrategyAnalyzer:
    def __init__(self, risk_free_rate: float = 0.0, ann: int = 252):
        self.rf = float(risk_free_rate)
        self.ann = int(ann)

    def _sharpe(self, r: pd.Series) -> float:
        ex = r - (self.rf / self.ann)
        if len(ex)<2 or ex.std()==0: return 0.0
        return float((ex.mean()/ex.std())*np.sqrt(self.ann))

    def _sortino(self, r: pd.Series) -> float:
        ex = r - (self.rf / self.ann)
        dn = ex[ex<0]
        if len(dn)==0 or dn.std()==0: return 0.0
        return float((ex.mean()/dn.std())*np.sqrt(self.ann))

    def _maxdd(self, eq: pd.Series) -> float:
        roll = eq.cummax()
        dd = (eq - roll) / roll
        return float(dd.min())

    def _calmar(self, annret: float, eq: pd.Series) -> float:
        mdd = abs(self._maxdd(eq)) or 1e-9
        return float(abs(annret)/mdd)

    def _annualized_return(self, r: pd.Series) -> float:
        if len(r)==0: return 0.0
        tot = (1+r).prod()-1
        return float((1+tot)**(self.ann/len(r))-1)

    def _vol(self, r: pd.Series) -> float:
        return float(r.std()*np.sqrt(self.ann))

    def _win_rate(self, r: pd.Series) -> float:
        return float((r>0).mean()) if len(r)>0 else 0.0

    def _profit_factor(self, r: pd.Series) -> float:
        gp = float(r[r>0].sum())
        gl = float(abs(r[r<0].sum()))
        return 10.0 if gl==0 else float(gp/gl)

    def _monthly_consistency(self, r: pd.Series) -> float:
        m = r.resample('M').apply(lambda x: (1+x).prod()-1)
        return float((m>0).mean()) if len(m)>0 else 0.0

    def _quarterly_consistency(self, r: pd.Series) -> float:
        q = r.resample('Q').apply(lambda x: (1+x).prod()-1)
        return float((q>0).mean()) if len(q)>0 else 0.0

    def evaluate(self, results: Dict) -> StrategyGrade:
        r = results.get('returns')
        if r is None:
            raise ValueError('results must include returns series')
        eq = results.get('equity') or results.get('equity_curve') or (1+r).cumprod()

        r = r.dropna().astype(float)
        eq = eq.dropna().astype(float)

        metrics = {
            'sharpe_ratio': self._sharpe(r),
            'sortino_ratio': self._sortino(r),
            'max_drawdown': self._maxdd(eq),
            'annualized_return': self._annualized_return(r),
            'volatility': self._vol(r),
            'calmar_ratio': self._calmar(self._annualized_return(r), eq),
            'win_rate': self._win_rate(r),
            'profit_factor': self._profit_factor(r),
            'skewness': float(stats.skew(r)),
            'kurtosis': float(stats.kurtosis(r)),
            'monthly_consistency': self._monthly_consistency(r),
            'quarterly_consistency': self._quarterly_consistency(r),
            'tail_ratio': float(r.quantile(0.95) / abs(r.quantile(0.05)) if r.quantile(0.05)!=0 else 10.0)
        }

        grades = self._assign_grades(metrics)
        overall = self._overall_score(metrics)

        notes = []
        if grades['performance'] in ['A','A+']: notes.append('Yüksek risk-ayarlı getiri')
        if grades['risk'] in ['A','A+']: notes.append('Düşük çekilme ve volatilite')
        if grades['consistency'] in ['A','A+']: notes.append('İstikrarlı pozitif dönemler')
        if not notes: notes.append('Ortalama performans')

        return StrategyGrade(
            overall_score=overall,
            performance_grade=grades['performance'],
            risk_grade=grades['risk'],
            consistency_grade=grades['consistency'],
            robustness_grade=grades['robustness'],
            metrics=metrics,
            notes=' | '.join(notes)
        )

    def _assign_grades(self, m: Dict[str,float]):
        def grade(x, cuts):
            return 'A+' if x>=cuts[4] else 'A' if x>=cuts[3] else 'B' if x>=cuts[2] else 'C' if x>=cuts[1] else 'D' if x>=cuts[0] else 'F'
        perf = 0.6*m.get('sharpe_ratio',0)+0.4*m.get('annualized_return',0)
        risk = 0.6*min(1.0/(abs(m.get('max_drawdown',0.5))+0.01),10)+0.4*max(1.0-m.get('volatility',1.0),0)
        cons = 0.5*m.get('monthly_consistency',0)+0.5*m.get('quarterly_consistency',0)
        rob  = 0.3*m.get('profit_factor',0)+0.3*min(m.get('tail_ratio',0),3)/3+0.2*m.get('win_rate',0)+0.2*max(0,1-abs(m.get('skewness',0)))
        return {
            'performance': grade(perf, [0,0.5,1.0,1.5,2.0]),
            'risk': grade(risk, [0,0.3,0.6,0.8,0.9]),
            'consistency': grade(cons, [0,0.4,0.6,0.75,0.85]),
            'robustness': grade(rob, [0,0.5,1.0,1.5,2.0])
        }

    def _overall_score(self, m: Dict[str,float]) -> float:
        weights = {
            'sharpe_ratio':0.2,'sortino_ratio':0.15,'max_drawdown':0.15,'calmar_ratio':0.1,
            'win_rate':0.1,'profit_factor':0.1,'monthly_consistency':0.1,'quarterly_consistency':0.1
        }
        def norm(key,val):
            rules = {
                'sharpe_ratio': lambda x: min(max(x,0),3)/3,
                'sortino_ratio': lambda x: min(max(x,0),4)/4,
                'max_drawdown': lambda x: 1 - min(max(abs(x),0),1),
                'calmar_ratio': lambda x: min(max(x,0),3)/3,
                'win_rate': lambda x: min(max(x,0),0.8)/0.8,
                'profit_factor': lambda x: min(max(x,0),5)/5,
                'monthly_consistency': lambda x: min(max(x,0),1.0),
                'quarterly_consistency': lambda x: min(max(x,0),1.0),
            }
            return rules.get(key, lambda v:0.0)(val)
        score = 0.0; tot=0.0
        for k,w in weights.items():
            score += norm(k, m.get(k,0))*w
            tot += w
        return score/tot if tot>0 else 0.0
