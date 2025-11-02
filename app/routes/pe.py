import math, json
from datetime import date
from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app import db

bp = Blueprint("pe", __name__, url_prefix="/v1/scenarios")

def _percentile(sorted_vals, p):
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
    asof = request.args.get("asof", type=str) or str(date.today())
    if not ticker:
        return jsonify({"error": "ticker required"}), 400

    # Latest price & eps on/before asof
    price = db.session.execute(text("""
        SELECT value FROM metrics
        WHERE ticker=:t AND metric_type='price_close' AND asof <= :asof
        ORDER BY asof DESC LIMIT 1
    """), {"t": ticker, "asof": asof}).scalar()
    eps = db.session.execute(text("""
        SELECT value FROM metrics
        WHERE ticker=:t AND metric_type='eps_trailing' AND asof <= :asof
        ORDER BY asof DESC LIMIT 1
    """), {"t": ticker, "asof": asof}).scalar()
    if price is None or eps is None:
        return jsonify({"error": "insufficient inputs"}), 400
    if float(eps) <= 0:
        return jsonify({"error": "non-positive EPS"}), 400

    current_pe = round(float(price) / float(eps), 2)

    # Peer P/Es (same date)
    peer_vals = [
        float(v) for (v,) in db.session.execute(text("""
            SELECT value FROM peer_metrics
            WHERE base_ticker=:t AND metric_type='pe_trailing' AND asof = :asof
        """), {"t": ticker, "asof": asof}).all()
        if v is not None
    ]
    if not peer_vals:
        return jsonify({"error": "no peer P/Es"}), 400

    peer_vals.sort()
    bear_pe = round(_percentile(peer_vals, 25), 2)
    base_pe = round(_percentile(peer_vals, 50), 2)
    bull_pe = round(_percentile(peer_vals, 75), 2)
    payload = {"bear": {"pe": bear_pe}, "base": {"pe": base_pe}, "bull": {"pe": bull_pe}}

    # Save scenario (SQLite)
    db.session.execute(text("""
        INSERT INTO scenarios (ticker, scenario_type, asof, payload, method, version, source)
        VALUES (:t, 'pe_potential', :asof, :payload, :method, :version, 'catalyst-finance')
    """), {
        "t": ticker, "asof": asof,
        "payload": json.dumps(payload),
        "method": "sector-percentile",
        "version": "v1"
    })
    db.session.commit()
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
