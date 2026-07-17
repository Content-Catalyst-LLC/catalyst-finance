"""Catalyst Finance demand and elasticity utility.

Retained as a named compatibility service for the future Pricing Studio.
"""

# Modes:
#   observed --input CSV [--group COL] [--output OUT.csv] [--plots --plot-dir DIR]
#   linear   --a A --b B --p-start S --p-end E --p-step D [--output OUT.csv] [--plots --plot-dir DIR]
from __future__ import annotations

import argparse
import csv
from typing import Any


def classify(abs_e: float) -> str:
    if abs(abs_e - 1.0) < 1e-9:
        return "unit elastic"
    return "elastic" if abs_e > 1 else "inelastic"


def midpoint_elasticity(p1, p2, q1, q2):
    qbar = (q1 + q2) / 2
    pbar = (p1 + p2) / 2
    if qbar == 0 or pbar == 0:
        raise ValueError("Midpoint denominator is zero")
    dq = (q2 - q1) / qbar
    dp = (p2 - p1) / pbar
    if dp == 0:
        raise ValueError("No price change; elasticity undefined")
    return dq / dp


def point_elasticity_linear(a, b, p):
    q = a - b * p
    if q <= 0:
        raise ValueError("Quantity <= 0 at this price; outside curve")
    return (-b) * (p / q)


def discrete_mr(prices: list[float], rev: list[float]):
    mr_vals, mr_at_price = [], []
    for i in range(1, len(prices)):
        dp = prices[i] - prices[i - 1]
        if dp == 0:
            continue
        dtr = rev[i] - rev[i - 1]
        mr_vals.append(dtr / dp)
        mr_at_price.append(prices[i])
    return mr_at_price, mr_vals


def load_csv_observed(path: str, group_col: str | None) -> list[dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            norm = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
            if "price" not in norm or "quantity" not in norm:
                raise ValueError("CSV must include 'Price' and 'Quantity'.")
            g = None
            if group_col:
                gkey = group_col.strip().lower()
                if gkey not in norm:
                    raise ValueError(f"Group column '{group_col}' not found.")
                g = norm[gkey] or None
            rows.append(
                {
                    "group": g,
                    "price": float(norm["price"]),
                    "quantity": float(norm["quantity"]),
                }
            )
        return rows


def observed_mode(input_path, output_path, group_col, do_plots, plot_dir):
    rows = load_csv_observed(input_path, group_col)
    groups = {}
    for r in rows:
        groups.setdefault(r["group"], []).append(r)
    plt = None
    if do_plots:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Matplotlib not available; skipping plots.")
            do_plots = False

    all_out = []
    print(
        "Group\tPrice\tQuantity\tRevenue\tE_mid_to_prev\t|E|\tType\tMR\tRevMax\tUnitElastic"
    )
    for g, lst in groups.items():
        lst.sort(key=lambda x: x["price"])
        prices = [x["price"] for x in lst]
        qty = [x["quantity"] for x in lst]
        rev = [p * q for p, q in zip(prices, qty, strict=False)]
        max_rev = max(rev) if rev else None

        e_mid = [None]
        abs_e = [None]
        e_type = [None]
        for i in range(1, len(lst)):
            try:
                e = midpoint_elasticity(prices[i - 1], prices[i], qty[i - 1], qty[i])
                e_mid.append(e)
                abs_e.append(abs(e))
                e_type.append(classify(abs(e)))
            except Exception:
                e_mid.append(None)
                abs_e.append(None)
                e_type.append(None)

        mr_p, mr_vals = discrete_mr(prices, rev)
        mr_map = {p: v for p, v in zip(mr_p, mr_vals, strict=False)}
        mr_col = [None] + [mr_map.get(prices[i]) for i in range(1, len(prices))]
        unit_flags = [False if x is None else abs(abs(x) - 1.0) < 1e-9 for x in e_mid]

        for i in range(len(lst)):
            row_print = [
                (g or ""),
                f"{prices[i]:.4g}",
                f"{qty[i]:.4g}",
                f"{rev[i]:.4g}",
                "" if e_mid[i] is None else f"{e_mid[i]:.4f}",
                "" if abs_e[i] is None else f"{abs_e[i]:.4f}",
                "" if e_type[i] is None else e_type[i],
                "" if mr_col[i] is None else f"{mr_col[i]:.4f}",
                1 if (max_rev is not None and abs(rev[i] - max_rev) < 1e-12) else 0,
                1 if unit_flags[i] else 0,
            ]
            print("\t".join(str(x) for x in row_print))
            all_out.append(
                [
                    (g or ""),
                    f"{prices[i]:.10g}",
                    f"{qty[i]:.10g}",
                    f"{rev[i]:.10g}",
                    "" if e_mid[i] is None else f"{e_mid[i]:.6f}",
                    "" if abs_e[i] is None else f"{abs_e[i]:.6f}",
                    "" if e_type[i] is None else e_type[i],
                    "" if mr_col[i] is None else f"{mr_col[i]:.6f}",
                    1 if (max_rev is not None and abs(rev[i] - max_rev) < 1e-12) else 0,
                    1 if unit_flags[i] else 0,
                ]
            )

        if do_plots and len(prices) >= 2:
            import os

            os.makedirs(plot_dir or "plots", exist_ok=True)
            # TR
            fig1 = plt.figure()
            plt.plot(prices, rev, marker="o")
            for i, r in enumerate(rev):
                if abs(r - max_rev) < 1e-12:
                    plt.scatter([prices[i]], [rev[i]], s=64)
            plt.xlabel("Price")
            plt.ylabel("Total Revenue (P×Q)")
            plt.title(f"TR vs Price ({g})" if g else "TR vs Price")
            tr_path = os.path.join(
                plot_dir or "plots", f"TR_{(g or 'ALL').replace(' ', '_')}.png"
            )
            fig1.savefig(tr_path, dpi=144, bbox_inches="tight")
            plt.close(fig1)
            # MR
            if len(mr_vals) >= 1:
                fig2 = plt.figure()
                plt.plot(mr_p, mr_vals, marker="o")
                plt.xlabel("Price")
                plt.ylabel("Marginal Revenue (ΔTR/ΔP)")
                plt.title(f"MR vs Price ({g})" if g else "MR vs Price")
                mr_path = os.path.join(
                    plot_dir or "plots", f"MR_{(g or 'ALL').replace(' ', '_')}.png"
                )
                fig2.savefig(mr_path, dpi=144, bbox_inches="tight")
                plt.close(fig2)

    if output_path:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "Group",
                    "Price",
                    "Quantity",
                    "Revenue",
                    "E_mid_to_prev",
                    "AbsE",
                    "Type",
                    "MR",
                    "RevMax",
                    "UnitElastic",
                ]
            )
            for r in all_out:
                w.writerow(r)
        print(f"\nWrote results to {output_path}")


def linear_mode(a, b, ps, pe, step, output_path, do_plots, plot_dir):
    if b <= 0:
        raise ValueError("Use b>0 for Q=a-bP.")
    if step == 0 or (pe - ps) / step < 0:
        raise ValueError("Step must move from start toward end.")
    plt = None
    if do_plots:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Matplotlib not available; skipping plots.")
            do_plots = False

    prices = []
    qty = []
    rev = []
    ept = []
    abse = []
    et = []
    p = ps
    forward = step > 0
    while (p <= pe + 1e-12) if forward else (p >= pe - 1e-12):
        q = a - b * p
        if q > 0:
            prices.append(p)
            qty.append(q)
            rev.append(p * q)
            e = point_elasticity_linear(a, b, p)
            ept.append(e)
            abse.append(abs(e))
            et.append(classify(abs(e)))
        p += step

    mr_p, mr_vals = discrete_mr(prices, rev)
    mr_map = {P: V for P, V in zip(mr_p, mr_vals, strict=False)}
    mr_col = [None] + [mr_map.get(prices[i]) for i in range(1, len(prices))]
    max_rev = max(rev) if rev else None
    unit_flags = [abs(x) - 1.0 < 1e-9 for x in ept]

    print("Price\tQty\tRevenue\tPointE\t|E|\tType\tMR\tRevMax\tUnitElastic")
    out = []
    for i in range(len(prices)):
        print(
            "\t".join(
                str(x)
                for x in [
                    f"{prices[i]:.4g}",
                    f"{qty[i]:.4g}",
                    f"{rev[i]:.4g}",
                    f"{ept[i]:.4f}",
                    f"{abse[i]:.4f}",
                    et[i],
                    "" if mr_col[i] is None else f"{mr_col[i]:.4f}",
                    1 if (max_rev is not None and abs(rev[i] - max_rev) < 1e-12) else 0,
                    1 if unit_flags[i] else 0,
                ]
            )
        )
        out.append(
            [
                f"{prices[i]:.10g}",
                f"{qty[i]:.10g}",
                f"{rev[i]:.10g}",
                f"{ept[i]:.6f}",
                f"{abse[i]:.6f}",
                et[i],
                "" if mr_col[i] is None else f"{mr_col[i]:.6f}",
                1 if (max_rev is not None and abs(rev[i] - max_rev) < 1e-12) else 0,
                1 if unit_flags[i] else 0,
            ]
        )

    if output_path:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "Price",
                    "Quantity",
                    "Revenue",
                    "PointElasticity",
                    "AbsE",
                    "Type",
                    "MR",
                    "RevMax",
                    "UnitElastic",
                ]
            )
            for r in out:
                w.writerow(r)
        print(f"\nWrote results to {output_path}")

    if do_plots and len(prices) >= 2:
        import os

        os.makedirs(plot_dir or "plots", exist_ok=True)
        # TR
        fig1 = plt.figure()
        plt.plot(prices, rev, marker="o")
        for i, R in enumerate(rev):
            if abs(R - max_rev) < 1e-12:
                plt.scatter([prices[i]], [rev[i]], s=64)
        plt.xlabel("Price")
        plt.ylabel("Total Revenue (P×Q)")
        plt.title("TR vs Price (Linear)")
        fig1.savefig(
            (plot_dir or "plots") + "/TR_linear.png", dpi=144, bbox_inches="tight"
        )
        plt.close(fig1)
        # MR
        if len(mr_vals) >= 1:
            fig2 = plt.figure()
            plt.plot(mr_p, mr_vals, marker="o")
            plt.xlabel("Price")
            plt.ylabel("Marginal Revenue (ΔTR/ΔP)")
            plt.title("MR vs Price (Linear)")
            fig2.savefig(
                (plot_dir or "plots") + "/MR_linear.png", dpi=144, bbox_inches="tight"
            )
            plt.close(fig2)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Catalyst Finance — Demand & Elasticity Helper"
    )
    sub = p.add_subparsers(dest="mode", required=True)
    obs = sub.add_parser("observed")
    obs.add_argument("--input", required=True)
    obs.add_argument("--group")
    obs.add_argument("--output")
    obs.add_argument("--plots", action="store_true")
    obs.add_argument("--plot-dir")
    lin = sub.add_parser("linear")
    lin.add_argument("--a", type=float, required=True)
    lin.add_argument("--b", type=float, required=True)
    lin.add_argument("--p-start", type=float, required=True)
    lin.add_argument("--p-end", type=float, required=True)
    lin.add_argument("--p-step", type=float, required=True)
    lin.add_argument("--output")
    lin.add_argument("--plots", action="store_true")
    lin.add_argument("--plot-dir")
    args = p.parse_args()
    if args.mode == "observed":
        observed_mode(args.input, args.output, args.group, args.plots, args.plot_dir)
    else:
        linear_mode(
            args.a,
            args.b,
            args.p_start,
            args.p_end,
            args.p_step,
            args.output,
            args.plots,
            args.plot_dir,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
