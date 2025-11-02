from typing import List, Optional, Dict

def compute_pe_potential(current_price: Optional[float],
                         trailing_eps: Optional[float],
                         sector_pe_series: Optional[List[float]]) -> Optional[Dict]:
    if not current_price or not trailing_eps or trailing_eps == 0:
        return None
    current_pe = current_price / trailing_eps

    if not sector_pe_series:
        return {
            "current_pe": round(current_pe, 2),
            "bear": {"pe": round(max(0.1, current_pe * 0.8), 2)},
            "base": {"pe": round(current_pe, 2)},
            "bull": {"pe": round(current_pe * 1.2, 2)},
            "method": "fallback-band"
        }

    series = sorted([x for x in sector_pe_series if x and x > 0])
    if not series:
        return {
            "current_pe": round(current_pe, 2),
            "bear": {"pe": round(max(0.1, current_pe * 0.8), 2)},
            "base": {"pe": round(current_pe, 2)},
            "bull": {"pe": round(current_pe * 1.2, 2)},
            "method": "fallback-band"
        }

    def pct(p: float) -> float:
        idx = max(0, min(len(series)-1, int(p * (len(series)-1))))
        return series[idx]

    return {
        "current_pe": round(current_pe, 2),
        "bear": {"pe": round(pct(0.30), 2)},
        "base": {"pe": round(pct(0.50), 2)},
        "bull": {"pe": round(pct(0.80), 2)},
        "method": "sector-percentile"
    }
