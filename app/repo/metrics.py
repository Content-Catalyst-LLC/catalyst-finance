from typing import Optional, List
from sqlalchemy import text
from app import db

def get_metric_value(ticker: str, metric_type: str, asof: Optional[str]) -> Optional[float]:
    if asof:
        sql = text("""
            SELECT value FROM metrics
             WHERE ticker = :ticker AND metric_type = :metric AND asof <= :asof
             ORDER BY asof DESC LIMIT 1
        """)
        row = db.session.execute(sql, {"ticker": ticker, "metric": metric_type, "asof": asof}).fetchone()
    else:
        sql = text("""
            SELECT value FROM metrics
             WHERE ticker = :ticker AND metric_type = :metric
             ORDER BY asof DESC LIMIT 1
        """)
        row = db.session.execute(sql, {"ticker": ticker, "metric": metric_type}).fetchone()
    return float(row[0]) if row and row[0] is not None else None

def get_sector_pe_series(ticker: str, asof: Optional[str]) -> List[float]:
    try:
        if asof:
            sql = text("""
                SELECT value FROM peer_metrics
                 WHERE base_ticker = :ticker AND metric_type = 'pe_trailing' AND asof <= :asof
            """)
            rows = db.session.execute(sql, {"ticker": ticker, "asof": asof}).fetchall()
        else:
            sql = text("""
                SELECT value FROM peer_metrics
                 WHERE base_ticker = :ticker AND metric_type = 'pe_trailing'
            """)
            rows = db.session.execute(sql, {"ticker": ticker}).fetchall()
        return [float(r[0]) for r in rows if r and r[0] is not None]
    except Exception:
        return []
