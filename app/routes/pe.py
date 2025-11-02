from flask import Blueprint, request, jsonify
from datetime import date
from app.repo.metrics import get_metric_value, get_sector_pe_series
from app.repo.scenarios import save_pe_scenarios
from app.services.pe_potential import compute_pe_potential

bp = Blueprint("pe", __name__, url_prefix="/v1")

@bp.get("/metrics/pe")
def get_pe():
    ticker = request.args.get("ticker")
    asof = request.args.get("asof")
    if not ticker:
        return jsonify({"error":"missing ticker"}), 400
    price = get_metric_value(ticker, "price_close", asof)
    eps = get_metric_value(ticker, "eps_trailing", asof)
    val = (price / eps) if price and eps else None
    return jsonify({"ticker": ticker, "metric": "pe_trailing", "value": round(val,2) if val else None, "asof": asof}), 200

@bp.get("/scenarios/pe")
def get_pe_scenarios():
    ticker = request.args.get("ticker")
    asof = request.args.get("asof") or date.today().isoformat()
    if not ticker:
        return jsonify({"error":"missing ticker"}), 400

    price = get_metric_value(ticker, "price_close", asof)
    eps = get_metric_value(ticker, "eps_trailing", asof)
    sector_series = get_sector_pe_series(ticker, asof)
    comp = compute_pe_potential(price, eps, sector_series)
    if comp is None:
        return jsonify({"error":"insufficient inputs"}), 422

    prov = save_pe_scenarios(ticker, asof,
                             {"bear": comp["bear"], "base": comp["base"], "bull": comp["bull"]},
                             comp["method"])

    return jsonify({
        "ticker": ticker,
        "asof": asof,
        "scenario_type": "pe_potential",
        "provenance_id": f"scn_{prov}" if prov else None,
        "current_pe": comp["current_pe"],
        "bear": comp["bear"],
        "base": comp["base"],
        "bull": comp["bull"],
        "method": comp["method"],
        "version": "v1"
    }), 200
