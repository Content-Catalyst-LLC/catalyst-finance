from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app import db
import math
from datetime import date

bp = Blueprint("pe", __name__, url_prefix="/v1/scenarios")

def _percentile(sorted_vals, p):
    """
    p in [0, 100]. Linear interpolation between closest ranks.
    For 5 values, p25=2nd, p50=3rd, p75=4th as expected.
    """
    if not sorted_vals:
        return None
    if p <= 0: return sorted_vals[0]
    if p >= 100: return sorted_vals[-1]
    k = (len(sorted_vals)-1) * (p/100.0)
    f = math.floor(k); c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)

@bp.get("/pe")
def get_pe_scenarios():
    ticker = request.args.get("ticker", type=str)
    asof = request.args.get("asof", type=str)

    if not ticker:
        return jsonify({"error": "ticker required"}), 400
    if not asof:
        asof = str(date.today())

    # 1) Fetch latest price_close and eps_trailing on/before asof
    price_sql = text("""
        SELECT value FROM metrics
        WHERE ticker=:t AND metric_type='price_close' AND asof <= :asof
        ORDER BY asof DESC LIMIT 1
    """)
    eps_sql = text("""
        SELECT value FROM metrics
        WHERE ticker=:t AND metric_type='eps_trailing' AND asof <= :asof
        ORDER BY asof DESC LIMIT 1
    """)
    row_p = db.session.execute(price_sql, {"t": ticker, "asof": asof}).fetchone()
    row_e = db.session.execute(eps_sql,   {"t": ticker, "asof": asof}).fetchone()
    if not row_p or not row_e:
        return jsonify({"error": "insufficient inputs"}), 400

    price = float(row_p[0])
    eps   = float(row_e[0])
    if eps <= 0:
        return jsonify({"error": "non-positive EPS"}), 400

    current_pe = round(price/eps, 2)

    # 2) Gather peer P/Es for the same asof
    peers_sql = text("""
        SELECT value FROM peer_metrics
        WHERE base_ticker=:t AND metric_type='pe_trailing' AND asof = :asof
    """)
    peer_vals = [float(r[0]) for r in db.session.execute(peers_sql, {"t": ticker, "asof": asof}).fetchall() if r[0] is not None]
    if len(peer_vals) == 0:
        return jsonify({"error": "no peer P/Es"}), 400

    peer_vals.sort()
    # 25th / 50th / 75th percentiles to match earlier band values
    bear_pe = round(_percentile(peer_vals, 25), 2)
    base_pe = round(_percentile(peer_vals, 50), 2)
    bull_pe = round(_percentile(peer_vals, 75), 2)

    # 3) Save a scenarios row and return payload + provenance id
    payload = {"bear": {"pe": bear_pe}, "base": {"pe": base_pe}, "bull": {"pe": bull_pe}}
    ins = text("""
        INSERT INTO scenarios (ticker, scenario_type, asof, payload, method, version, source)
        VALUES (:t, 'pe_potential', :asof, :payload, :method, :version, 'catalyst-finance')
    """)
    db.session.execute(ins, {
        "t": ticker,
        "asof": asof,
        "payload": jsonify(payload).data.decode("utf-8"),
        "method": "sector-percentile",
        "version": "v1"
    })
    db.session.commit()

    # fetch last rowid (SQLite specific)
    rid = db.session.execute(text("SELECT last_insert_rowid()")).scalar_one()
    return jsonify({
        "ticker": ticker,
        "asof": asof,
        "scenario_type": "pe_potential",
        "provenance_id": f"scn_{rid}",
        "current_pe": current_pe,
        **payload,
        "method": "sector-percentile",
        "version": "v1"
    }), 200
