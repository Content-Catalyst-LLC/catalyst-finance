import json
from sqlalchemy import text
from app import db

def save_pe_scenarios(ticker: str, asof: str, payload: dict, method: str, version: str="v1") -> int:
    sql = text("""
        INSERT INTO scenarios (ticker, scenario_type, asof, payload, method, version, source)
        VALUES (:ticker, 'pe_potential', :asof, :payload, :method, :version, 'catalyst-finance')
    """)
    res = db.session.execute(sql, {
        "ticker": ticker,
        "asof": asof,
        "payload": json.dumps(payload),
        "method": method,
        "version": version
    })
    db.session.commit()
    return getattr(res, "lastrowid", 0)
